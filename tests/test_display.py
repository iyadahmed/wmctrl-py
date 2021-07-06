import pytest
from wmctrl.display import *


def test_display_context():
    with Display() as display:
        pass
