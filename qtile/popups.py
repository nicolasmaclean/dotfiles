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


# ═══ anchoring ════════════════════════════════════════════════════════════
def bar_widget(name):
    """The widget called `name` on the *current* screen's bar, or None.

    Not qtile.widgets_map[name], which is what the popups here used to use.
    That map is global and keyed by name, and register_widget renames
    duplicates - "powerbutton", then "powerbutton_1", "powerbutton_2" - so the
    bare name always resolves to screen 0's widget however many screens there
    are. Its offsetx is measured along screen 0's bar, while the clamp beside
    it uses qtile.current_screen.width: two frames of reference mixed, and the
    popup lands on the right monitor under the wrong glyph. Latent on one
    screen, wrong on every screen but the first as soon as there are two.

    Searching this screen's own bar gives an offsetx in the same frame as the
    clamp. Matching through .reflects is what makes a shared widget work: a
    widget handed to more than one bar appears on the others as a Mirror that
    paints the original's pixels and forwards clicks back to it. The Mirror is
    the object with this bar's offsetx - and its own .name is just "mirror" -
    so match on what it reflects and return the mirror itself.
    """
    top = getattr(getattr(qtile, "current_screen", None), "top", None)
    for widget in getattr(top, "widgets", ()):
        # A Mirror reflects the widget it copies; anything else is its own.
        target = getattr(widget, "reflects", None) or widget
        if getattr(target, "name", None) == name:
            return widget
    return None
