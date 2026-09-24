# ═══ imports ══════════════════════════════════════════════════════════════
import shutil
import subprocess

from libqtile.log_utils import logger

# ═══ transient readouts ═══════════════════════════════════════════════════
# Brightness and friends are worth a glance, not a log entry: one notification
# that replaces itself on every press and times out in a second or two.
#
# These go through whatever owns org.freedesktop.Notifications rather than
# through the qtile-extras popup toolkit (popups.py), so they share the frame,
# corner and font of every other notification. The int:value hint below is the
# de-facto progress-bar hint; nothing answers the bus in a bare qtile session
# any more (dunst is gone, quickshell only runs under Hyprland), and without a
# daemon notify-send simply fails and is logged.
#
# --replace-id (libnotify >= 0.8) is what keeps a held-down key from stacking a
# column of notifications down the right-hand edge.
_NOTIFY_SEND = shutil.which("notify-send")

# One fixed id per kind of readout, allocated high: daemons hand out their own
# ids from 1 upward, so staying well clear of that range means a notification
# of ours can never land on top of somebody else's.
BRIGHTNESS_ID = 9001
VOLUME_ID = 9002


def notify_value(summary, percent, replace_id, urgency="low", timeout=1500):
    """Post a self-replacing notification with a progress bar at `percent`.

    Blocking, but only just: notify-send without --wait is a single D-Bus call
    and returns as soon as the daemon has taken the message.
    """
    if _NOTIFY_SEND is None:
        return
    try:
        subprocess.run(
            [
                _NOTIFY_SEND,
                "--app-name=qtile",
                f"--urgency={urgency}",
                f"--replace-id={replace_id}",
                f"--expire-time={timeout}",
                # The daemon draws a progress bar for any notification carrying
                # this hint.
                f"--hint=int:value:{round(percent)}",
                summary,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        # A notification is never worth taking a keybinding down with it.
        logger.warning("notify-send failed: %s", e)
