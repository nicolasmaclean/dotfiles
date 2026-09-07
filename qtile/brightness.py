# ═══ imports ══════════════════════════════════════════════════════════════
import os
import subprocess

from libqtile import qtile
from libqtile.log_utils import logger

from notify import BRIGHTNESS_ID, notify_value
from theme import G

# ═══ screen brightness ════════════════════════════════════════════════════
# This used to be a bar widget (BrightnessBar), and the XF86MonBrightness keys
# drove it by name so the meter and the keys could not disagree. With the meter
# gone - the dunst notification says everything it said, and says it where you
# are actually looking - there is nothing left for a widget to draw, so the
# control logic lives here instead and the keys call it directly.
#
# Reading and writing happen on brightnessctl's -e curve rather than on the raw
# sysfs ratio. The panel's response to raw values is perceptually non-linear,
# so linear steps crawl at the top and lurch at the bottom; the curve makes
# each press feel like the same change. A panel at raw 30% is 74% of the way up
# the curve, so the two scales are far apart and mixing them would show one
# number while moving by another.

BACKLIGHT_DIR = "/sys/class/backlight"
EXPONENT = 4  # brightnessctl -e is a fourth-power curve
STEP = 5  # percent of the curve per press
# A floor, because nothing below it has one: brightnessctl clamps neither its
# relative nor its absolute form, and the curve collapses anything under ~7% to
# a raw 0 - a black panel with no way back except the keys you cannot see to
# find. 10% of the curve is the dimmest this panel still lights at.
MIN_PERCENT = 10


def _find_device():
    """First entry in /sys/class/backlight, or None if there is no panel."""
    try:
        return next(iter(sorted(os.listdir(BACKLIGHT_DIR))), None)
    except OSError:
        return None


_DEVICE = _find_device()
# brightnessctl writes /sys/class/backlight unprivileged here thanks to the
# brightness-udev rule plus video-group membership, so none of this needs root.
_BRIGHTNESS_FILE = os.path.join(BACKLIGHT_DIR, _DEVICE or "", "brightness")
_MAX_FILE = os.path.join(BACKLIGHT_DIR, _DEVICE or "", "max_brightness")

# Set while a brightnessctl call is still in flight. Key repeat outruns the
# process, and without this a held key queues a backlog that keeps moving the
# panel after you let go.
_future = None


def _read(path):
    with open(path) as f:
        return float(f.read().strip())


def _current_percent():
    """Where we sit on the -e curve, 0-100, from the raw sysfs ratio."""
    return 100 * (_read(_BRIGHTNESS_FILE) / _read(_MAX_FILE)) ** (1 / EXPONENT)


def _notify(percent):
    notify_value(
        f"{G.brightness}  Brightness  {round(percent)}%", percent, BRIGHTNESS_ID
    )


def _apply(percent):
    """Runs in an executor: brightnessctl is a fork+exec, not a file write."""
    subprocess.run(
        ["brightnessctl", "-e", "set", f"{percent:.0f}%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
        check=False,
    )
    _notify(percent)


def _change(step):
    global _future
    if _DEVICE is None:
        logger.warning("No backlight device in %s", BACKLIGHT_DIR)
        return
    if _future is not None and not _future.done():
        return
    try:
        now = _current_percent()
    except (OSError, ValueError, ZeroDivisionError) as e:
        logger.warning("Cannot read backlight: %s", e)
        return

    new = min(100, now + step) if step > 0 else max(MIN_PERCENT, now + step)
    if new == now:
        # Already against the floor or the ceiling. Acknowledge the press
        # anyway, at the level we are actually at - silence is unhelpful when
        # the notification is the only feedback there is.
        _notify(now)
        return
    _future = qtile.run_in_executor(_apply, new)


def up(_qtile=None):
    _change(STEP)


def down(_qtile=None):
    _change(-STEP)
