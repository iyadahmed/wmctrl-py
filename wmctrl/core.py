import sys
from ctypes import (
    CDLL,
    POINTER,
    byref,
    c_char_p,
    c_int,
    c_long,
    c_uint,
    c_ulong,
    c_void_p,
    sizeof,
)

# ctypes Union collides
from typing import List, Tuple, Union as TypingUnion

from .xconsts import *
from .xfuncs import *
from .xtypes import *

# TODO: error handler for XSetErrorHandler

# TODO: parse command-line arguments
VERBOSE = False
SHOW_PID = True
SHOW_GEOM = True
SHOW_CLASS = True


def p_verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, file=sys.stderr, **kwargs)


MAXLEN = 4096


class XError(Exception):
    """Generic XLib error"""

    pass


# TODO: more exception classes


def client_msg(
    disp: "DisplayP",
    win: "Window",
    msg: str,
    data0: int,
    data1: int,
    data2: int,
    data3: int,
    data4: int,
) -> None:

    event = XEvent()
    mask = SubstructureRedirectMask | SubstructureNotifyMask
    event.xclient.type = ClientMessage
    event.xclient.serial = 0
    event.xclient.send_event = True
    event.xclient.message_type = XInternAtom(disp, msg.encode("ascii"), False)
    event.xclient.window = win
    event.xclient.format = 32
    event.xclient.data.l[0] = data0
    event.xclient.data.l[1] = data1
    event.xclient.data.l[2] = data2
    event.xclient.data.l[3] = data3
    event.xclient.data.l[4] = data4

    result = XSendEvent(disp, XDefaultRootWindow(disp), False, mask, byref(event))
    # TODO: raise error on BadWindow and BadValue
    if result == 0:
        raise XError("Conversion to wire protocol format failed")


def show_desktop(disp: "DisplayP", state: bool) -> None:
    root = XDefaultRootWindow(disp)
    try:
        client_msg(disp, root, "_NET_SHOWING_DESKTOP", state, 0, 0, 0, 0)
    except XError:
        raise XError("Showing desktop failed")


def change_viewport(disp: "DisplayP", x: int, y: int) -> TypingUnion["XEvent", None]:
    root = XDefaultRootWindow(disp)
    try:
        client_msg(disp, root, "_NET_DESKTOP_VIEWPORT", x, y, 0, 0, 0)
    except XError:
        raise XError("Changing viewport failed")


def change_geometry(disp: "DisplayP", x: int, y: int) -> TypingUnion["XEvent", None]:
    root = XDefaultRootWindow(disp)
    try:
        client_msg(disp, root, "_NET_DESKTOP_GEOMETRY", x, y, 0, 0, 0)
    except XError:
        pass


def change_number_of_desktops(disp: "DisplayP", n: int) -> TypingUnion["XEvent", None]:
    root = XDefaultRootWindow(disp)
    return client_msg(disp, root, "_NET_NUMBER_OF_DESKTOPS", n, 0, 0, 0, 0)


def switch_desktop(disp: "DisplayP", target: int) -> TypingUnion["XEvent", None]:
    root = XDefaultRootWindow(disp)
    return client_msg(disp, root, "_NET_CURRENT_DESKTOP", target, 0, 0, 0, 0)


def set_window_title(disp: "DisplayP", win: "Window", title: str, mode: str) -> None:

    title_local = None
    title_utf8 = None
    try:
        title_local = title.encode("ascii")
    except UnicodeEncodeError:
        pass

    title_utf8 = title.encode("utf8")

    if mode in ("T", "N"):
        if title_local:
            XChangeProperty(
                disp,
                win,
                XA_WM_NAME,
                XA_STRING,
                8,
                PropModeReplace,
                title_local,
                len(title_local),
            )
        else:
            XDeleteProperty(disp, win, XA_WM_NAME)

        XChangeProperty(
            disp,
            win,
            XInternAtom(disp, b"_NET_WM_NAME", False),
            XInternAtom(disp, b"UTF8_STRING", False),
            8,
            PropModeReplace,
            title_utf8,
            len(title_utf8),
        )

    if mode in ("T", "I"):
        if title_local:
            XChangeProperty(
                disp,
                win,
                XA_WM_ICON_NAME,
                XA_STRING,
                8,
                PropModeReplace,
                title_local,
                len(title_local),
            )
        else:
            XDeleteProperty(disp, win, XA_WM_ICON_NAME)

        XChangeProperty(
            disp,
            win,
            XInternAtom(disp, b"_NET_WM_ICON_NAME", False),
            XInternAtom(disp, b"UTF8_STRING", False),
            8,
            PropModeReplace,
            title_utf8,
            len(title_utf8),
        )


def window_to_desktop(
    disp: "DisplayP", win: "Window", desktop: c_int
) -> TypingUnion["XEvent", None]:
    """Move a window to a specified desktop

    Args:
        disp (DisplayP): The connection to the X server
        win (Window): Window to be moved
        desktop (c_int): Number of target desktop, -1 for current

    Returns:
        XEvent | None: [description]
    """
    root = XDefaultRootWindow(disp)

    if desktop == -1:
        cur_desktop = get_property(disp, root, XA_CARDINAL, "_NET_CURRENT_DESKTOP")
        if cur_desktop is None:
            cur_desktop = get_property(disp, root, XA_CARDINAL, "_WIN_WORKSPACE")
            if cur_desktop is None:
                p_verbose(
                    "Cannot get current desktop properties. "
                    "(_NET_CURRENT_DESKTOP or _WIN_WORKSPACE property)"
                    "\n"
                )
                # TODO


def get_property(
    disp: "DisplayP", win: "Window", xa_prop_type: "Atom", prop_name: str
) -> TypingUnion[Tuple["c_ubyte_p", int], None]:

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


def get_client_list(disp: "DisplayP") -> TypingUnion[List[int], None]:
    root = XDefaultRootWindow(disp)
    result = get_property(disp, root, XA_WINDOW, "_NET_CLIENT_LIST")
    if result:
        client_list, size = result
        client_list = WindowP.from_buffer(client_list)
        clients = client_list[: size // sizeof(Window)]
        XFree(client_list)
        return clients

    result = get_property(disp, root, XA_WINDOW, "_WIN_CLIENT_LIST")
    if result:
        client_list, size = result
        if client_list:
            client_list = WindowP.from_buffer(client_list)
            clients = client_list[: size // sizeof(Window)]
            XFree(client_list)
            return clients
    return None


def get_window_pid(disp: "DisplayP", win: "Window") -> int:
    """Return process ID stored in _NET_WM_PID, if none, return -1"""
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


def get_window_desktop_id(disp: "DisplayP", win: "Window") -> TypingUnion[int, None]:
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
