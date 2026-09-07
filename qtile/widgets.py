# ═══ imports ══════════════════════════════════════════════════════════════
import subprocess
import xml.etree.ElementTree as ET
from typing import ClassVar

from dbus_fast import InterfaceNotFoundError, InvalidObjectPathError, Variant
from dbus_fast.errors import DBusError
from libqtile import hook, widget
from libqtile.command.base import expose_command
from libqtile.utils import create_task
from libqtile.widget import base
from libqtile.widget.helpers.status_notifier import StatusNotifierItem
from libqtile.widget.helpers.status_notifier.statusnotifier import (
    STATUS_NOTIFIER_ITEM_SPEC,
)

from notify import VOLUME_ID, notify_value
from theme import C, G

# ═══ custom widgets ══════════════════════════════════════════════════════
# Stock qtile has no threshold colouring on CPU, no glyph-based layout
# indicator, and no icon substitution in TaskList. These fill those gaps.


class _Thresholded:
    """Recolour a polled widget as its reading crosses the medium/high marks."""

    def _colorize(self, value, text):
        if value > self.threshold_high:
            self.foreground = C.fg_orange
            return f"🔥 {text}"
        if value > self.threshold_medium:
            self.foreground = C.fg_yellow
            return text
        self.foreground = C.fg_normal
        return text


class ColorizedCPU(_Thresholded, widget.CPU):
    def __init__(self, threshold_medium=65, threshold_high=85, **config):
        self.threshold_medium = threshold_medium
        self.threshold_high = threshold_high
        widget.CPU.__init__(self, **config)

    def poll(self):
        text = widget.CPU.poll(self)
        return self._colorize(float(text.replace("%", "").strip()), text)


# ═══ volume ═══════════════════════════════════════════════════════════════
# Just the speaker glyph. The level itself lives in the dunst notification
# below, which is where you are actually looking when you reach for the volume
# keys - a block meter in a corner of a 34px strip was telling you the same
# thing somewhere you were not.


class VolumeIcon(widget.Volume):
    """The stock speaker glyph, plus a dunst notification on every change.

    With emoji=True and no theme_path the parent already draws exactly one
    thing - the glyph for the current level, or the muted one - so nothing here
    touches the drawing. This subclass only adds the notification.

    That cannot be posted from the commands below: they only run a mixer
    command, and the widget does not learn the new level until do_volume()
    polls for it. Announcing what self.volume held at the moment of the press
    would report the level *before* it, and would be a press behind for as long
    as a key is held.

    So a press only arms a flag, and the next poll - within update_interval,
    0.2s - posts the reading it actually got back. Holding a key down then
    coalesces to one notification per poll rather than one per repeat, which
    keeps a held key from spawning dunstify thirty times a second.
    """

    def __init__(self, **config):
        self._announce = False
        widget.Volume.__init__(self, **config)

    def _volume_icon(self, volume, muted):
        """The glyph _update_drawer picks, on the same thresholds."""
        if not self.emoji or len(self.emoji_list) < 4:
            return ""
        if muted or volume <= 0:
            return self.emoji_list[0]
        if volume <= 30:
            return self.emoji_list[1]
        if volume < 80:
            return self.emoji_list[2]
        return self.emoji_list[3]

    async def get_volume(self):
        volume, muted = await widget.Volume.get_volume(self)
        if self._announce:
            self._announce = False
            # get_volume() reports -1 when the mixer command fails
            level = 0 if muted else max(0, volume)
            icon = self._volume_icon(volume, muted)
            # Mute reads as zero rather than as the level waiting behind it, so
            # the progress bar agrees with the glyph.
            label = "Muted" if muted else f"Volume  {level}%"
            notify_value(f"{icon}  {label}".strip(), level, VOLUME_ID)
        return volume, muted

    @expose_command()
    def increase_vol(self):
        widget.Volume.increase_vol(self)
        self._announce = True

    @expose_command()
    def decrease_vol(self):
        widget.Volume.decrease_vol(self)
        self._announce = True

    @expose_command()
    def mute(self):
        widget.Volume.mute(self)
        self._announce = True


# Only the two layouts actually configured above; extend if you add more.
LAYOUT_ICONS = {
    "tabbedcolumns": "\U000f0322",  # nf-md-tab
    "evencolumns": "",
    "max": "",
}


class CurrentLayoutIcon(base._TextBox):
    """CurrentLayout, drawn as a Nerd Font glyph instead of a name."""

    def _configure(self, qtile, parent_bar):
        base._TextBox._configure(self, qtile, parent_bar)
        self.text = self._icon(parent_bar.screen.group.layout.name)
        hook.subscribe.layout_change(self._on_change)

    def _on_change(self, current_layout, group):
        if group.screen is not None and group.screen is self.bar.screen:
            self.text = self._icon(current_layout.name)
            self.bar.draw()

    def _icon(self, name):
        return LAYOUT_ICONS.get(name, "")  # question mark for unmapped

    def finalize(self):
        hook.unsubscribe.layout_change(self._on_change)
        base._TextBox.finalize(self)


# ═══ input sources ════════════════════════════════════════════════════════
# Replaces the ibus tray icon, which is a GTK panel drawing its own blue "US"
# and takes no styling from anything the bar controls.
#
# Driven through `ibus engine` rather than setxkbmap: ibus-daemon runs with
# --xim and owns the layout in this session, so qtile's stock KeyboardLayout
# widget - which shells out to setxkbmap - would set a layout ibus then
# overrides, and the two would disagree about what is actually active.


def _ibus(*args, timeout=2):
    """Run ibus, returning stripped stdout, or "" if it failed in any way.

    Only the read - `ibus engine` with no argument - has a trustworthy exit
    status. `ibus engine <name>` exits 1 on ibus 1.5.29 even when the switch
    goes through, so next_layout() below ignores what this returns for a set
    rather than treating that 1 as a failure.
    """
    try:
        done = subprocess.run(
            ("ibus", *args),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # see the docstring: a set exits 1 even when it works
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


class KeyboardLayout(base.BackgroundPoll):
    """The active ibus engine as a glyph and a short code: ⌨ US

    `engines` is a list of (engine id, label) pairs, set in config.py, and is
    both the cycle order and the label lookup. `ibus list-engine` prints every
    id available.
    """

    defaults: ClassVar = [
        (
            "engines",
            [("xkb:us::eng", "US")],
            "(engine id, label) pairs, in cycle order.",
        ),
        ("icon", G.keyboard, "Glyph drawn after the label."),
    ]

    def __init__(self, **config):
        base.BackgroundPoll.__init__(self, "", **config)
        self.add_defaults(KeyboardLayout.defaults)
        self.add_callbacks({"Button1": self.next_layout})

    def poll(self):
        return f" {self._label(_ibus('engine'))} {self.icon}"

    def _label(self, engine):
        for name, label in self.engines:
            if name == engine:
                return label
        if not engine:
            return "--"  # ibus is not running, or not answering
        # Not one of the configured pair - somebody switched with ibus's own
        # keybinding. Fall back to the layout out of an xkb id: xkb:us::eng.
        parts = engine.split(":")
        return parts[1].upper() if parts[0] == "xkb" and len(parts) > 1 else engine[:4]

    @expose_command()
    def next_layout(self):
        """Switch to the next configured input source."""
        names = [name for name, _ in self.engines]
        if not names:
            return
        # subprocess.run on the event loop, unlike poll() above: both calls are
        # a few milliseconds, and the read has to see the write, so a keypress
        # cannot leave the bar showing the layout it just switched away from.
        current = _ibus("engine")
        index = names.index(current) + 1 if current in names else 0
        _ibus("engine", names[index % len(names)])
        self.force_update()


# Substring of wm_class (or window title) -> glyph. First match wins, so keep
# the more specific keys above the generic ones.
APP_ICONS = {
    "firefox": "",
    "chromium": "",
    "chrome": "",
    "brave": "",
    "alacritty": "",
    "kitty": "",
    "terminal": "",
    "code": "",
    "vim": "",
    "emacs": "",
    "thunar": "",
    "nautilus": "",
    "pcmanfm": "",
    "mpv": "",
    "spotify": "",
    "slack": "",
    "discord": "",
    "telegram": "",
    "signal": "",
    "gimp": "",
    "blender": "",
    "steam": "",
    "htop": "",
    "virtualbox": "",
}
FALLBACK_ICON = ""  # generic window

# Display names for the APP_ICONS keys that .title() would get wrong.
APP_NAMES = {
    "code": "VS Code",
    "gimp": "GIMP",
    "htop": "htop",
    "mpv": "mpv",
    "pcmanfm": "PCManFM",
    "virtualbox": "VirtualBox",
}


def _prettify(wm_class):
    """Best-effort app name for something not in APP_ICONS."""
    name = ((wm_class[-1] if wm_class else "") or "").strip()
    # reverse-DNS ids (flatpak, GNOME): org.gnome.TextEditor -> TextEditor
    if name.count(".") >= 2:
        name = name.rsplit(".", 1)[-1]
    # snap/flatpak wrappers repeat the name, e.g. 'firefox_firefox'
    parts = []
    for part in name.replace("-", "_").split("_"):
        if part and (not parts or part.lower() != parts[-1].lower()):
            parts.append(part)
    return " ".join(p if p[:1].isupper() else p.title() for p in parts) or "?"


def _app_identity(window):
    """(glyph, app name) for a window - the application, not the document.

    WM_CLASS is (instance, class). The class is normally the app's own name but
    packaging mangles it: Firefox reports ('Navigator', 'firefox_firefox'), so
    neither element is usable raw and both get matched against APP_ICONS.

    Matching is on WM_CLASS alone, deliberately not the title as it used to be:
    the label now names the app, so an icon drawn from the title could disagree
    with it - a terminal running vim would show the vim glyph beside
    "Alacritty".
    """
    wm_class = (window.get_wm_class() if window else None) or []
    haystack = " ".join(wm_class).lower()
    for key, icon in APP_ICONS.items():
        if key in haystack:
            return icon, APP_NAMES.get(key, key.title())
    return FALLBACK_ICON, _prettify(wm_class)


# 0xProto is monospace, so every Unicode space character - thin, hair, em-quad -
# renders as one full 10px cell. A sub-cell gap has to come from pango markup:
# a space shrunk to 6pt measures exactly 5px at our 16px font.
# Width comes from letter_spacing, not from a big font size. A space scaled up
# to size="17000" is 10px taller than the 14px line around it, and pango grows
# the whole line box to fit it - which pushed every entry down the bar.
# letter_spacing adds pure advance and leaves the line metrics alone; these two
# values give the same total width as size="17000" did.
ICON_GAP = '<span size="6144" letter_spacing="9000"> </span>'


class IconTaskList(widget.TaskList):
    """TaskList showing a Nerd Font glyph and the application name."""

    def _configure(self, qtile, bar):
        widget.TaskList._configure(self, qtile, bar)
        # TaskList derives self.markup from its markup_* options and does it in
        # _configure, so it has to be forced on after that - and on the already
        # built text layout too, which read the old value.
        self.markup = True
        self.layout.markup = True

    @property
    def margin_top(self):
        """Centre each entry in the bar.

        The base class draws every box at y = margin_top + padding_top and lets
        whatever is left fall below, so at fontsize 14 in a 34px bar that was 4
        above and 2 below. Deriving the margin from the real line height keeps
        it even if the font size or the bar height changes.
        """
        layout = getattr(self, "layout", None)
        if layout is None:  # asked for before _configure built the layout
            return widget.TaskList.margin_top.fget(self)
        return max(0, (self.bar.size - layout.height) // 2 - self.padding_top)

    def get_taskname(self, window):
        icon, app = _app_identity(window)
        # parse_text is the base class's only hook over the displayed name, and
        # it isn't handed the window - so feed it the name already resolved
        # here. Going through the base still gets the state prefix (minimized,
        # floating) and the markup escaping.
        self.parse_text = lambda _: app
        name = widget.TaskList.get_taskname(self, window)
        return f"{icon}{ICON_GAP}{name}"


# ═══ tray ═════════════════════════════════════════════════════════════════
# Proton VPN registers a tray item but never drew one; qtile dropped it with
#
#   Error starting StatusNotifierItem for
#   org.kde.StatusNotifierItem-proton.vpn.app.gtk-339152:
#   'ProxyInterface' object has no attribute 'get_icon_name'
#
# Its object serves the whole property set over the standard
# org.freedesktop.DBus.Properties interface - IconName, Status, Title, Menu
# all read fine - but the introspection XML it publishes for
# org.kde.StatusNotifierItem declares only the Activate method and the NewIcon
# signal, and not one <property> element. dbus-fast generates a proxy's get_*
# accessors from that XML, so on this item the properties are readable and the
# accessors to read them with are simply never created.
#
# qtile ships a complete spec (STATUS_NOTIFIER_ITEM_SPEC) for apps that
# introspect badly, but only falls back to it when the item interface is
# missing outright. Proton's is present, just empty, so the fallback doesn't
# fire and the first get_icon_name() raises AttributeError - which the helper
# doesn't catch, guarding only DBusError, so the item is discarded.
#
# Rather than reimplement the helper, put the missing accessors back on the
# proxy and let the stock code run: each one reads through Properties.Get,
# which the app does implement.


def _snake(name):
    """IconName -> icon_name, the way dbus-fast names its accessors."""
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in name).lstrip("_")


# Taken from qtile's own spec rather than hardcoded, so this tracks whatever
# the installed version thinks a StatusNotifierItem has.
_SPEC = ET.fromstring(STATUS_NOTIFIER_ITEM_SPEC).find("interface")
_SPEC_PROPERTIES = {
    f"get_{_snake(p.get('name'))}": p.get("name") for p in _SPEC.findall("property")
}
_SPEC_SIGNALS = [f"on_{_snake(s.get('name'))}" for s in _SPEC.findall("signal")]


def _property_reader(properties, interface, name):
    """An accessor with dbus-fast's signature, reading through Properties.Get."""

    async def read():
        if properties is None:
            raise DBusError(
                "org.freedesktop.DBus.Error.UnknownProperty",
                f"{interface} on this item serves no properties interface",
            )
        return (await properties.call_get(interface, name)).value

    return read


async def _properties_interface(item):
    """The item's org.freedesktop.DBus.Properties proxy, or None."""
    try:
        introspection = await item.bus.introspect(item.bus_name, item.path)
        obj = item.bus.get_proxy_object(item.bus_name, item.path, introspection)
        return obj.get_interface("org.freedesktop.DBus.Properties")
    except (InterfaceNotFoundError, DBusError):
        return None


async def _restore_accessors(item):
    """Fill in whatever the item's own introspection left off the proxy."""
    missing = [name for name in _SPEC_PROPERTIES if not hasattr(item, name)]
    # Called on every icon refresh, not just at startup, so it has to be cheap
    # once it has run: the hasattr sweep is the whole guard.
    if missing:
        properties = await _properties_interface(item)
        interface = item.introspection.name
        for accessor in missing:
            reader = _property_reader(properties, interface, _SPEC_PROPERTIES[accessor])
            setattr(item, accessor, reader)

    # An undeclared signal cannot be subscribed to at all, so these are no-ops:
    # the icon still draws, it just won't follow a change the app never told us
    # about. Proton declares NewIcon, which is the one that matters here.
    for subscribe in _SPEC_SIGNALS:
        if not hasattr(item, subscribe):
            setattr(item, subscribe, lambda _callback: None)


# A config reload re-imports this module, so take the stock method out of a
# patch already applied rather than wrapping the wrapper: that chain grows by
# one call per reload and ends in "maximum recursion depth exceeded".
_stock_get_local_icon = getattr(
    StatusNotifierItem._get_local_icon,
    "__wrapped__",
    StatusNotifierItem._get_local_icon,
)


async def _get_local_icon(self, fallback=True):
    # The first thing start() calls once self.item exists, and where the
    # AttributeError above was raised - so the accessors are in place before
    # anything reads one.
    await _restore_accessors(self.item)
    return await _stock_get_local_icon(self, fallback)


_get_local_icon.__wrapped__ = _stock_get_local_icon
StatusNotifierItem._get_local_icon = _get_local_icon


# A left click on the Proton icon did nothing either. The stock widget calls
# the item's Activate, and Proton's implementation of it fires an on_left_click
# callback that the app never sets - the only set_left_click call in the whole
# package is in tray_icon.py's __main__ demo - so the call goes through, is
# answered, and does nothing at all.
#
# The item does report ItemIsMenu, which in the spec means exactly this: the
# menu, not Activate, is where the item's actions are. Proton's menu holds one
# entry whose label tracks the window - "Show" while it is hidden, "Hide" once
# it is up - and clicking that is what raises it.
#
# So a menu-only item's click goes to that entry and everything else keeps the
# stock Activate. The show/hide pair is deliberately both halves of the toggle:
# a second click puts the window away again, the same as using the app's menu.

DBUSMENU_INTERFACE = "com.canonical.dbusmenu"
WINDOW_ENTRY_LABELS = frozenset({"show", "hide", "open", "restore", "show window"})

# The errors a badly behaved item can raise on any of this. AttributeError is
# in here for the same reason the tray fix above exists: an accessor the item's
# introspection never declared.
_ITEM_ERRORS = (
    AttributeError,
    DBusError,
    InterfaceNotFoundError,
    InvalidObjectPathError,
)


def _prop(properties, name, default):
    """One dbusmenu property, unwrapped, with the spec's default if unset."""
    variant = properties.get(name)
    return default if variant is None else variant.value


async def _click_window_entry(item):
    """Click the menu entry that raises the app's window; True if there is one."""
    try:
        path = await item.item.get_menu()
        if not path:
            return False
        introspection = await item.bus.introspect(item.service, path)
        obj = item.bus.get_proxy_object(item.service, path, introspection)
        menu = obj.get_interface(DBUSMENU_INTERFACE)
        # (0, -1): the whole tree from the root. Only the top level is read
        # below, but an item is free to answer with the depth it likes.
        _revision, (_id, _properties, children) = await menu.call_get_layout(0, -1, [])
    except _ITEM_ERRORS:
        return False

    for child in children:
        entry, properties, _grandchildren = child.value
        if _prop(properties, "type", "standard") != "standard":
            continue
        if not (
            _prop(properties, "enabled", True) and _prop(properties, "visible", True)
        ):
            continue
        if _prop(properties, "label", "").strip().lower() not in WINDOW_ENTRY_LABELS:
            continue
        try:
            # The data variant and the timestamp are both required by the
            # signature and read by neither of the menus this fires at.
            await menu.call_event(entry, "clicked", Variant("s", ""), 0)
        except _ITEM_ERRORS:
            return False
        return True

    return False


async def _item_is_menu(item):
    """Whether the item says its actions live in its menu rather than Activate."""
    try:
        return bool(await item.item.get_item_is_menu())
    except _ITEM_ERRORS:
        return False


class StatusNotifier(widget.StatusNotifier):
    """The stock tray widget, clicking a menu-only item aside.

    Also where the module-level fix above is anchored: config.py imports the
    tray from here, so the patch cannot be lost to a tidied-up import.
    """

    def activate(self):
        # The item is read off self now rather than in the coroutine: a click
        # on another icon would move selected_item out from under it.
        if self.selected_item:
            create_task(self._activate(self.selected_item))

    async def _activate(self, item):
        if await _item_is_menu(item) and await _click_window_entry(item):
            return
        item.activate()
