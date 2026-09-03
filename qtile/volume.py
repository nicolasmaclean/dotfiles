# ═══ imports ══════════════════════════════════════════════════════════════
import subprocess

from libqtile import qtile
from qtile_extras.popup.toolkit import PopupRelativeLayout, PopupSlider, PopupText

from popups import POPUP_KEYMAP, popup_alive
from theme import C, F

# ═══ volume slider popup ═════════════════════════════════════════════════
# Left-clicking the volume glyph opens a draggable slider under it.
# PopupSlider tracks the pointer while the button is held and hands the final
# value to drag_callback on release.

SINK = "@DEFAULT_AUDIO_SINK@"
POPUP_W, POPUP_H = 250, 86


def _volume_get():
    out = subprocess.run(
        ["wpctl", "get-volume", SINK], capture_output=True, text=True
    ).stdout
    return float(out.split()[1])  # "Volume: 0.76 [MUTED]"


def _volume_set(value):
    subprocess.run(
        ["wpctl", "set-volume", "-l", "1.0", SINK, f"{round(value * 100)}%"],
        check=False,
    )


VOLUME_LABEL = "Volume   {}%"


class LabelledSlider(PopupSlider):
    """PopupSlider that keeps a sibling PopupText in step while dragging.

    The stock control only reports its value through drag_callback on release,
    so the readout would sit stale until you let go.
    """

    def __init__(self, label_name="label", label_format="{}", **config):
        PopupSlider.__init__(self, **config)
        self._label_name = label_name
        self._label_format = label_format

    def pointer_motion(self, x, y):
        # the parent recomputes self.value from the pointer and repaints the bar
        PopupSlider.pointer_motion(self, x, y)
        if self._drag:
            self._sync_label()

    def _sync_label(self):
        label = next(
            (c for c in self.container.controls if c.name == self._label_name), None
        )
        if label is None:
            return
        text = self._label_format.format(round(self.value * 100))
        # motion fires far faster than the value changes a whole percent, so
        # only repaint when the text actually differs
        if label.text != text:
            label.text = text
            self.container.draw()  # clears and repaints every control


_volume_popup = None


def toggle_volume_slider():
    """Button1 on the volume widget: open the slider, or dismiss it if open."""
    global _volume_popup

    if popup_alive(_volume_popup):
        _volume_popup.kill()
        _volume_popup = None
        return
    _volume_popup = None

    vol = _volume_get()

    # centre the popup under the volume glyph, clamped to the screen edge
    # NB: offsetx, not offset — info() reports it as "offset" but the attribute
    # on the widget is offsetx.
    vol_widget = qtile.widgets_map.get("volume")
    if vol_widget is not None:
        x = vol_widget.offsetx + vol_widget.length // 2 - POPUP_W // 2
    else:
        x = 0
    x = max(0, min(x, qtile.current_screen.width - POPUP_W))

    _volume_popup = PopupRelativeLayout(
        qtile,
        width=POPUP_W,
        height=POPUP_H,
        background=C.bg_topbar,
        border=C.bg_topbar_selected,
        border_width=2,
        initial_focus=None,
        keymap=POPUP_KEYMAP,
        close_on_click=False,  # a click here starts a drag; don't dismiss on it
        # Not hide_on_mouse_leave: you click the glyph up in the bar, so the
        # pointer is never inside the popup when it opens and it reads as an
        # immediate "leave" — the popup dies before it can be seen. Dismiss is
        # a second click on the glyph, or Escape.
        hide_on_mouse_leave=False,
        controls=[
            PopupText(
                text=VOLUME_LABEL.format(round(vol * 100)),
                name="label",
                pos_x=0.06,
                pos_y=0.14,
                width=0.88,
                height=0.28,
                font=F.normal,
                fontsize=15,
                foreground=C.fg_normal,
                h_align="center",
            ),
            LabelledSlider(
                name="volume",
                label_name="label",
                label_format=VOLUME_LABEL,
                value=vol,
                # The toolkit derives keyboard_navigation from whether any
                # control is focusable, overwriting the layout's own setting.
                # Without a focusable control it never calls set_hooks(), so
                # nothing watches focus and the popup can only be dismissed by
                # clicking the glyph again. can_focus arms the focus hooks,
                # which is what closes it on a click elsewhere (and on Escape).
                can_focus=True,
                # ...but focusable controls also highlight on hover, in a teal
                # that clashes badly. Match the popup background to hide it.
                highlight=C.bg_topbar,
                pos_x=0.09,
                pos_y=0.52,
                width=0.82,
                height=0.30,
                colour_below=C.bg_topbar_selected,
                colour_above=C.bg_topbar_arrow,
                marker_colour=C.fg_normal,
                marker_size=14,
                bar_size=6,
                bar_border_size=0,
                end_margin=0,
                drag_callback=_volume_set,
            ),
        ],
    )
    # relative_to=1 anchors to the screen's top-left, so x/y are plain screen
    # coordinates; relative_to_bar drops y below the bar. Note relative_to=0
    # is NOT absolute — it ignores x/y and places the popup at the pointer.
    _volume_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)


def toggle_mute():
    """Button3 on the volume widget."""
    subprocess.run(["wpctl", "set-mute", SINK, "toggle"], check=False)
