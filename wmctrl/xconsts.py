from .xtypes import Atom

XA_CARDINAL = Atom(6)
XA_STRING = Atom(31)
XA_WINDOW = Atom(33)
XA_STRING = Atom(31)
XA_WM_NAME = Atom(39)
XA_WM_ICON_NAME = Atom(37)
Success = 0
BadWindow = 3
BadAtom = 5
BadValue = 2
SubstructureRedirectMask = 1048576
SubstructureNotifyMask = 524288
ClientMessage = 33

# XChangeProperty modes
PropModeReplace = 0
PropModePrepend = 1
PropModeAppend = 2
