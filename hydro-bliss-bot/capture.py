"""Find the game window and grab screenshots of it."""

import mss
import pygetwindow as gw
from PIL import Image


class GameWindowNotFound(Exception):
    pass


def find_window(title_substring):
    """Return the first visible window whose title contains `title_substring`."""
    matches = [
        w for w in gw.getAllWindows()
        if title_substring.lower() in (w.title or "").lower()
        and w.visible and w.width > 0 and w.height > 0
    ]
    if not matches:
        return None
    # Prefer the largest match (avoids picking a tiny helper/console window).
    return max(matches, key=lambda w: w.width * w.height)


def list_window_titles():
    """All non-empty window titles, for troubleshooting 'window not found'."""
    return sorted({w.title for w in gw.getAllWindows() if (w.title or "").strip()})


def focus_window(win):
    """Bring the game to the foreground so it receives our keypresses."""
    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception:
        # activate() can throw on some window managers; a failure here just
        # means the game might not be focused. The caller keeps going.
        pass


def capture(win):
    """Return a PIL RGB image of the game window's current contents."""
    region = {"left": win.left, "top": win.top, "width": win.width, "height": win.height}
    with mss.mss() as sct:
        raw = sct.grab(region)
    return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
