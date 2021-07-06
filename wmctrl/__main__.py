from wmctrl.core import list_windows
from wmctrl.xfuncs import XCloseDisplay, XDefaultRootWindow, XOpenDisplay


display = XOpenDisplay(None)
root = XDefaultRootWindow(display)

list_windows(display)
# show_desktop(display, 1)
# show_desktop(display, 0)

# change_number_of_desktops(display, 2)
# switch_desktop(display, 1)

# Rename all windows to foo
# for w in get_client_list(display):
#     client_msg(display, w, "_NET_DESKTOP_GEOMETRY", 100, 100, 0, 0, 0)
#     set_window_title(display, w, "foo", "T")

XCloseDisplay(display)
