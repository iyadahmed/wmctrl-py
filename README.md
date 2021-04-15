**work in progress**

> _wmctrl is a command that can be used to interact with an X Window manager that is compatible with the EWMH/NetWM specification. wmctrl can query the window manager for information, and it can request that certain window management actions be taken._

wmctrl(1) - Linux man page

#### What is this?
A port of the wmctrl tool to Python ctypes, no extra dependencies, no subprocess calling

#### Why?
A. To practice calling C libs in Python ctypes <br>
B. This is allows extending and improving on the original wmctrl <br>
C. It servers as a great example for calling C libs from Python ctypes <br>


#### Sites that helped:
* https://docs.rs/x11/2.18.2/x11/xlib/index.html
* https://tronche.com/gui/x/xlib/
