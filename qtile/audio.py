# ═══ imports ══════════════════════════════════════════════════════════════
import re
import subprocess
from functools import partial

from libqtile import qtile
from qtile_extras.popup.toolkit import PopupAbsoluteLayout, PopupText

from popups import POPUP_KEYMAP, bar_widget, popup_alive
from theme import C, F, G

# ═══ audio output ═════════════════════════════════════════════════════════
# Sink switching goes through wpctl, same as VolumeIcon in widgets.py: this box
# is PipeWire, and wpctl talks to it directly. `wpctl status` is also the only
# listing that gives a human sink name ("CSRA64210 ... Analog Stereo") rather
# than pactl's ALSA card path, and it already marks the current default with a
# leading '*' - one parse gets both the menu contents and which row is checked.
#
# No rescan/executor dance like network.py's Wi-Fi list: `wpctl status` is a
# local, instant read, not a hardware scan, so the menu is just built and shown
# synchronously - closer to power.py's popup than to network.py's.

AUDIO_W = 340  # popup width
AUDIO_PAD = 6  # inner margin
AUDIO_ROW_H = 30  # one clickable line
MAX_SINKS = 8  # sinks listed before the list is cut off
NAME_CHARS = 40  # truncation inside the menu
WPCTL_TIMEOUT = 3  # seconds before a reading is given up on

# One line of `wpctl status`'s Sinks block, e.g.:
#   " │  *   55. CSRA64210 [TaoTronics ...] Analog Stereo   [vol: 0.35 MUTED]"
# The name itself can contain '[...]' (a monitor or headset model in brackets),
# so the lazy .+? is anchored on the literal "[vol:" rather than on the first
# bracket - that string only ever appears once, right before the reading.
_SINK_RE = re.compile(r"^[\s│]*(\*)?\s*(\d+)\.\s+(.+?)\s*\[vol:")


# ═══ wpctl ════════════════════════════════════════════════════════════════
def _spawn(argv):
    """Fire and forget. Output is dropped; failures announce themselves."""
    try:
        subprocess.Popen(
            argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def _wpctl(*args, timeout=WPCTL_TIMEOUT):
    """Run wpctl and return stdout, or None if it failed in any way."""
    try:
        done = subprocess.run(
            ("wpctl", *args),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def _sinks():
    """[(id, name, is_default), ...] straight out of `wpctl status`'s Sinks
    block, in the order wpctl lists them."""
    out = _wpctl("status")
    if out is None:
        return []
    lines = out.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if "Sinks:" in line)
        end = next(
            i for i, line in enumerate(lines[start + 1 :], start + 1) if "Sources:" in line
        )
    except StopIteration:
        return []

    sinks = []
    for line in lines[start + 1 : end]:
        match = _SINK_RE.match(line)
        if match:
            default, sink_id, name = match.groups()
            sinks.append((sink_id, name.strip(), default == "*"))
    return sinks[:MAX_SINKS]


# ═══ actions ══════════════════════════════════════════════════════════════
def _select_sink(sink_id):
    _close_audio_popup()
    _spawn(["wpctl", "set-default", sink_id])


# ═══ the menu ═════════════════════════════════════════════════════════════
_audio_popup = None


def _close_audio_popup():
    global _audio_popup
    if popup_alive(_audio_popup):
        _audio_popup.kill()  # kill() has no re-entry guard, hence the check
    _audio_popup = None


def _sink_label(name, is_default):
    short = name if len(name) <= NAME_CHARS else name[: NAME_CHARS - 1] + "…"
    mark = f"  {G.check}" if is_default else ""
    return f"{G.device_speaker}  {short}{mark}"


def _audio_row(offset_y, text, callback, is_default):
    return PopupText(
        text=text,
        pos_x=AUDIO_PAD,
        pos_y=offset_y,
        width=AUDIO_W - 2 * AUDIO_PAD,
        height=AUDIO_ROW_H,
        font=F.normal,
        fontsize=15,
        foreground=C.fg_white if is_default else C.fg_normal,
        highlight=C.bg_highlight,
        foreground_highlighted=C.fg_white,
        highlight_method="block",
        h_align="left",
        mouse_callbacks={"Button1": callback},
    )


def _show_menu(sinks):
    global _audio_popup
    _close_audio_popup()

    controls, y = [], AUDIO_PAD
    for sink_id, name, is_default in sinks:
        controls.append(
            _audio_row(y, _sink_label(name, is_default), partial(_select_sink, sink_id), is_default)
        )
        y += AUDIO_ROW_H
    y += AUDIO_PAD

    # Right-align under the button, clamped to the screen edge - see
    # popups.bar_widget for why this goes through it rather than
    # qtile.widgets_map, and network.py's _show_menu for the same anchoring.
    button = bar_widget("volume")
    if button is not None:
        x = button.offsetx + button.length - AUDIO_W
    else:
        x = qtile.current_screen.width - AUDIO_W
    x = max(0, min(x, qtile.current_screen.width - AUDIO_W))

    _audio_popup = PopupAbsoluteLayout(
        qtile,
        width=AUDIO_W,
        height=y,
        background=C.bg_topbar,
        border=C.bg_topbar_selected,
        border_width=2,
        initial_focus=None,
        keymap=POPUP_KEYMAP,
        close_on_click=False,
        # opened by a click up in the bar, so the pointer is never inside the
        # popup when it opens - mouse-leave would kill it instantly
        hide_on_mouse_leave=False,
        controls=controls,
    )
    _audio_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)


def audio_menu():
    """Button3 on the volume glyph: open the output menu, or dismiss it."""
    if popup_alive(_audio_popup):
        _close_audio_popup()
        return
    sinks = _sinks()
    if sinks:
        _show_menu(sinks)
