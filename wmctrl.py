import sys
from ctypes import (
    CDLL,
    POINTER,
    byref,
    sizeof,
    create_string_buffer,
    memmove,
    cast,
    c_char_p,
    c_int,
    c_long,
    c_ubyte,
    c_ulong,
    c_void_p,
)


def p_verbose(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Types
Display = c_void_p
DisplayP = POINTER(Display)
Atom = XID = Time = c_ulong
AtomP = POINTER(Atom)
Window = XID
WindowP = POINTER(Window)
Status = Bool = c_int


# Consts
XA_CARDINAL = Atom(6)
XA_STRING = Atom(31)
XA_WINDOW = Atom(33)
Success = 0
BadWindow = 3
BadAtom = 5
BadValue = 2

MAXLEN = 4096


# Libs
xlib = CDLL("libX11.so")


# Funcs
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


display = OpenDisplay(None)
root = DefaultRootWindow(display)


def get_property(disp, win, xa_prop_type, prop_name):
    xa_ret_type = Atom()
    ret_format = c_int()
    ret_nitems = c_ulong()
    ret_bytes_after = c_ulong()
    ret_prop = POINTER(c_ubyte)()

    xa_prop_name = InternAtom(disp, prop_name.encode(), True)
    if not (xa_prop_name):
        p_verbose("{0} is not in the Host Portable Character Encoding".format(prop_name))
        return None

    # MAX_PROPERTY_VALUE_LEN / 4 explanation (XGetWindowProperty manpage):
    # long_length = Specifies the length in 32-bit multiples of the
    #               data to be retrieved.
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
        p_verbose("Invalid type of {} property.".format(prop_name))
        xlib.XFree(ret_prop)
        return None

    tmp_size = (ret_format.value // (32 // sizeof(c_long))) * ret_nitems.value
    ret = create_string_buffer(tmp_size + 1)
    memmove(ret, ret_prop, tmp_size)
    ret[tmp_size] = b"\0"

    xlib.XFree(ret_prop)
    return ret, tmp_size


def get_window_pid(disp, win):
    result = get_property(disp, win, XA_CARDINAL, "_NET_WM_PID")
    if result:
        prop, size = result
        prop = cast(prop, POINTER(c_long))
        return prop.contents.value
    return None


def get_client_list(disp):
    client_list, size = get_property(
        disp, DefaultRootWindow(disp), XA_WINDOW, "_NET_CLIENT_LIST"
    )
    client_list = cast(client_list, WindowP)
    if not client_list:
        client_list, size = get_property(
            disp, DefaultRootWindow(disp), XA_WINDOW, "_WIN_CLIENT_LIST"
        )
        client_list = cast(client_list, WindowP)
        if not client_list:
            p_verbose(
                "Cannot get client list properties. \n"
                "(_NET_CLIENT_LIST or _WIN_CLIENT_LIST)"
            )
            return None
    return client_list, size


def list_windows(disp):
    client_list = WindowP()
    # client_list_size = c_ulong()
    i = c_int()
    max_client_machine_len = 0

    client_list, size = get_client_list(disp)
    if not client_list:
        return None


pid = get_window_pid(display, 0x05200003)

print(pid)

xlib.XCloseDisplay(display)
