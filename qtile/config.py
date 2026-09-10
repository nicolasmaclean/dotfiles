# qtile config — X11 backend
# Docs: https://docs.qtile.org/en/latest/
#
# Heavy inspo from williampsena's "ebenezer" theme:
# https://github.com/williampsena/dotfiles/tree/main/qtile
#
# This file is the assembly point: it wires the pieces together into the bar
# and sets the qtile-level globals. The pieces themselves live next door —
#   theme.py          palette, fonts, glyphs, tab defaults
#   hardware.py       what this box has: battery, sensor, wallpaper, screens
#   remap.py          keybindings and mouse bindings
#   tabbed_column.py  the TabbedColumns layout
#   widgets.py        custom bar widgets
#   popups.py         shared popup keymap and liveness check
#   power.py          power menu popup
#   network.py        network widget and its Wi-Fi menu
#
# The clock's calendar popup is the one bar affordance not built in here:
# it is gsimplecal, configured in this repo's gsimplecal/config.

# ═══ imports ═══════════════════════════════════════════════════════════════
import os
import subprocess

import libqtile
from libqtile import bar, hook, layout, widget
from libqtile.config import Group, Match, Screen
from libqtile.lazy import lazy

import hardware
from network import NetworkButton
from power import PowerButton, power_menu
from remap import bar_keys, group_keys, keys, mouse  # noqa: F401
from tabbed_column import EvenColumns, TabbedColumns
from theme import B, C, F, G
from widgets import (
    ColorizedCPU,
    KeyboardLayout,
    NowPlaying,
    StatusNotifier,
    VolumeIcon,
)

# ═══ groups ══════════════════════════════════════════════════════════════
groups = [Group(i) for i in "12345"]
keys += group_keys(groups)


# ═══ layouts ═════════════════════════════════════════════════════════════
# One gap, used between two windows and between a window and a screen edge.
WINDOW_GAP = 4

_COLUMN_OPTS = {
    # Two columns, and no more: past that, TabbedColumns stacks the new window
    # into the current column instead of splitting it.
    "num_columns": 2,
    "border_focus": C.border_focus,
    "border_normal": C.border_normal,
    "border_focus_stack": C.border_focus_stack,
    "border_normal_stack": C.border_normal_stack,
    "border_width": 2,
    # Half of WINDOW_GAP: both layouts are EvenColumns, which turns a
    # half-gap margin into one gap between any two windows and the same gap
    # between a window and a screen edge.
    "margin": WINDOW_GAP // 2,
}

layouts = [
    # Tab styling comes from theme.py (Tabs); pass tab_* here to override it.
    TabbedColumns(**_COLUMN_OPTS),
    # Plain columns kept as a fallback: mod+Tab reaches a known-good layout if
    # the tab strips ever misbehave.
    EvenColumns(**_COLUMN_OPTS),
    layout.Max(),
]

# Layouts that mean "this window and nothing else" - the bar hides for these.
# Matched on Layout.name, which is the class name lowercased.
_BARLESS_LAYOUTS = {"max"}

floating_layout = layout.Floating(
    border_focus=C.border_focus,
    border_normal=C.border_normal,
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),
        Match(wm_class="makebranch"),
        Match(wm_class="maketag"),
        Match(wm_class="ssh-askpass"),
        # Flameshot's overlay is a normal window, and tiled it covers one
        # monitor and shows the desktop *underneath* the bar rather than the
        # frozen screen. Floating it is the documented fix for tiling WMs.
        Match(wm_class="flameshot"),
        # The clock's calendar popup. mainwindow_resizable=0 already pins
        # min == max size hints, which is usually enough to get a window
        # floated, but naming it here means the popup cannot end up tiled
        # into a column by a stray hint change.
        Match(wm_class="gsimplecal"),
        Match(title="branchdialog"),
        Match(title="pinentry"),
    ],
)


widget_defaults = {"font": F.bold, "fontsize": F.size, "padding": 3}
extension_defaults = widget_defaults.copy()


# ═══ taskbar ═════════════════════════════════════════════════════════════════
# One flat bar, one background. Everything sits straight on the body and the
# grouping is done with rules alone —
#   Left    thermal, CPU  |  now playing
#   Centre  clock
#   Right   the two trays, volume, network, input source
#             |  group numbers  |  battery, power
#
# The bar is a pill: bar.Bar's own margin insets the *window* by B.gutter on
# three sides, so the gutter is simply not part of the bar and the wallpaper
# there needs no transparency to show. The background stays fully opaque, and
# deliberately: a bar with an alpha channel is handed to Systray as a 32-bit
# visual, and X copies a child window's pixels into its parent rather than
# blending them, so every transparent pixel in a tray icon would punch a hole
# straight through to the desktop. The ends are square — the body just stops,
# and _pill_end is only the padding that keeps the outermost widget off it.
#
# Widgets set no background of their own: with none, each one draws over the
# bar's own C.bg_topbar, so there is exactly one place the colour is set.
def _bar_text(**kwargs):
    """Shared styling for every widget on the bar."""
    return dict(
        font=F.normal,
        fontsize=F.icon_size,
        foreground=C.fg_normal,
        **kwargs,
    )


def _bar_icon(glyph, color):
    """An accent-coloured icon, paired with the readout after it."""
    return widget.TextBox(f"{glyph} ", **{**_bar_text(padding=2), "foreground": color})


def _sep():
    """The rule that does all the grouping now that no widget has a band.

    Dim grey and short of full height: it has to read against the #1e1e1e
    body without turning into a hard division.
    """
    return widget.Sep(foreground=C.fg_dim, padding=24, linewidth=1, size_percent=55)


def _pill_end():
    """A square end of the pill — a little room off the vertical edge.

    Nothing but padding: the corner is square because the body simply stops,
    so this only keeps the first/last widget off the edge.
    """
    return widget.Spacer(length=6)


# ═══ the two hardware-dependent groups ════════════════════════════════════
# Both return a *list* - empty on a machine lacking the hardware - so the entry
# can be splatted into the bar literal without the literal growing a
# conditional. Both also return their neighbouring decoration along with the
# widget, because half a group left behind reads as a broken widget rather
# than as an absent one.
def _thermal_widgets():
    """The thermometer and its readout, or nothing at all.

    tag_sensor comes from hardware.py, which picks a label that is unique
    across chips and belongs to a known CPU-package driver. None means nothing
    qualified, and omitting the widget is much better than showing it: an
    unmatched tag makes ThermalSensor read "N/A" forever with no error logged
    anywhere - which is exactly what the old hardcoded "Package id 0" would do
    on an AMD desktop.
    """
    if hardware.THERMAL is None:
        return []
    return [
        _bar_icon(G.thermal, C.fg_light_blue),
        widget.ThermalSensor(
            **_bar_text(padding=2),
            tag_sensor=hardware.THERMAL,
            format="{temp:.0f}{unit} ",
            # A taste value rather than a hardware one, and right for both
            # Intel (Tj 100) and Zen (Tctl 95) - so it is not detected.
            threshold=75,
            foreground_alert=C.fg_orange,
        ),
    ]


def _battery_widgets():
    """The separator and the battery, or nothing at all.

    The _sep() comes with it deliberately. Battery and power sit at the right
    end of the bar, so this is the rule immediately before widget.Battery, and
    a bare [] on a batteryless desktop would leave it hanging against
    PowerButton with nothing on its left.

    battery= is always passed explicitly rather than left to qtile's own
    autodetect, which walks /sys/class/power_supply in raw listdir order and
    can settle on the MX Master's hidpp_battery_N - reporting capacity but no
    energy_now, so the widget renders a permanent "Unable to read status for
    energy_now_file". hardware.battery_name() encodes why that happens.
    """
    if hardware.BATTERY is None:
        return []
    return [
        _sep(),
        widget.Battery(
            **_bar_text(padding=5),
            battery=hardware.BATTERY,
            format="{char} {percent:2.0%}",
            charge_char="\uf1e6",  # plug
            discharge_char="\uf241",  # battery draining
            empty_char="\uf244",
            full_char="\uf240",
            not_charging_char="\U000f06a6",
            unknown_char="\U000f06c4",
            low_percentage=0.15,
            low_foreground=C.fg_urgent,
        ),
    ]


def _tray_widgets():
    """The two trays. Screen 0 only - see _bar_for."""
    return [
        # Two tray protocols, two widgets: Systray speaks XEmbed, StatusNotifier
        # speaks StatusNotifierItem/AppIndicator. Apps pick one or the other, so
        # dropping either loses its icons. StatusNotifier needs dbus-fast, and
        # pyxdg for items that publish an icon name instead of a pixmap.
        widget.Systray(**_bar_text(padding=4)),  # Discord etc. dock here
        # widgets.StatusNotifier, not the stock one: Proton VPN introspects its
        # item without any properties, which the stock widget cannot read an icon
        # from. See the tray section of widgets.py.
        StatusNotifier(
            **_bar_text(padding=4),
            icon_size=20,  # Proton VPN etc.
            # Spotify's indicator is redundant now that the bar has a now-playing
            # widget of its own, and its only other trick - click to raise the
            # window - is what the taskbar entry is for. Matched on the item's own
            # Id; `busctl --user get-property <service> <path> \
            # org.kde.StatusNotifierItem Id` reads it off any other item.
            hidden_ids=("spotify",),
        ),
    ]


# ═══ the widgets every bar shares ═════════════════════════════════════════
# Built once here and handed to every bar. qtile wraps a re-used widget in a
# widget.base.Mirror, which paints the original's pixels and forwards clicks
# and scrolls back to it - so one nmcli poll, one wpctl poll and one Spotify
# request feed every monitor and the readouts cannot drift apart. On a
# three-monitor desktop the alternative is 3x the polling and 3x the Spotify
# Web API traffic against a rolling rate limit.
#
# Everything NOT here is built fresh per screen by _bar_for, and two of them
# have to be:
#   GroupBox   a mirror is a pixel copy, so a shared one would paint screen
#              0's this_current_screen_border on every monitor and no bar
#              would show which screen you are actually on.
#   Systray    an XEmbed host owning _NET_SYSTEM_TRAY_S0. It cannot be
#              mirrored at all - create_mirror() returns a fresh Systray()
#              whose _configure then raises ConfigError.
# The rest - spacers, rules, static icons, PowerButton - are too cheap to be
# worth sharing, and a STRETCH spacer is bar-width-dependent besides.
_THERMAL_WIDGETS = _thermal_widgets()
_BATTERY_WIDGETS = _battery_widgets()

# Padded to the width of "100.0%" so the readout is a fixed six cells from
# single digits to full load, and nothing to the right of it moves as the load
# climbs and falls. ColorizedCPU only recolours it.
#
# No trailing space, unlike the sensor above: the readout ends at the "%" and
# the gap before the next widget is the spacer, not padding baked into the
# text.
_CPU = ColorizedCPU(**_bar_text(padding=2), format="{load_percent:5.1f}%")

# Now playing, read off Spotify's MPRIS interface over dbus.
#
# objname pins it to Spotify, and that pin is what makes a track show up after
# a qtile restart: without it the widget only learns of a player when that
# player next broadcasts a change, so something already playing would leave the
# bar blank until the track ended. Drop objname to follow every MPRIS player on
# the box - browsers, mpv - and give that up.
#
# The glyph lives in the state text rather than in a _bar_icon() beside it, for
# the same reason as the spacer before it: it has to disappear along with the
# track. Markup is safe in these two - the track text is escaped before it is
# substituted in - and NowPlaying elides rather than scrolls, so the glyph
# stays put at the left of the widget however long the title runs.
_NOW_PLAYING = NowPlaying(
    **_bar_text(padding=2),
    name="spotify",
    objname="org.mpris.MediaPlayer2.spotify",
    format="{xesam:title} · {xesam:artist}",
    playing_text=f'<span foreground="{C.fg_green}">{G.spotify}</span> {{track}}',
    paused_text=f'<span foreground="{C.fg_dim}">{G.spotify}</span> {{track}}',
    stopped_text="",
    no_metadata_text="",
    max_track_chars=50,
    # Spotify does broadcast its changes, but not every one of them - a slow
    # poll picks up whatever the signals missed.
    poll_interval=5,
    # And when nothing is playing here at all, ask Spotify what the account is
    # playing anywhere - music started on the phone shows up on the bar without
    # the desktop client ever being opened. Needs the one-time login in
    # qtile/spotify_auth.py; without it these are simply inert.
    #
    # The device glyph goes after the Spotify mark rather than replacing it:
    # the track is still Spotify's, it is only the speaker that is somewhere
    # else. Dim, because it is a note about the track and not part of it.
    remote_playing_text=(
        f'<span foreground="{C.fg_green}">{G.spotify}</span>'
        f'<span foreground="{C.fg_dim}"> {{device_glyph}}</span> {{track}}'
    ),
    remote_paused_text=(
        f'<span foreground="{C.fg_dim}">{G.spotify} {{device_glyph}}</span> {{track}}'
    ),
    remote_device_glyphs={
        "Smartphone": G.device_phone,
        "Tablet": G.device_phone,
        "Computer": G.device_computer,
        "Speaker": G.device_speaker,
        "CastAudio": G.device_cast,
        "CastVideo": G.device_cast,
        "default": G.device_speaker,
    },
    remote_poll_interval=10,
)

_CLOCK = widget.Clock(
    format="%b %d, %I:%M:%S %p",
    font=F.normal,
    fontsize=F.icon_size,
    foreground=C.fg_normal,
    padding=2,
    # Click for a month calendar, scroll to page through months.
    #
    # gsimplecal rather than a popup built here: it toggles itself, so the one
    # spawn both opens and closes it, and prev_month/next_month start it if it
    # is not already up - which is what makes a scroll on the clock open the
    # calendar already moved by a month. It places itself centred on the
    # pointer, so it lands under the clock you clicked - on the monitor you
    # clicked it on, since GTK clamps the window into that monitor before
    # applying the offset. The repo's gsimplecal/config carries the offsets
    # that lift it clear of the bar, and everything else about how it looks.
    mouse_callbacks={
        "Button1": lazy.spawn("gsimplecal"),
        "Button4": lazy.spawn("gsimplecal prev_month"),
        "Button5": lazy.spawn("gsimplecal next_month"),
    },
)

_VOLUME = VolumeIcon(
    **_bar_text(padding=5),
    # VolumeIcon would otherwise be addressed as "volumeicon", and remap.py's
    # XF86Audio* keys look the widget up as "volume".
    name="volume",
    emoji=True,
    emoji_list=["\U000f075f", "\U000f057f", "\U000f0580", "\U000f057e"],
    # this box is PipeWire. amixer does work via pipewire-alsa (Master tracks
    # the real sink), but wpctl talks to it directly rather than through the
    # compatibility shim.
    get_volume_command="wpctl get-volume @DEFAULT_AUDIO_SINK@ "
    "| awk '{printf \"%d%%\", $2*100}'",
    check_mute_command="wpctl get-volume @DEFAULT_AUDIO_SINK@",
    check_mute_string="[MUTED]",
    volume_up_command="wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+",
    volume_down_command="wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-",
    mute_command="wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
    step=5,
    # Mouse handling is left to the widget itself: Button1 mutes and scroll
    # nudges the volume. Button3 runs volume_app, which is unset - there is no
    # mixer installed for it to open anyway.
)

_NETWORK = NetworkButton(
    **_bar_text(padding=5),
    # network.py's popup finds the widget under this name to anchor itself -
    # on the current screen's own bar, matching through .reflects so the mirror
    # on a second monitor anchors under itself. See popups.bar_widget.
    name="network",
    update_interval=5,
    # Glyph only. show_name=True adds the SSID next to it.
)

# App icons first, then the two things this config draws itself. Both used to
# be foreign tray icons - ibus's GTK panel and nm-applet - and both are native
# widgets now, so they sit outside the trays and follow the palette in theme.py
# like everything else on the bar.
_KEYBOARD = KeyboardLayout(
    **_bar_text(padding=5),
    # remap.py's mod+shift+space drives this widget by name.
    name="keyboard",
    # (ibus engine id, label), in cycle order. `ibus list-engine` lists all 983
    # of them; the Chinese IMEs installed on this box are libpinyin (pinyin),
    # chewing (zhuyin) and the ibus-table engines (cangjie, wubi).
    #
    # Note that "cn" is deliberately not here. GNOME's input-sources list on
    # this box still reads [('xkb','us'), ('xkb','cn')], but ibus registers no
    # xkb:cn engine at all, so that entry was never selectable - see the README
    # note. libpinyin is the working Chinese input method.
    engines=[("xkb:us::eng", "US"), ("libpinyin", "CN")],
    # Nothing polls usefully here: the widget re-reads on its own switch, and
    # this only catches a switch made behind its back.
    update_interval=30,
)


def _bar_for(index):
    """Every widget on screen `index`'s bar, in order.

    A function rather than the flat list it used to be, because the desktop has
    more than one screen and each needs its own GroupBox, its own PowerButton
    to anchor the power menu under, and the trays on exactly one of them. The
    order is the one the header describes:
      Left    thermal, CPU  |  now playing
      Centre  clock
      Right   the two trays, volume, network, input source
                |  group numbers  |  battery, power
    """
    return [
        _pill_end(),
        *_THERMAL_WIDGETS,
        _bar_icon(G.cpu, C.fg_yellow),
        _CPU,
        # Plain space rather than a _sep(): the widget after it draws nothing at
        # all when Spotify is closed or stopped, and a rule left hanging beside
        # an empty stretch of bar reads worse than no rule.
        widget.Spacer(length=10),
        _NOW_PLAYING,
        widget.Spacer(length=bar.STRETCH),
        _CLOCK,
        widget.Spacer(length=bar.STRETCH),
        # Trays on screen 0 and nowhere else. Systray *cannot* be anywhere else
        # - one XEmbed host per X display - and StatusNotifier is D-Bus and
        # could be mirrored, but the same icons repeated on every monitor are
        # noise. Keeping the pair on index 0 also pins them to the one Screen
        # that is never finalized while any output at all is plugged in.
        *(_tray_widgets() if index == 0 else []),
        _VOLUME,
        _NETWORK,
        _KEYBOARD,
        # Divides all of that from the group numbers.
        _sep(),
        # Fresh per screen, and it has to be - see the sharing note above.
        widget.GroupBox(
            margin_y=3,
            margin_x=3,
            padding=1,
            borderwidth=0,
            font=F.normal,
            fontsize=F.icon_size,
            active=C.fg_dim,
            inactive=C.fg_dim,
            foreground=C.fg_dim,
            this_current_screen_border=C.fg_white,
            this_screen_border=C.fg_blue,
            other_current_screen_border=C.fg_white,
            highlight_color=C.fg_white,
            highlight_method="text",
            rounded=False,
            urgent_alert_method="border",
            urgent_border=C.fg_urgent,
        ),
        *_BATTERY_WIDGETS,
        # Fresh per screen so each bar has its own to anchor the power menu
        # under. They all register as "powerbutton" and qtile renames the
        # duplicates in widgets_map, which is why popups.bar_widget searches
        # this screen's bar instead of that map.
        PowerButton(
            G.power,
            **_bar_text(padding=8),
            mouse_callbacks={"Button1": power_menu},
        ),
        _pill_end(),
    ]


# ═══ desktop ══════════════════════════════════════════════════════════════
# No `screens` list at all any more. generate_screens replaces it: qtile calls
# it with the real output list at startup *and* on every hotplug, so the
# laptop's one panel and the desktop's several are the same config and plugging
# a monitor in mid-session grows a bar onto it. Defining both would only earn a
# warning - get_screens_from_config uses generate_screens and ignores screens.
def _screen_for(index, rect=None):
    """One screen's worth of desktop: a wallpaper and a bar.

    `rect` is passed only on the fake-screens path, where the geometry is
    invented. On the real path qtile fills it in from the output itself.
    """
    x, y, width, height = rect or (None, None, None, None)
    return Screen(
        # hardware.py looks in the repo first, so a fresh clone has one before
        # anything has been downloaded. None is a real answer and is handled
        # rather than papered over: Painter.paint catches the OSError from a
        # missing file and logs a full traceback per screen on every
        # reconfigure, where None paints nothing and logs nothing. The bar
        # colour stands in for it so an unwallpapered box gets the palette
        # rather than X's grey stipple.
        wallpaper=hardware.WALLPAPER,
        wallpaper_mode="fill" if hardware.WALLPAPER else None,
        background=None if hardware.WALLPAPER else C.bg_topbar,
        # margin is [N E S W]: the gutter on three sides, nothing below.
        top=bar.Bar(
            _bar_for(index),
            B.height,
            background=C.bg_topbar,
            margin=[B.gutter, B.gutter, 0, B.gutter],
        ),
        x=x,
        y=y,
        width=width,
        height=height,
    )


if hardware.FAKE_OUTPUTS:
    # QTILE_FAKE_OUTPUTS=N carves the one real panel into N side-by-side
    # screens. This is the only lever that fabricates geometry, and it is the
    # right one: get_screens_from_config checks fake_screens *before*
    # generate_screens, so the bar builder under test is the real one and only
    # the outputs are invented. Xephyr's +xinerama is not a substitute -
    # _process_screens takes its geometry from the real output list, so extra
    # Screens there simply go unused.
    fake_screens = [
        _screen_for(i, rect)
        for i, rect in enumerate(hardware.fake_rects(hardware.FAKE_OUTPUTS))
    ]
else:
    # The wrapper caches Screen objects by index and re-hands the same ones on
    # a hotplug. That is not an optimisation: rebuilding them leaks a bar
    # window and silently drops the systray on every replug, because
    # Screen.__eq__ compares by output identity and qtile therefore never
    # finalizes the old one. The long version is in hardware.screen_generator.
    generate_screens = hardware.screen_generator(
        lambda index, output: _screen_for(index)
    )

# ═══ global settings ═════════════════════════════════════════════════════════════════
dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False

auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True
wl_input_rules = None
wl_xcursor_theme = None
wl_xcursor_size = 24

# Java compatibility; harmless otherwise.
wmname = "LG3D"


# QTILE_NESTED is set by bin/qtile-nested. A nested instance shares the one
# `systemd --user` manager with the session you started it from, so without
# this guard testing the config in Xephyr would start the *real* session's
# target on the way in and - much worse - stop it on the way out, killing the
# picom, dunst, flameshot, polkit and VPN services out from under the desktop
# you are sitting at. The nested instance simply does without them.
_NESTED = bool(os.environ.get("QTILE_NESTED"))


@hook.subscribe.startup_once
def _start_systemd_session():
    """Hand session lifetime to systemd --user (see qtile-session.target)."""
    if _NESTED:
        return
    subprocess.run(
        ["systemctl", "--user", "start", "qtile-session.target"], check=False
    )


@hook.subscribe.shutdown
def _stop_systemd_session():
    if _NESTED:
        return
    subprocess.run(["systemctl", "--user", "stop", "qtile-session.target"], check=False)


# ═══ bar visibility ══════════════════════════════════════════════════════════
# Max is the stop on mod+Tab you reach for when you want the window and nothing
# else, and the bar is the last thing in the way: qtile reserves its strip out
# of the screen's usable area, so a Max window stops short of the top edge.
# Hiding the bar hands that strip back to the layout and Max fills the screen.
#
# Two hooks, because the current layout changes two ways - mod+Tab cycles it
# (layout_change) and switching group swaps in whatever layout that group was
# left on (setgroup). setgroup is passed nothing, so both go through the same
# walk over the screens rather than being handed the one that changed.
#
# mod+d sets _bar_override to True or False and it wins from then on; None means
# "no opinion, follow the layout". It has to be state out here rather than
# something recomputed per press, because these same two hooks are what would
# otherwise undo the toggle on the next mod+Tab or group switch.
#
# A config reload drops it: qtile re-executes this file, so the None comes back
# and the bar returns to whatever the layout wants. Not worth working around -
# the reload builds a fresh Bar too, so there is no state to carry over anyway.
_bar_override = None


def _sync_bar_to_layout():
    for scr in getattr(libqtile.qtile, "screens", ()):
        top = scr.top
        # A Gap has no show(), and a Bar has no .window until _configure has
        # run - calling show() before that zeroes the reserved size out from
        # under the first layout pass.
        if not isinstance(top, bar.Bar) or getattr(top, "window", None) is None:
            continue
        if scr.group is None:
            continue
        if _bar_override is not None:
            top.show(_bar_override)
            continue
        top.show(scr.group.layout.name not in _BARLESS_LAYOUTS)


@hook.subscribe.layout_change
def _bar_follows_layout(new_layout, group):
    _sync_bar_to_layout()


@hook.subscribe.setgroup
def _bar_follows_group():
    _sync_bar_to_layout()


# Which way to toggle is read off the bar rather than off _bar_override: on the
# first press the override has no opinion yet, and on Max the bar is already
# hidden - inverting the override there would ask for a hide you cannot see.
def _toggle_bar(qtile):
    global _bar_override
    top = qtile.current_screen.top
    if not isinstance(top, bar.Bar):
        return
    _bar_override = not top.is_show()
    _sync_bar_to_layout()


# Down here rather than up with the other keys, because bar_keys needs the
# toggle and the toggle needs _sync_bar_to_layout.
keys += bar_keys(_toggle_bar)


# ═══ calendar popup ══════════════════════════════════════════════════════════
# The clock spawns gsimplecal (see the widget above), configured to sit just
# under the bar - which is also the band TabbedColumns draws its tab strip in.
# A tab strip is an Internal window, and those stack above ordinary clients, so
# the strip paints over the top of the popup and swallows its month header.
#
# Raising the popup once it is managed fixes it: the strip only repaints on a
# layout change, and the popup is gone before the next one.
@hook.subscribe.client_managed
def _raise_calendar_popup(window):
    if "gsimplecal" in (window.get_wm_class() or ()):
        window.bring_to_front()
