# Libs
from ctypes import CDLL, POINTER, c_char_p, c_int, c_long, c_void_p

from .xtypes import *

xlib = CDLL("libX11.so.6")


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

XChangeProperty = xlib.XChangeProperty
XChangeProperty.argtypes = [
    DisplayP,
    Window,
    Atom,
    Atom,
    c_int,
    c_int,
    c_char_p,
    c_int,
]
XChangeProperty.restype = None

XDeleteProperty = xlib.XDeleteProperty
XDeleteProperty.argtypes = [DisplayP, Window, Atom]
XDeleteProperty.restype = None

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
