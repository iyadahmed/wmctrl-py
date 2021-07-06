from .core import get_window_title

# TODO
class Window:
    _window: int
    _display: int

    @property
    def title(self, display):
        get_window_title(self._window, self._display)
