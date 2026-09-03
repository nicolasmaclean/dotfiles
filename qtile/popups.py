# ═══ imports ══════════════════════════════════════════════════════════════
from libqtile import qtile

# ═══ popup keyboard ══════════════════════════════════════════════════════
# A popup is an Internal window that takes input focus while open, so every
# keystroke goes to it and not to whatever you were typing in. The toolkit's
# default keymap binds bare letters for that - h/j/k/l to navigate and space to
# select - which turns ordinary typing into menu operation. Arrows, Enter and
# Escape only.

POPUP_KEYMAP = {
    "left": ["Left"],
    "right": ["Right"],
    "up": ["Up"],
    "down": ["Down"],
    "select": ["Return"],
    "step": ["Tab"],
    "close": ["Escape"],
}


# ═══ liveness ═════════════════════════════════════════════════════════════
def popup_alive(popup):
    """True only if `popup` is both un-killed and still a live window.

    Checking _killed alone is not enough: it is only set by the toolkit's own
    kill(), so a popup whose window went away by any other route would leave a
    stale reference behind and the next click would close nothing.
    """
    if popup is None or getattr(popup, "_killed", True):
        return False
    win = getattr(getattr(popup, "popup", None), "win", None)
    return win is not None and win.wid in qtile.windows_map
