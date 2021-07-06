from .core import XOpenDisplay, XCloseDisplay

# TODO
class Display:
    def __init__(self, display_name=None):
        self.display = XOpenDisplay(display_name)

    def __enter__(self):
        return self.display

    def __exit__(self, type, value, traceback):
        XCloseDisplay(self.display)
