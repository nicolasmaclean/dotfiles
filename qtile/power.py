# ═══ imports ══════════════════════════════════════════════════════════════
import subprocess
from functools import partial

from libqtile import qtile, widget
from qtile_extras.popup.toolkit import PopupAbsoluteLayout, PopupText

from popups import POPUP_KEYMAP, bar_widget, popup_alive
from theme import C, F, G

# ═══ power menu ══════════════════════════════════════════════════════════
# Clicking the power glyph opens a menu built with the same qtile-extras popup
# toolkit as the volume slider, so it inherits click-outside dismissal, Escape
# and arrow-key navigation from that machinery.
#
# Every entry confirms before acting: the menu opens directly under the button,
# where the logout text button used to be, so a misclick is a real power-off.
# polkit already allows poweroff and reboot for a local active session, so
# neither prompts for a password.

POWER_W = 210  # popup width
POWER_PAD = 6  # inner margin
POWER_ROW_H = 34  # one clickable line
POWER_TITLE_H = 30  # "Are you sure?" header


def _logout():
    # qtile's own shutdown rather than `loginctl terminate-session`: it fires
    # the shutdown hook, which is what stops qtile-session.target.
    qtile.shutdown()


def _reboot():
    subprocess.Popen(["systemctl", "reboot"])


def _poweroff():
    subprocess.Popen(["systemctl", "poweroff"])


# glyph, menu label, confirmation label, action
POWER_ACTIONS = [
    (G.shutdown, "Shut down", "Yes, shut down", _poweroff),
    (G.reboot, "Reboot", "Yes, reboot", _reboot),
    (G.logout, "Log out", "Yes, log out", _logout),
]

_power_popup = None


def _close_power_popup():
    global _power_popup
    if popup_alive(_power_popup):
        _power_popup.kill()  # kill() has no re-entry guard, hence the check
    _power_popup = None


def _power_row(index, glyph, label, callback, danger=False, offset_y=0):
    """One clickable line in the menu."""
    return PopupText(
        text=f"{glyph}  {label}",
        pos_x=POWER_PAD,
        pos_y=POWER_PAD + offset_y + index * POWER_ROW_H,
        width=POWER_W - 2 * POWER_PAD,
        height=POWER_ROW_H,
        font=F.normal,
        fontsize=15,
        foreground=C.fg_urgent if danger else C.fg_normal,
        # can_focus is left at "auto", which resolves to True for any control
        # with a Button1 callback. That is what arms the layout's focus hooks -
        # without a focusable control the toolkit never calls set_hooks() and
        # neither click-outside nor Escape would work.
        highlight=C.bg_highlight,
        # Hover lifts the block *and* brightens the text, rather than
        # inverting to dark-on-light: bg_topbar_selected is a near-black
        # border accent, so inverting against it left #1e1e1e text on a
        # #2a2a2a block - 1.16:1, effectively invisible. A destructive row
        # keeps its red instead of going white, so hovering it never reads
        # as ordinary.
        foreground_highlighted=C.fg_urgent if danger else C.fg_white,
        highlight_method="block",
        h_align="left",
        mouse_callbacks={"Button1": callback},
    )


def _show_power_popup(controls, height, initial_focus=None):
    global _power_popup
    _close_power_popup()

    # centre under the power glyph, clamped to the screen edge. Found on the
    # current screen's own bar rather than in qtile.widgets_map - see
    # popups.bar_widget - so offsetx and the clamp below measure along the same
    # bar on a multi-monitor box. The widget is a named subclass because the
    # lookup keys on the class name and a plain TextBox would collide with the
    # other text boxes in the bar.
    btn = bar_widget("powerbutton")
    x = btn.offsetx + btn.length // 2 - POWER_W // 2 if btn is not None else 0
    x = max(0, min(x, qtile.current_screen.width - POWER_W))

    _power_popup = PopupAbsoluteLayout(
        qtile,
        width=POWER_W,
        height=height,
        background=C.bg_topbar,
        border=C.bg_topbar_selected,
        border_width=2,
        # The menu pre-selects its first row so one Down doesn't skip it: with
        # nothing focused, the first key press adopts row 0 and *then* moves.
        # The confirmation passes None instead, so Enter can't fire an action
        # you never selected.
        initial_focus=initial_focus,
        keymap=POPUP_KEYMAP,
        # the row callbacks decide what happens next (confirm, act, or close),
        # so don't let the toolkit tear the popup down underneath them
        close_on_click=False,
        # you click the glyph up in the bar, so the pointer is never inside the
        # popup when it opens - mouse-leave would kill it instantly
        hide_on_mouse_leave=False,
        controls=controls,
    )
    _power_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)


def _confirm_power(glyph, confirm_label, action):
    """Second stage: swap the menu for a yes/cancel prompt."""

    def _do():
        _close_power_popup()
        action()

    controls = [
        PopupText(
            text="Are you sure?",
            pos_x=POWER_PAD,
            pos_y=POWER_PAD,
            width=POWER_W - 2 * POWER_PAD,
            height=POWER_TITLE_H,
            font=F.normal,
            fontsize=14,
            foreground=C.fg_normal,
            h_align="center",
        ),
        _power_row(0, glyph, confirm_label, _do, danger=True, offset_y=POWER_TITLE_H),
        _power_row(1, G.cancel, "Cancel", _close_power_popup, offset_y=POWER_TITLE_H),
    ]
    # Focus Cancel, not the action: focusable_controls is built in control
    # order, so index 1 is the Cancel row. Enter on this popup backs out.
    _show_power_popup(
        controls,
        POWER_PAD * 2 + POWER_TITLE_H + 2 * POWER_ROW_H,
        initial_focus=1,
    )


def power_menu():
    """Button1 on the power glyph: open the menu, or dismiss it if open."""
    if popup_alive(_power_popup):
        _close_power_popup()
        return

    controls = [
        _power_row(i, glyph, label, partial(_confirm_power, glyph, confirm, act))
        for i, (glyph, label, confirm, act) in enumerate(POWER_ACTIONS)
    ]
    _show_power_popup(
        controls,
        POWER_PAD * 2 + len(POWER_ACTIONS) * POWER_ROW_H,
        initial_focus=0,
    )


class PowerButton(widget.TextBox):
    """TextBox under its own name, so the popup can locate it in widgets_map."""
