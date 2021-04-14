import sys
from ctypes import (
    CDLL,
    POINTER,
    byref,
    Structure,
    Union,
    c_char,
    c_char_p,
    c_short,
    c_int,
    c_long,
    c_ubyte,
    c_ulong,
    c_void_p,
    c_uint,
    cast,
    create_string_buffer,
    create_unicode_buffer,
    memmove,
    sizeof,
)


# TODO: parse command-line arguments
VERBOSE = False
SHOW_PID = True
SHOW_GEOM = True
SHOW_CLASS = True


def p_verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, file=sys.stderr, **kwargs)


# Types
Display = c_void_p
DisplayP = POINTER(Display)
Atom = XID = Time = c_ulong
AtomP = POINTER(Atom)
Drawable = Window = XID
WindowP = POINTER(Window)
Status = Bool = c_int


# Consts
XA_CARDINAL = Atom(6)
XA_STRING = Atom(31)
XA_WINDOW = Atom(33)
XA_STRING = Atom(31)
Success = 0
BadWindow = 3
BadAtom = 5
BadValue = 2

MAXLEN = 4096


# Structs & Unions
class XButtonEvent(Structure):
    _fields_ = [
        ("type", c_int),
        ("serial", c_ulong),
        ("send_event", Bool),
        ("display", DisplayP),
        ("window", Window),
        ("root", Window),
        ("subwindow", Window),
        ("time", Time),
        ("x", c_int),
        ("y", c_int),
        ("x_root", c_int),
        ("y_root", c_int),
        ("state", c_uint),
        ("button", c_uint),
        ("same_screen", Bool),
    ]


class _data(Union):
    _fields_ = [("b", c_char * 20), ("s", c_short * 10), ("l", c_long * 5)]


class XClientMessageEvent(Structure):
    _fields_ = [
        ("type", c_int),
        ("serial", c_ulong),
        ("send_event", Bool),
        ("display", DisplayP),
        ("window", Window),
        ("message_type", Atom),
        ("format", c_int),
        ("data", _data),
    ]


class XEvent(Union):
    _fields_ = [
        ("type", c_int),
        ("xbutton", XButtonEvent),
        ("xclient", XClientMessageEvent),
        ("pad", c_long * 24),
    ]


# Libs
xlib = CDLL("libX11.so")


# Funcs
Free = xlib.XFree
Free.argtypes = [c_void_p]
Free.restype = None

OpenDisplay = xlib.XOpenDisplay
OpenDisplay.argtypes = [c_char_p]
OpenDisplay.restype = DisplayP

CloseDisplay = xlib.XCloseDisplay
CloseDisplay.argtypes = [DisplayP]
CloseDisplay.restype = None

DefaultRootWindow = xlib.XDefaultRootWindow
DefaultRootWindow.argtypes = [DisplayP]
DefaultRootWindow.restype = Window

InternAtom = xlib.XInternAtom
InternAtom.argtypes = [DisplayP, c_char_p, Bool]
InternAtom.restype = Atom

GetWindowProperty = xlib.XGetWindowProperty
GetWindowProperty.argtypes = [
    DisplayP,
    Window,
    Atom,
    c_long,
    c_long,
    Bool,
    Atom,
    AtomP,
    POINTER(c_int),
    POINTER(c_ulong),
    POINTER(c_ulong),
    POINTER(POINTER(c_ubyte)),
]
GetWindowProperty.restype = Status

GetGeometry = xlib.XGetGeometry
GetGeometry.argtypes = [
    DisplayP,
    Drawable,
    WindowP,
    POINTER(c_int),
    POINTER(c_int),
    POINTER(c_uint),
    POINTER(c_uint),
    POINTER(c_uint),
    POINTER(c_uint),
]
GetGeometry.restype = Status

TranslateCoordinates = xlib.XTranslateCoordinates
TranslateCoordinates.argtypes = [
    DisplayP,
    Window,
    Window,
    c_int,
    c_int,
    POINTER(c_int),
    POINTER(c_int),
    WindowP,
]
TranslateCoordinates.restype = Bool


def get_property(disp, win, xa_prop_type, prop_name):
    xa_ret_type = Atom()
    ret_format = c_int()
    ret_nitems = c_ulong()
    ret_bytes_after = c_ulong()
    ret_prop = POINTER(c_ubyte)()

    xa_prop_name = InternAtom(disp, prop_name.encode(), True)
    if not (xa_prop_name):
        p_verbose(
            "{0} is not in the Host Portable Character Encoding".format(prop_name)
        )
        return None

    # MAX_PROPERTY_VALUE_LEN / 4 explanation (XGetWindowProperty manpage):
    # long_length = Specifies the length in 32-bit multiples of the
    # data to be retrieved.
    status = GetWindowProperty(
        disp,
        win,
        xa_prop_name,
        0,
        MAXLEN // 4,
        False,
        xa_prop_type,
        byref(xa_ret_type),
        byref(ret_format),
        byref(ret_nitems),
        byref(ret_bytes_after),
        byref(ret_prop),
    )

    if status != Success:
        p_verbose("Cannot get {} property.".format(prop_name))
        return None

    if xa_ret_type.value != xa_prop_type.value:
        Free(ret_prop)
        p_verbose("Invalid type of {} property.".format(prop_name))
        return None

    tmp_size = (ret_format.value // (32 // sizeof(c_long))) * ret_nitems.value
    ret = create_string_buffer(tmp_size + 1)
    memmove(ret, ret_prop, tmp_size)
    ret[tmp_size] = b"\x00"

    Free(ret_prop)
    return ret, tmp_size


def get_client_list(disp):
    root = DefaultRootWindow(disp)
    result = get_property(disp, root, XA_WINDOW, "_NET_CLIENT_LIST")
    if result:
        client_list, size = result
        client_list = cast(client_list, WindowP)
        return client_list, size

    result = get_property(disp, root, XA_WINDOW, "_WIN_CLIENT_LIST")
    if result:
        client_list, size = result
        client_list = cast(client_list, WindowP)
        return client_list, size

    p_verbose(
        "Cannot get client list properties. \n" "(_NET_CLIENT_LIST or _WIN_CLIENT_LIST)"
    )
    return None


def get_window_pid(disp, win):
    result = get_property(disp, win, XA_CARDINAL, "_NET_WM_PID")
    if result:
        prop, size = result
        prop = cast(prop, POINTER(c_ulong))
        return prop.contents.value
    return None


def get_window_title(disp, win):
    # TODO: use XFetchName for WM_NAME, get _NET_WM_NAME first if set
    result = get_property(disp, win, XA_STRING, "WM_NAME")
    if result:
        wm_name, _ = result
        if wm_name.value:
            return wm_name.value.decode("utf8")

    xa_prop_type = Atom(InternAtom(disp, b"UTF8_STRING", False))
    result = get_property(disp, win, xa_prop_type, "_NET_WM_NAME")
    if result:
        net_wm_name, _ = result
        return net_wm_name.value.decode("utf8")

    return None


def get_window_class(disp, win):
    # TODO: use XGetClassHint
    result = get_property(disp, win, XA_STRING, "WM_CLASS")
    if result:
        wm_class, size = result
        wm_class = b".".join(wm_class.raw.split(b"\x00")[:2])
        return wm_class.decode("ascii")
    return None


def get_window_desktop_id(disp, win):
    result = get_property(disp, win, XA_CARDINAL, "_NET_WM_DESKTOP")
    if result:
        desktop, _ = result
        desktop = cast(desktop, POINTER(c_ulong)).contents.value
        return c_long(desktop).value if desktop else 0

    result = get_property(disp, win, XA_CARDINAL, "_WIN_WORKSPACE")
    if result:
        desktop, _ = result
        desktop = cast(desktop, POINTER(c_ulong)).contents.value
        return c_long(desktop).value if desktop else 0
    return None


def get_window_geometry(disp, win):
    junkroot = Window()
    x = c_int()
    y = c_int()
    junkx = c_int()
    junky = c_int()

    wwidth = c_uint()
    wheight = c_uint()
    bw = c_uint()
    depth = c_uint()

    GetGeometry(
        disp,
        win,
        byref(junkroot),
        byref(junkx),
        byref(junky),
        byref(wwidth),
        byref(wheight),
        byref(bw),
        byref(depth),
    )
    TranslateCoordinates(
        disp, win, junkroot, junkx, junky, byref(x), byref(y), byref(junkroot)
    )
    return x.value, y.value, wwidth.value, wheight.value, bw.value, depth.value


def get_window_client_name(disp, win):
    # TODO: use XGetWMClientMachine
    result = get_property(disp, win, XA_STRING, "WM_CLIENT_MACHINE")
    if result:
        client_machine, _ = result
        return client_machine.value.decode("utf8")
    return None


def list_window_props(disp):
    client_list, client_list_size = get_client_list(disp)
    props = (
        (
            client_list[i],
            get_window_desktop_id(disp, client_list[i]),
            get_window_class(disp, client_list[i]),
            get_window_pid(disp, client_list[i]),
            *get_window_geometry(disp, client_list[i])[:4],
            get_window_client_name(disp, client_list[i]),
            get_window_title(disp, client_list[i]),
        )
        for i in range(client_list_size // sizeof(Window))
    )
    return props


def list_windows(disp):
    max_client_machine_len = 0
    max_class_name_len = 0

    client_list, client_list_size = get_client_list(disp)
    for i in range(client_list_size // sizeof(Window)):
        result = get_property(disp, client_list[i], XA_STRING, "WM_CLIENT_MACHINE")
        if result:
            client_machine, _ = result
            client_machine_size = len(client_machine.value)
            max_client_machine_len = max(client_machine_size, max_client_machine_len)

        wm_class = get_window_class(disp, client_list[i])
        if wm_class:
            max_class_name_len = max(max_class_name_len, len(wm_class))

    for i in range(client_list_size // sizeof(Window)):
        client = client_list[i]
        title_out = get_window_title(disp, client)
        class_out = get_window_class(disp, client)
        desktop = get_window_desktop_id(disp, client)
        client_machine = get_window_client_name(disp, client)
        pid = get_window_pid(disp, client)
        x, y, wwidth, wheight, _, _ = get_window_geometry(disp, client)

        print("0x%.8lx %2ld" % (client, desktop), end="")

        if SHOW_PID:
            print(" %-6lu" % (pid or 0), end="")

        if SHOW_GEOM:
            print(
                " %-4d %-4d %-4d %-4d" % (x, y, wwidth, wheight),
                end="",
            )

        if SHOW_CLASS:
            print(" %-*s " % (max_class_name_len, class_out or "N/A"), end="")

        print(
            " %*s %s\n"
            % (
                max_client_machine_len,
                client_machine or "N/A",
                title_out or "N/A",
            ),
            end="",
        )


if __name__ == "__main__":
    display = OpenDisplay(None)
    root = DefaultRootWindow(display)

    list_windows(display)
    list_window_props(display)

    xlib.XCloseDisplay(display)
