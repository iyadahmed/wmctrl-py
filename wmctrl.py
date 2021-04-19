import sys
from typing import Tuple, Union, List
from ctypes import (
    CDLL,
    POINTER,
    byref,
    Structure as CStruct,
    Union as CUnion,
    c_char,
    c_char_p,
    c_short,
    c_int,
    c_long,
    c_ubyte,
    c_ulong,
    c_void_p,
    c_uint,
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

c_int_p = POINTER(c_int)
c_uint_p = POINTER(c_uint)
c_ulong_p = POINTER(c_ulong)
c_ubyte_p = POINTER(c_ubyte)


# Consts
XA_CARDINAL = Atom(6)
XA_STRING = Atom(31)
XA_WINDOW = Atom(33)
XA_STRING = Atom(31)
Success = 0
BadWindow = 3
BadAtom = 5
BadValue = 2
SubstructureRedirectMask = 1048576
SubstructureNotifyMask = 524288
ClientMessage = 33

MAXLEN = 4096


# Structs & Unions
class XButtonEvent(CStruct):
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


class _data(CUnion):
    _fields_ = [("b", c_char * 20), ("s", c_short * 10), ("l", c_long * 5)]


class XClientMessageEvent(CStruct):
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


class XEvent(CUnion):
    _fields_ = [
        ("type", c_int),
        ("xbutton", XButtonEvent),
        ("xclient", XClientMessageEvent),
        ("pad", c_long * 24),
    ]


class XTextProperty(CStruct):
    _fields_ = [
        ("value", c_ubyte_p),
        ("encoding", Atom),
        ("format", c_int),
        ("nitems", c_ulong),
    ]


class XClassHint(CStruct):
    _fields_ = [("res_name", c_char_p), ("res_class", c_char_p)]


# Libs
xlib = CDLL("libX11.so")


# Funcs
XFree = xlib.XFree
XFree.argtypes = [c_void_p]
XFree.restype = None

XOpenDisplay = xlib.XOpenDisplay
XOpenDisplay.argtypes = [c_char_p]
XOpenDisplay.restype = DisplayP

XCloseDisplay = xlib.XCloseDisplay
XCloseDisplay.argtypes = [DisplayP]
XCloseDisplay.restype = None

XDefaultRootWindow = xlib.XDefaultRootWindow
XDefaultRootWindow.argtypes = [DisplayP]
XDefaultRootWindow.restype = Window

XInternAtom = xlib.XInternAtom
XInternAtom.argtypes = [DisplayP, c_char_p, Bool]
XInternAtom.restype = Atom

XSendEvent = xlib.XSendEvent
XSendEvent.argtypes = [DisplayP, Window, Bool, c_long, POINTER(XEvent)]
XSendEvent.restype = Status

XGetWindowProperty = xlib.XGetWindowProperty
XGetWindowProperty.argtypes = [
    DisplayP,
    Window,
    Atom,
    c_long,
    c_long,
    Bool,
    Atom,
    AtomP,
    c_int_p,
    c_ulong_p,
    c_ulong_p,
    POINTER(c_ubyte_p),
]
XGetWindowProperty.restype = Status

XGetGeometry = xlib.XGetGeometry
XGetGeometry.argtypes = [
    DisplayP,
    Drawable,
    WindowP,
    c_int_p,
    c_int_p,
    c_uint_p,
    c_uint_p,
    c_uint_p,
    c_uint_p,
]
XGetGeometry.restype = Status

XTranslateCoordinates = xlib.XTranslateCoordinates
XTranslateCoordinates.argtypes = [
    DisplayP,
    Window,
    Window,
    c_int,
    c_int,
    c_int_p,
    c_int_p,
    WindowP,
]
XTranslateCoordinates.restype = Bool

XFetchName = xlib.XFetchName
XFetchName.argtypes = [DisplayP, Window, POINTER(c_char_p)]
XFetchName.restype = Status

XGetWMClientMachine = xlib.XGetWMClientMachine
XGetWMClientMachine.argtypes = [DisplayP, Window, POINTER(XTextProperty)]
XGetWMClientMachine.restype = Status

XGetClassHint = xlib.XGetClassHint
XGetClassHint.argtypes = [DisplayP, Window, POINTER(XClassHint)]
XGetClassHint.restype = Status


def client_msg(
    disp: "DisplayP", win: "Window", msg: str, *data: Tuple
) -> Union["XEvent", None]:

    assert len(data) == 5
    event = XEvent()
    mask = SubstructureRedirectMask | SubstructureNotifyMask
    event.xclient.type = ClientMessage
    event.xclient.serial = 0
    event.xclient.send_event = True
    event.xclient.message_type = XInternAtom(disp, msg.encode("ascii"), False)
    event.xclient.window = win
    event.xclient.format = 32
    event.xclient.data.l[0] = data[0]
    event.xclient.data.l[1] = data[1]
    event.xclient.data.l[2] = data[2]
    event.xclient.data.l[3] = data[3]
    event.xclient.data.l[4] = data[4]

    result = XSendEvent(disp, XDefaultRootWindow(disp), False, mask, byref(event))
    if result:
        return event

    print("Cannot send %s event." % msg, file=sys.stderr)
    return None


def get_property(
    disp: "DisplayP", win: "Window", xa_prop_type: "Atom", prop_name: str
) -> Union[Tuple["c_ubyte_p", int], None]:

    xa_ret_type = Atom()
    ret_format = c_int()
    ret_nitems = c_ulong()
    ret_bytes_after = c_ulong()
    ret_prop = c_ubyte_p()

    xa_prop_name = XInternAtom(disp, prop_name.encode(), True)
    if not (xa_prop_name):
        p_verbose(f"{prop_name} is not in the Host Portable Character Encoding")
        return None

    # MAX_PROPERTY_VALUE_LEN / 4 explanation (XGetWindowProperty manpage):
    # long_length = Specifies the length in 32-bit multiples of the
    # data to be retrieved.
    status = XGetWindowProperty(
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
        p_verbose(f"Cannot get {prop_name} property.")
        return None

    if xa_ret_type.value != xa_prop_type.value:
        XFree(ret_prop)
        p_verbose(f"Invalid type of {prop_name} property.")
        return None

    size = (ret_format.value // (32 // sizeof(c_long))) * ret_nitems.value
    if ret_prop:
        return ret_prop, size

    p_verbose(f"{prop_name} not found.")
    return None


def get_client_list(disp: "DisplayP") -> Union[List[int], None]:
    root = XDefaultRootWindow(disp)
    result = get_property(disp, root, XA_WINDOW, "_NET_CLIENT_LIST")
    if result:
        client_list, size = result
        client_list = WindowP.from_buffer(client_list)
        clients = client_list[: size // sizeof(WindowP)]
        XFree(client_list)
        return clients

    result = get_property(disp, root, XA_WINDOW, "_WIN_CLIENT_LIST")
    if result:
        client_list, size = result
        if client_list:
            client_list = WindowP.from_buffer(client_list)
            clients = client_list[: size // sizeof(WindowP)]
            XFree(client_list)
            return clients
    return None


def get_window_pid(disp: "DisplayP", win: "Window") -> int:
    """ Return process ID stored in _NET_WM_PID, if none, return -1 """
    result = get_property(disp, win, XA_CARDINAL, "_NET_WM_PID")
    if result:
        prop = c_ulong_p.from_buffer(result[0])
        pid = prop.contents.value
        XFree(prop)
        return pid
    return -1


def get_window_title(disp: "DisplayP", win: "Window") -> str:
    xa_prop_type = Atom(XInternAtom(disp, b"UTF8_STRING", False))
    result = get_property(disp, win, xa_prop_type, "_NET_WM_NAME")
    if not result:
        result = get_property(disp, win, XA_STRING, "WM_NAME")

    if result:
        prop = c_char_p.from_buffer(result[0])
        title = prop.value.decode("utf8")
        XFree(prop)
        return title

    return "N/A"


def get_window_class(disp: "DisplayP", win: "Window") -> str:
    ret = XClassHint()
    result = XGetClassHint(disp, win, byref(ret))
    if result:
        wm_class = ret.res_name + b"." + ret.res_class
        return wm_class.decode("ascii")
    return "N/A"


def get_window_desktop_id(disp: "DisplayP", win: "Window") -> Union[int, None]:
    result = get_property(disp, win, XA_CARDINAL, "_NET_WM_DESKTOP")
    if not result:
        result = get_property(disp, win, XA_CARDINAL, "_WIN_WORKSPACE")

    if result:
        prop, _ = result
        desktop = c_ulong_p.from_buffer(prop).contents.value
        XFree(prop)
        return c_long(desktop).value if desktop else 0
    return None


def get_window_geometry(disp: "DisplayP", win: "Window") -> Tuple[int]:
    junkroot = Window()
    x = c_int()
    y = c_int()
    junkx = c_int()
    junky = c_int()

    wwidth = c_uint()
    wheight = c_uint()
    bw = c_uint()
    depth = c_uint()

    XGetGeometry(
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
    XTranslateCoordinates(
        disp, win, junkroot, junkx, junky, byref(x), byref(y), byref(junkroot)
    )
    return x.value, y.value, wwidth.value, wheight.value, bw.value, depth.value


def get_window_client_machine(disp: "DisplayP", win: "Window") -> str:
    prop = XTextProperty()
    XGetWMClientMachine(disp, win, byref(prop))
    client_machine = c_char_p.from_buffer(prop.value)
    return client_machine.value.decode("ascii") or "N/A"


def list_windows(disp: "DisplayP") -> None:
    max_client_machine_len = 0
    max_class_name_len = 0

    client_list = get_client_list(disp)
    for client in client_list:
        client_machine = get_window_client_machine(disp, client)
        max_client_machine_len = max(len(client_machine), max_client_machine_len)

        wm_class = get_window_class(disp, client)
        max_class_name_len = max(len(wm_class), max_class_name_len)

    for client in client_list:
        title_out = get_window_title(disp, client)
        desktop = get_window_desktop_id(disp, client)
        client_machine = get_window_client_machine(disp, client)

        print("0x%.8lx %2ld" % (client, desktop), end="")

        if SHOW_PID:
            print(" %-6lu" % get_window_pid(disp, client), end="")

        if SHOW_GEOM:
            # x, y, width, height
            print(
                " %-4d %-4d %-4d %-4d" % get_window_geometry(disp, client)[:4], end=""
            )

        if SHOW_CLASS:
            class_out = get_window_class(disp, client)
            print(" %-*s" % (max_class_name_len, class_out), end="")

        print(" %*s %s" % (max_client_machine_len, client_machine, title_out))


if __name__ == "__main__":
    display = XOpenDisplay(None)
    root = XDefaultRootWindow(display)

    # list_windows(display)
    # show_desktop(display, 1)
    # show_desktop(display, 0)

    print(change_number_of_desktops(display, 4))

    xlib.XCloseDisplay(display)
