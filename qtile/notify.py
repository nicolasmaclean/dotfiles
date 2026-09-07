# ═══ imports ══════════════════════════════════════════════════════════════
import shutil
import subprocess

from libqtile.log_utils import logger

# ═══ transient readouts ═══════════════════════════════════════════════════
# Brightness and friends are worth a glance, not a log entry: one notification
# that replaces itself on every press and times out in a second or two.
#
# These go through dunst rather than through the qtile-extras popup toolkit
# (popups.py) because dunst is already the session's notification daemon and
# already draws exactly this - ../dunst/dunstrc sets progress_bar = true, so
# the int:value hint below renders as the bar under the text, in the same
# frame, corner and font as every other notification on this desktop. Drawing
# a lookalike in-process would mean keeping two copies of that styling in step.
#
# dunstify, not notify-send: -r (replace an existing notification by id) is a
# dunstify extension, and it is what keeps a held-down key from stacking a
# column of notifications down the right-hand edge.
_DUNSTIFY = shutil.which("dunstify")

# One fixed id per kind of readout, allocated high: dunst hands out its own ids
# from 1 upward, so staying well clear of that range means a notification of
# ours can never land on top of somebody else's.
BRIGHTNESS_ID = 9001
VOLUME_ID = 9002


def notify_value(summary, percent, replace_id, urgency="low", timeout=1500):
    """Post a self-replacing notification with a progress bar at `percent`.

    Blocking, but only just: dunstify without --block is a single D-Bus call
    and returns as soon as dunst has taken the message.
    """
    if _DUNSTIFY is None:
        return
    try:
        subprocess.run(
            [
                _DUNSTIFY,
                "--appname=qtile",
                f"--urgency={urgency}",
                f"--replace={replace_id}",
                f"--timeout={timeout}",
                # dunst draws a progress bar for any notification carrying this
                # hint, and clamps it to 0-100 itself.
                f"--hints=int:value:{round(percent)}",
                summary,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        # A notification is never worth taking a keybinding down with it.
        logger.warning("dunstify failed: %s", e)
