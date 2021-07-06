from ctypes import (
    POINTER,
    Structure,
    Union,
    c_char,
    c_int,
    c_long,
    c_short,
    c_ubyte,
    c_uint,
    c_ulong,
    c_void_p,
    c_char_p,
)

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


class XTextProperty(Structure):
    _fields_ = [
        ("value", c_ubyte_p),
        ("encoding", Atom),
        ("format", c_int),
        ("nitems", c_ulong),
    ]


class XClassHint(Structure):
    _fields_ = [("res_name", c_char_p), ("res_class", c_char_p)]
