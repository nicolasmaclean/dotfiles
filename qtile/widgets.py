# ═══ imports ══════════════════════════════════════════════════════════════
import asyncio
import string
import subprocess
import xml.etree.ElementTree as ET
from typing import ClassVar

from dbus_fast import InterfaceNotFoundError, InvalidObjectPathError, Variant
from dbus_fast.errors import DBusError
from libqtile import pangocffi, widget
from libqtile.command.base import expose_command
from libqtile.utils import create_task
from libqtile.widget import base
from libqtile.widget.helpers.status_notifier import StatusNotifierItem, host
from libqtile.widget.helpers.status_notifier.statusnotifier import (
    STATUS_NOTIFIER_ITEM_SPEC,
)
from libqtile.widget.mpris2widget import Mpris2Formatter

from notify import VOLUME_ID, notify_value
from spotify_web import SpotifyWeb
from theme import C, G

# ═══ custom widgets ══════════════════════════════════════════════════════
# Stock qtile has no threshold colouring on CPU, no glyph-based layout
# indicator, and no icon substitution in TaskList. These fill those gaps.


class _Thresholded:
    """Recolour a polled widget as its reading crosses the medium/high marks.

    Colour and nothing else: the text is handed back untouched, so a readout
    padded to a fixed width by the caller's format string stays that width in
    every state and nothing further along the bar steps sideways as the reading
    climbs and falls.

    The colour goes on the text layout and not only on self.foreground. That
    attribute is read once, when _configure builds the layout, and update()
    never syncs it again - so setting it alone changes what the widget thinks
    its colour is and nothing about what it draws. The layout reads .colour at
    draw time, which is also why writing it from a poll thread is safe: the
    draw itself happens later, back on the event loop.
    """

    def _colorize(self, value, text):
        if value > self.threshold_high:
            color = C.fg_orange
        elif value > self.threshold_medium:
            color = C.fg_yellow
        else:
            color = C.fg_normal
        self.foreground = color
        if self.layout is not None:
            self.layout.colour = color
        return text


class ColorizedCPU(_Thresholded, widget.CPU):
    def __init__(self, threshold_medium=65, threshold_high=85, **config):
        self.threshold_medium = threshold_medium
        self.threshold_high = threshold_high
        widget.CPU.__init__(self, **config)

    def poll(self):
        text = widget.CPU.poll(self)
        try:
            load = float(text.replace("%", "").strip())
        except ValueError:
            # The parse only works for config.py's format="{load_percent:5.1f}%",
            # which is a coupling between two files that nothing enforces. A
            # format carrying anything else is a colour we cannot compute, not a
            # readout worth dropping - draw it in the last colour we set.
            return text
        return self._colorize(load, text)


# ═══ group box ════════════════════════════════════════════════════════════
# Stock GroupBox's highlight_method="text" cannot tell "shown on this bar's
# screen" from "shown on some other screen": in libqtile's own draw(), the
# `if g.screen:` branch for text mode always resolves to
# this_current_screen_border for *any* group that is displayed anywhere,
# regardless of which screen - this_screen_border, other_current_screen_border
# and other_screen_border are simply dead code under "text". Setting
# this_screen_border blue and other_screen_border white therefore paints every
# shown group blue on every bar, on every screen. Only "block" and "line" read
# those four colours - and both draw a border/box around the label rather than
# just colouring it, which is not what the bar wants here.
class ScreenGroupBox(widget.GroupBox):
    """A text-mode GroupBox that actually distinguishes this screen from others.

    Reimplements draw() rather than patching around the parent's, since the
    three-way choice (this bar's screen / another screen / no screen) has to
    replace the two-way one baked into GroupBox.draw(), not layer on top of
    it. Click handling, hooks and geometry are all still the parent's -
    this only changes which colour each label is drawn in:
      this_current_screen_border   the group shown on *this* bar's screen
      other_current_screen_border  a group shown on a different screen
      active / inactive            a group not shown on any screen
    """

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)
        offset = self.margin_x
        for g in self.groups:
            if self.group_has_urgent(g) and self.urgent_alert_method == "text":
                text_color = self.urgent_text
            elif g.windows:
                text_color = self.active
            else:
                text_color = self.inactive

            if g.screen is self.bar.screen:
                text_color = self.this_current_screen_border
            elif g.screen is not None:
                text_color = self.other_current_screen_border

            bw = self.box_width([g])
            self.drawbox(offset, g.label, None, text_color, width=bw)
            offset += bw + self.spacing
        self.draw_at_default_position()


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


# ═══ now playing ══════════════════════════════════════════════════════════


class NowPlaying(widget.Mpris2):
    """Mpris2 that elides a long track line instead of scrolling it.

    The stock widget's scrolling shifts the whole layout, so the player glyph -
    which has to live inside the text, being the only part of the widget that
    can disappear along with the track - is dragged out of view with it. The
    glyph belongs at the left edge, so the line is cut to fit instead and
    nothing moves.

    The cut is made on the raw metadata, before it is escaped: trimming the
    finished string could slice a pango escape (&amp;) in half and hand the
    text layout markup it cannot parse. So the line is built twice - once
    unescaped, to measure and cut, and once escaped, on the way out.

    It also falls back to Spotify's Web API when nothing is playing on this
    machine. MPRIS is a local bus and knows nothing about the account, so
    playing from the phone left the bar blank; the API answers for the account
    and so covers every device signed into it. MPRIS stays the primary source
    wherever it has an answer - it is pushed, and instant, where the API is
    polled and lags by up to remote_poll_interval.
    """

    defaults: ClassVar = [
        ("max_track_chars", 40, "Longest track line drawn, in characters."),
        (
            "remote_playing_text",
            None,
            (
                "Text to show when the account is playing on another device. "
                "Takes {track}, {device} and {device_glyph}. "
                "``None`` turns the Web API fallback off entirely."
            ),
        ),
        (
            "remote_paused_text",
            None,
            (
                "As remote_playing_text, for a paused remote device. "
                "``None`` shows nothing for one."
            ),
        ),
        (
            "remote_poll_interval",
            10,
            (
                "Seconds between Web API polls. Spotify rate limits on a rolling "
                "30 second window, which this is nowhere near."
            ),
        ),
        (
            "remote_device_glyphs",
            {},
            (
                "Spotify device type ('Computer', 'Smartphone', ...) to glyph, "
                "for {device_glyph}. The 'default' key covers unlisted types."
            ),
        ),
    ]

    class _PlainFormatter(Mpris2Formatter):
        """The widget's own formatter, with the markup escaping taken out."""

        def get_value(self, key, args, kwargs):
            kwargs = {k.replace(":", "_"): v for k, v in kwargs.items()}
            try:
                return string.Formatter.get_value(self, key, args, kwargs)
            except (IndexError, KeyError):
                return self._default

    def __init__(self, **config):
        widget.Mpris2.__init__(self, **config)
        self.add_defaults(NowPlaying.defaults)
        self._plain_formatter = self._PlainFormatter()
        # Mpris2 turns scrolling on in its own defaults, and _configure then
        # logs "You must specify a width when enabling scrolling" and turns it
        # straight back off. Eliding is the whole point of this subclass, so
        # settle it here rather than leave that warning on every reload.
        self.scroll = False
        # The two halves of what could be on the bar, kept apart so either can
        # change without the other having to be recomputed.
        self._local_text = ""
        self._remote_text = ""
        self._remote: SpotifyWeb | None = None
        self._remote_timer: asyncio.TimerHandle | None = None

    def get_track_info(self, metadata):
        # Called for the values it leaves in self.metadata - the raw strings,
        # already unwrapped out of their dbus variants - rather than for the
        # escaped line it returns, which is rebuilt from those below.
        widget.Mpris2.get_track_info(self, metadata)
        line = self._plain_formatter.format(self.format, **self.metadata)
        return pangocffi.markup_escape_text(
            _elide(line.replace("\n", ""), self.max_track_chars)
        )

    # ─── choosing between the local player and the account ────────────────

    def update(self, text):
        """Take `text` as the local player's line and redraw.

        Every path in Mpris2 that changes the text - a property signal, the
        background poll, the player dropping off the bus - lands here, which
        makes this the one place to capture the local half without having to
        touch the parent's logic.
        """
        self._local_text = text
        base._TextBox.update(self, self._display_text())

    def _display_text(self):
        """Which source gets the bar: whichever one is actually playing.

        Not simply "local if there is one". The desktop client stays on the bus
        when you start playing from the phone - paused, still holding the last
        track it played - and preferring it there would leave the bar naming a
        song that stopped an hour ago.
        """
        if self._local_text and self.is_playing:
            return self._local_text
        return self._remote_text or self._local_text

    # ─── remote playback ──────────────────────────────────────────────────

    async def _config_async(self):
        await widget.Mpris2._config_async(self)
        if self.remote_playing_text is None:
            return
        self._remote = SpotifyWeb()
        self._poll_remote()

    def _poll_remote(self):
        if self.finalized:
            return
        create_task(self._check_remote())

    async def _check_remote(self):
        """Ask the account what it is playing, then book the next poll.

        The reschedule sits in a finally: a poll that raises still has to book
        its successor, or one bad response ends the fallback for the session.
        """
        try:
            loop = asyncio.get_running_loop()
            # now_playing blocks on the network, so it goes to a thread - on
            # the event loop a slow reply would stall every widget on the bar.
            track = await loop.run_in_executor(None, self._remote.now_playing)
            self._remote_text = self._remote_line(track)
            base._TextBox.update(self, self._display_text())
        finally:
            if not self.finalized:
                self._remote_timer = self.timeout_add(
                    self.remote_poll_interval, self._poll_remote
                )

    def _remote_line(self, track):
        """`track` as bar text, or "" if it is not the thing to show."""
        if track is None or not track.title:
            return ""
        # Anything playing on this machine is MPRIS's to report: same track,
        # and it gets there a poll sooner.
        if track.is_local:
            return ""
        template = (
            self.remote_playing_text if track.is_playing else self.remote_paused_text
        )
        if not template:
            return ""
        # Run through the configured format, so a remote track is laid out
        # exactly like a local one - same fields, same order, same eliding.
        line = self._plain_formatter.format(
            self.format,
            **{
                "xesam:title": track.title,
                "xesam:artist": track.artist,
                "qtile:player": track.device,
            },
        )
        return template.format(
            track=pangocffi.markup_escape_text(
                _elide(line.replace("\n", ""), self.max_track_chars)
            ),
            device=pangocffi.markup_escape_text(track.device),
            device_glyph=self.remote_device_glyphs.get(track.device_type)
            or self.remote_device_glyphs.get("default", ""),
        )

    @expose_command()
    def info(self):
        """Mpris2's info, plus which of the two sources is on the bar.

        The inherited fields describe the local player alone, so both of them
        read as "nothing playing" while the bar is showing a track from the
        phone - true, but not what someone querying this wants to know.
        """
        d = widget.Mpris2.info(self)
        text = self._display_text()
        d.update(
            remote_text=self._remote_text,
            source="local"
            if text and text == self._local_text
            else "remote"
            if text
            else "none",
        )
        return d

    def finalize(self):
        if self._remote_timer is not None:
            self._remote_timer.cancel()
        widget.Mpris2.finalize(self)


def _elide(text, limit):
    """`text` cut to `limit` characters, with an ellipsis where it was cut."""
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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


# The errors a badly behaved item can raise on any of the dbus work below.
# AttributeError is in here for the same reason this whole section exists: an
# accessor the item's introspection never declared.
_ITEM_ERRORS = (
    AttributeError,
    DBusError,
    InterfaceNotFoundError,
    InvalidObjectPathError,
)


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


async def _remember_app_id(item):
    """Read the item's Id once and keep it on the item as .app_id.

    Id is the app's own name for itself - "spotify-client",
    "proton.vpn.app.gtk" - and the only stable handle there is on an item: the
    bus name is a unique connection name that changes with every launch, and
    the object path is whatever the app's indicator library happened to build.

    It is read here, at start, because the widget filters on it from
    available_icons, which draws and so cannot await anything.
    """
    if getattr(item, "app_id", None) is not None:
        return
    try:
        item.app_id = await item.item.get_id()
    except _ITEM_ERRORS:
        # Nothing to filter on. An empty id matches no substring, so an item
        # that will not say what it is stays visible.
        item.app_id = ""


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
    await _remember_app_id(self)
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

    defaults: ClassVar = [
        (
            "hidden_ids",
            (),
            "Substrings of an item's Id whose icon should not be drawn.",
        ),
    ]

    def __init__(self, **config):
        widget.StatusNotifier.__init__(self, **config)
        self.add_defaults(StatusNotifier.defaults)

    async def _config_async(self):
        await widget.StatusNotifier._config_async(self)
        # The host is a module-level singleton in libqtile and outlives a
        # config reload, along with every item already registered with it.
        # Those items ran their start() - and so the id read patched into it -
        # under the previous instance of this widget, or under one that never
        # asked for an id at all, so fill in whatever is missing before the
        # first draw filters on it.
        for item in host.items:
            await _remember_app_id(item)
        self.bar.draw()

    @property
    def available_icons(self):
        """The drawable items, less anything hidden_ids names.

        Every part of the stock widget - its width, its hit testing and its
        drawing - reads the icons through this one property, so filtering here
        is all it takes for an item to be gone rather than merely invisible.

        Matched on a substring of the app id rather than the whole thing: it
        has to survive an app renaming itself from "spotify" to
        "spotify-client".
        """
        return [
            item
            for item in widget.StatusNotifier.available_icons.fget(self)
            if not any(
                hidden in getattr(item, "app_id", "") for hidden in self.hidden_ids
            )
        ]

    def calculate_length(self):
        # The stock method returns a padding's worth of width for an empty
        # tray as long as *some* item is registered, which after filtering can
        # be a gap in the bar with nothing in it.
        if not self.available_icons:
            return 0
        return widget.StatusNotifier.calculate_length(self)

    def activate(self):
        # The item is read off self now rather than in the coroutine: a click
        # on another icon would move selected_item out from under it.
        if self.selected_item:
            create_task(self._activate(self.selected_item))

    async def _activate(self, item):
        if await _item_is_menu(item) and await _click_window_entry(item):
            return
        item.activate()
