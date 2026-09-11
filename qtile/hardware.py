# ═══ imports ══════════════════════════════════════════════════════════════
import functools
import json
import os
import shutil

import libqtile.core.manager
from libqtile.config import Screen
from libqtile.log_utils import logger

# ═══ what this box is ═════════════════════════════════════════════════════
# Every fact about the *hardware* that config.py would otherwise hardcode:
# which battery, which backlight, which temperature sensor, which wallpaper,
# and how many screens there are. Resolved here at runtime rather than written
# in by a provisioning run, so one config.py serves the laptop and the desktop
# and stays plain hand-editable Python you can reload with mod+ctrl+r.
#
# A flat sibling of config.py, like theme.py and widgets.py, and it imports
# nothing from any of them - so there is no cycle, and Config's
# _reload_config_submodules picks it up on a reload along with the rest.
#
# NOTHING IN HERE MAY RAISE. A config exception does not leave you at a black
# screen, it leaves you in qtile's own default_config: mod4 bindings, no bar,
# no groups, on a machine you may have no other way into. Every probe is
# wrapped in @safe(fallback), which logs the traceback and returns a stated
# default instead.
#
# Precedence for every fact, highest first:
#
#   QTILE_<NAME> in the environment    testing, and the desktop dry-run
#   ~/.config/qtile-host.json          optional, usually absent
#   detection                          the normal path
#
# An *empty* env value is a real answer meaning "this box has none":
#   QTILE_BATTERY=       -> None        (pretend to be a desktop)
#   QTILE_BATTERY=BAT1   -> pin it
#   unset                -> detect
#
# The JSON file is deliberately outside the repo, so a provisioning run never
# writes through a symlink into a git checkout. It is read if it happens to be
# there and is not created by anything here.


def safe(fallback):
    """Wrap a probe so a broken box costs a log line, not the session."""

    def decorate(probe):
        @functools.wraps(probe)
        def wrapper(*args, **kwargs):
            try:
                return probe(*args, **kwargs)
            except Exception:
                logger.exception(
                    "hardware.%s failed; falling back to %r", probe.__name__, fallback
                )
                return fallback

        return wrapper

    return decorate


_UNSET = object()

_HOST_FILE = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
    "qtile-host.json",
)


@safe({})
@functools.lru_cache(maxsize=1)
def _host_file():
    """~/.config/qtile-host.json, or {} - which is the normal case."""
    try:
        with open(_HOST_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    return data if isinstance(data, dict) else {}


def _override(name):
    """The env or host-file answer for NAME, or _UNSET to go and detect it."""
    env = os.environ.get(f"QTILE_{name}")
    if env is not None:
        # "" is an answer, not an absence - see the header.
        return env or None
    return _host_file().get(name.lower(), _UNSET)


def _fact(name, probe):
    value = _override(name)
    return probe() if value is _UNSET else value


def _first_line(path):
    """The contents of a one-line sysfs file, or None if it is not there."""
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


# ═══ battery ══════════════════════════════════════════════════════════════
POWER_SUPPLY_DIR = "/sys/class/power_supply"


@safe(None)
def battery_name():
    """The ACPI name of the internal pack, or None on a batteryless box.

    Three predicates, taken from the kernel's own classification rather than
    from a name prefix, each of which independently rules out the things that
    have caught this config before:

      type == "Battery"   rules out AC (Mains) and the USB-C PD source ports.
      scope != "Device"   rules out peripherals. A HID++ mouse sets
                          POWER_SUPPLY_SCOPE=Device; an internal pack omits
                          the file, which the ABI defines as System.
      energy_now|charge_now
                          widget.Battery reads one of these on every poll, so
                          an entry without either is one it cannot report on.

    This is the bug the old battery="BAT0" pin documented. qtile's own
    autodetect appends any name that *either* starts with BAT *or* has a
    capacity file, in raw os.listdir order with no preference - which is how
    hidpp_battery_0 (the MX Master 3S) can win, and the widget then renders a
    permanent "Unable to read status for energy_now_file". sorted(), not
    listdir order, so a two-battery ThinkPad answers BAT0 rather than whichever
    the filesystem happened to hand back first.
    """
    for name in sorted(os.listdir(POWER_SUPPLY_DIR)):
        entry = os.path.join(POWER_SUPPLY_DIR, name)
        if _first_line(os.path.join(entry, "type")) != "Battery":
            continue
        if _first_line(os.path.join(entry, "scope")) == "Device":
            continue
        if not any(
            os.path.exists(os.path.join(entry, f)) for f in ("energy_now", "charge_now")
        ):
            continue
        return name
    return None


# ═══ backlight ════════════════════════════════════════════════════════════
BACKLIGHT_DIR = "/sys/class/backlight"

# Best first. firmware is what the vendor's own hotkeys drive, platform is the
# vendor interface, raw is the direct register poke - and on a panel exposing
# more than one of them, driving the wrong one moves a scale nothing is
# looking at. A device whose type is none of these still ranks, just last.
_BACKLIGHT_TYPES = ("firmware", "platform", "raw")


@safe(None)
def backlight_name():
    """The backlight device brightness.py should drive, or None.

    None is the normal answer on a desktop: monitors dim over DDC/CI and
    register nothing here, so the directory exists and is empty. brightness.py
    logs one line per keypress and returns, which is the right behaviour.

    Three things beyond "the first entry", which is all _find_device() used to
    do and which is a coin toss on a two-device panel:

      the type ranking above;
      both brightness and max_brightness present, because _current_percent()
        reads both and a device missing either is not drivable;
      brightnessctl on PATH, because without it the notification would move
        while the panel did not - worse feedback than none at all.
    """
    if shutil.which("brightnessctl") is None:
        logger.warning("brightnessctl is not on PATH; no backlight control")
        return None

    best = None
    for name in sorted(os.listdir(BACKLIGHT_DIR)):
        entry = os.path.join(BACKLIGHT_DIR, name)
        if not all(
            os.path.exists(os.path.join(entry, f))
            for f in ("brightness", "max_brightness")
        ):
            continue
        kind = _first_line(os.path.join(entry, "type"))
        rank = (
            _BACKLIGHT_TYPES.index(kind)
            if kind in _BACKLIGHT_TYPES
            else len(_BACKLIGHT_TYPES)
        )
        if best is None or rank < best[0]:
            best = (rank, name)
    return best[1] if best else None


# ═══ cpu temperature ══════════════════════════════════════════════════════
# (chip, preferred labels best-first). An empty label tuple means "any sensor
# this chip publishes" - cpu_thermal on ARM has exactly one and does not name
# it. On AMD, Tdie is the real junction temperature and Tctl the same reading
# with a vendor offset baked in, so prefer Tdie wherever both exist.
_CPU_CHIPS = (
    ("coretemp", ("Package id 0",)),  # Intel
    ("k10temp", ("Tdie", "Tctl")),  # AMD
    ("zenpower", ("Tdie", "Tctl")),
    ("cpu_thermal", ()),  # ARM / Pi
    ("thinkpad", ("CPU",)),  # last resort: EC, not the package
)

# thinkpad pads its list with five unpopulated slots reading a flat 0.0, and a
# sensor that has gone away can read absurdly high. Neither is a temperature.
_TEMP_MIN = 0.0
_TEMP_MAX = 150.0


def _flatten_sensors():
    """psutil's {chip: [shwtemp]} as ThermalSensor actually sees it.

    The widget flattens the whole tree into one label -> value dict, so the
    tag it is given must be a label that is unique *across chips* - which is
    what makes "Composite" unusable here, nvme publishing it twice.

    The unlabelled-sensor renaming below is copied from the widget rather than
    approximated: it names them "<chip>-<n>" off a counter that runs across
    every chip, so the only way to know what an unlabelled sensor ends up
    called is to count the same way it does.

    Returns label -> list of (chip, value); anything with more than one entry
    is a duplicate the widget would silently overwrite.
    """
    import psutil

    flat = {}
    empty_index = 0
    for chip, sensors in psutil.sensors_temperatures().items():
        for sensor in sensors:
            label = sensor.label
            if not label:
                label = "{}-{}".format(chip if chip else "UNKNOWN", str(empty_index))
                empty_index += 1
            flat.setdefault(label, []).append((chip, sensor.label, sensor.current))
    return flat


@safe(None)
def cpu_temp_sensor():
    """A tag_sensor naming the CPU package, or None if nothing qualifies.

    None is a real answer and a better one than a wrong tag: an unmatched tag
    makes the widget read "N/A" forever with no error logged anywhere, which
    is exactly what "Package id 0" would do on an AMD box.
    """
    flat = _flatten_sensors()

    # The labels the widget could actually read: label -> (chip, raw label).
    usable = {}
    for label, entries in flat.items():
        if len(entries) != 1:
            continue  # owned by two chips - the widget would overwrite it
        chip, raw_label, value = entries[0]
        if not _TEMP_MIN < value < _TEMP_MAX:
            continue
        usable[label] = (chip, raw_label)

    for want_chip, want_labels in _CPU_CHIPS:
        on_chip = [
            (label, raw) for label, (chip, raw) in usable.items() if chip == want_chip
        ]
        if not on_chip:
            continue
        if not want_labels:
            # The chip publishes one unnamed sensor and it is the CPU.
            return min(label for label, _ in on_chip)
        named = [(label, raw) for label, raw in on_chip if raw in want_labels]
        if not named:
            continue
        # Order by how the chip's labels were listed, not alphabetically:
        # Tdie has to beat Tctl.
        return min(named, key=lambda pair: want_labels.index(pair[1]))[0]
    return None


# ═══ wallpaper ════════════════════════════════════════════════════════════
# Searched in this order, first hit wins. The repo copy comes first so a fresh
# clone has one before anything has been downloaded.
_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

# Matched as a *substring*, so re-fetching the same image under a new date
# stamp does not break the config.
_PREFERRED = "puppycat"


def _repo_root():
    """The checkout this file lives in.

    realpath, not abspath: config.py is loaded through the symlinked
    ~/.config/qtile, so abspath would resolve a repo-relative path to a
    location inside ~/.config instead of inside the checkout.
    """
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def _wallpaper_dirs():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return (
        os.path.join(_repo_root(), "wallpapers"),
        os.path.join(data_home, "backgrounds"),
        "/usr/share/backgrounds",
    )


@safe(None)
def wallpaper():
    """A path to paint, or None.

    None is passed straight through to Screen(wallpaper=...), which paints
    nothing and logs nothing. Handing it a path that does not exist is the bad
    case: Painter.paint catches the OSError and logs a full traceback per
    screen on every reconfigure.
    """
    listings = []
    for directory in _wallpaper_dirs():
        try:
            names = sorted(os.listdir(directory))
        except OSError:
            continue
        images = [n for n in names if n.lower().endswith(_IMAGE_SUFFIXES)]
        if images:
            listings.append((directory, images))

    for directory, images in listings:
        for name in images:
            if _PREFERRED in name.lower():
                return os.path.join(directory, name)

    # Nothing preferred anywhere: first image in name order, so a fresh box
    # still gets something rather than X's grey stipple.
    for directory, images in listings:
        return os.path.join(directory, images[0])
    return None


# ═══ screens ══════════════════════════════════════════════════════════════
@safe(0)
def fake_outputs():
    """QTILE_FAKE_OUTPUTS=N, or 0 for the real thing.

    The lever that tests the multi-monitor path from a one-panel laptop. It
    feeds `fake_screens`, which get_screens_from_config checks *before*
    generate_screens - so the screen builder under test is the real one, and
    only the geometry is invented. Xephyr +xinerama is not a substitute:
    _process_screens takes geometry from the real output list, so extra
    Screens there simply go unused.
    """
    raw = os.environ.get("QTILE_FAKE_OUTPUTS")
    return max(0, int(raw)) if raw else 0


@safe((0, 0, 1920, 1080))
def _root_geometry():
    """The whole X display, as (x, y, width, height)."""
    import xcffib
    import xcffib.xproto  # registers the core protocol object xcffib.connect needs

    conn = xcffib.connect()
    try:
        # xcffib types get_setup() as a bare Struct, so pyright cannot see
        # .roots on it; it is there at runtime. mypy does not object.
        root = conn.get_setup().roots[0]  # pyright: ignore[reportAttributeAccessIssue]
        return (0, 0, root.width_in_pixels, root.height_in_pixels)
    finally:
        conn.disconnect()


@safe([])
def fake_rects(count):
    """`count` side-by-side (x, y, w, h) slices of the real display."""
    x0, y0, width, height = _root_geometry()
    slice_w = width // count
    return [(x0 + i * slice_w, y0, slice_w, height) for i in range(count)]


def screen_generator(build):
    """Wrap `build(index, output) -> Screen` into a `generate_screens`.

    generate_screens is the supported API for a machine whose monitor count is
    not known when the config is written: qtile calls it from _process_screens
    at startup *and on every hotplug*, so there is nothing to shell out to and
    nothing to parse.

    A wrapper rather than a comprehension for three reasons:

    1. CACHING, KEYED BY INDEX, IS THE WHOLE POINT. Screen.__eq__ compares by
       *output identity*, not object identity, so a freshly-built Screen for a
       monitor that is still plugged in compares equal to the old one - and
       _process_screens' `if screen not in new_screens: screen.finalize_gaps()`
       therefore never fires. The old bar's window and widgets are never
       finalized, Systray._instances is still 1, and the new bar's Systray
       raises ConfigError("Only one Systray can be used.") and is silently
       dropped. You would lose the tray and leak a bar window on every replug.
       Re-handing the same object is what avoids that.

    2. IT MUST NOT RAISE, and @safe is not enough on its own: _process_screens
       is called outside load_config's try/except, so an exception here at
       startup takes the session with it rather than falling back to
       default_config. A bare Screen has no bar, but it is a working desktop
       you can open a terminal on and read the traceback in.

    3. INDEX, NOT EDID. Keying on the output's identity pins a bar to a
       physical monitor, which sounds nicer until you unplug the primary and
       plug it back: its Screen comes back out of the cache while a second one
       has been built meanwhile, and one of the two trays loses the ConfigError
       coin toss. Index is also what qtile keys group assignment on, and it
       guarantees exactly one Screen carries the tray for the life of the
       session. Nested X publishes no EDID at all - Output(None, None, None,
       None, rect) - which is a second reason not to key on it.

    Entries are never dropped from the cache. A Screen for an index that has
    gone away does get finalized by qtile, but Bar._configure recreates its
    window and drawer if it is ever handed back, and the one Screen that must
    not be rebuilt - index 0, which carries the trays - is never finalized
    while any output at all is present.

    `outputs` arrives already in desk order - see _order_outputs_for_desk
    below, which patches the one spot upstream that both this function and
    _process_screens' own geometry pairing read from. Reordering again in
    here would be pointless: _process_screens pairs config_screens[i] with
    its *own* re-fetched output_info[i], not with whatever `outputs` this
    function was handed, so a local reorder here would only shuffle which
    cached bar style lands on which monitor while the geometry stayed keyed
    to the unordered list underneath it.
    """
    cache = {}

    def generate(outputs):
        try:
            screens = []
            for index, output in enumerate(outputs):
                if index not in cache:
                    cache[index] = build(index, output)
                screens.append(cache[index])
            return screens or [Screen()]
        except Exception:
            logger.exception("screen build failed; falling back to bare screens")
            return [Screen() for _ in outputs] or [Screen()]

    return generate


# _process_screens (libqtile/core/manager.py) calls self.get_output_info()
# *twice knowing it's the same list* - once to hand to generate_screens above,
# once again to zip against whatever generate_screens returned:
#
#   output_info = self.get_output_info()
#   config_screens = self.get_screens_from_config(output_info)   # -> our generate()
#   for i, info in enumerate(output_info):
#       scr = config_screens[i]
#       scr.output = info                                        # <- geometry
#       scr._configure(self, i, info.rect.x, info.rect.y, ...)
#
# scr.output, and therefore every pixel _configure paints, comes from
# output_info[i] - the RAW, RandR-connector-order list - regardless of what
# order generate_screens' return value is in. Sorting inside generate() (see
# the docstring above) only permutes which cached Screen object sits at
# config_screens[i]; _process_screens still glues output_info[i]'s unsorted
# geometry onto it. The two would drift out of step - the tray-carrying
# Screen built for logical index 0 landing on whatever monitor the connector
# order happens to put first, not the physically leftmost one.
#
# The only lever that keeps both reads of output_info consistent is patching
# get_output_info() itself, once, so every caller - ours and
# _process_screens' own second call - sees the same reordered list.
# Qtile.get_output_info is a plain method, not part of any documented
# extension point, which is why this is a monkeypatch rather than a config
# option: there is no generate_screens-shaped hook upstream of the ordering
# _process_screens needs to not undo.

# cnick's desk, screen 0/1/2 left-to-right, matching physical position:
# HDMI-1 (portrait, left), DP-1 (middle), HDMI-0 (right) - confirmed by
# blanking each output live and watching which physical panel went dark;
# the connector names don't sort the way their desk position does. An
# output whose port is not listed here - the laptop's single eDP-*, or a
# monitor plugged in later - sorts after everything named, by (x, y), so it
# never raises and never hijacks a slot a named output is entitled to.
_DESK_ORDER = ("HDMI-1", "DP-1", "HDMI-0")


def _order_outputs_for_desk(get_output_info):
    """Wrap Qtile.get_output_info so its result matches _DESK_ORDER.

    Idempotent against repeat wrapping: a config reload re-execs this module
    (see confreader._reload_config_submodules) and would otherwise nest a new
    ordering wrapper around the previous reload's wrapper on every
    mod+ctrl+r. Reordering an already-ordered list is harmless, but the
    closures would still pile up one per reload for the life of the session.
    """
    if getattr(get_output_info, "_ordered_for_desk", False):
        return get_output_info

    def _key(output):
        try:
            rank = _DESK_ORDER.index(output.port)
        except ValueError:
            rank = len(_DESK_ORDER)
        return (rank, output.rect.x, output.rect.y)

    @functools.wraps(get_output_info)
    def wrapped(self):
        return sorted(get_output_info(self), key=_key)

    wrapped._ordered_for_desk = True
    return wrapped


libqtile.core.manager.Qtile.get_output_info = _order_outputs_for_desk(
    libqtile.core.manager.Qtile.get_output_info
)


# ═══ the answers ══════════════════════════════════════════════════════════
# Resolved once at import. brightness.py reads BACKLIGHT at import time too,
# so these have to be values rather than calls made later.
BATTERY = _fact("BATTERY", battery_name)
BACKLIGHT = _fact("BACKLIGHT", backlight_name)
THERMAL = _fact("THERMAL", cpu_temp_sensor)
WALLPAPER = _fact("WALLPAPER", wallpaper)
FAKE_OUTPUTS = fake_outputs()


def facts():
    return {
        "BATTERY": BATTERY,
        "BACKLIGHT": BACKLIGHT,
        "THERMAL": THERMAL,
        "WALLPAPER": WALLPAPER,
        "FAKE_OUTPUTS": FAKE_OUTPUTS,
    }


if __name__ == "__main__":
    # `python hardware.py` - a sanity check with no qtile involved.
    for key, value in facts().items():
        print(f"{key:<13} {value!r}")
