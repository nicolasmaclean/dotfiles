# qtile config — X11 backend
# Docs: https://docs.qtile.org/en/latest/
#
# Heavy inspo from williampsena's "ebenezer" theme:
# https://github.com/williampsena/dotfiles/tree/main/qtile
#
# This file is the assembly point: it wires the pieces together into the bar
# and sets the qtile-level globals. The pieces themselves live next door —
#   theme.py          palette, fonts, glyphs, tab defaults
#   remap.py          keybindings and mouse bindings
#   tabbed_column.py  the TabbedColumns layout
#   widgets.py        custom bar widgets
#   popups.py         shared popup keymap and liveness check
#   power.py          power menu popup
#   network.py        network widget and its Wi-Fi menu

# ═══ imports ═══════════════════════════════════════════════════════════════
import subprocess

import libqtile
from libqtile import bar, hook, layout, widget
from libqtile.config import Group, Match, Screen

from network import NetworkButton
from power import PowerButton, power_menu
from remap import group_keys, keys, mouse  # noqa: F401
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


bar_widgets = [
    _pill_end(),
    _bar_icon(G.thermal, C.fg_light_blue),
    widget.ThermalSensor(
        **_bar_text(padding=2),
        tag_sensor="Package id 0",
        format="{temp:.0f}{unit} ",
        threshold=75,
        foreground_alert=C.fg_orange,
    ),
    _bar_icon(G.cpu, C.fg_yellow),
    # Padded to the width of "100.0%" so the readout is a fixed six cells from
    # single digits to full load, and nothing to the right of it moves as the
    # load climbs and falls. ColorizedCPU only recolours it.
    #
    # No trailing space, unlike the sensor above: the readout ends at the "%"
    # and the gap before the next widget is the spacer below, not padding baked
    # into the text.
    ColorizedCPU(**_bar_text(padding=2), format="{load_percent:5.1f}%"),
    # Plain space rather than a _sep(): the widget after it draws nothing at
    # all when Spotify is closed or stopped, and a rule left hanging beside an
    # empty stretch of bar reads worse than no rule.
    widget.Spacer(length=10),
    # Now playing, read off Spotify's MPRIS interface over dbus.
    #
    # objname pins it to Spotify, and that pin is what makes a track show up
    # after a qtile restart: without it the widget only learns of a player when
    # that player next broadcasts a change, so something already playing would
    # leave the bar blank until the track ended. Drop objname to follow every
    # MPRIS player on the box - browsers, mpv - and give that up.
    #
    # The glyph lives in the state text rather than in a _bar_icon() beside it,
    # for the same reason as the spacer above: it has to disappear along with
    # the track. Markup is safe in these two - the track text is escaped before
    # it is substituted in - and NowPlaying elides rather than scrolls, so the
    # glyph stays put at the left of the widget however long the title runs.
    NowPlaying(
        **_bar_text(padding=2),
        name="spotify",
        objname="org.mpris.MediaPlayer2.spotify",
        format="{xesam:title} · {xesam:artist}",
        playing_text=f'<span foreground="{C.fg_green}">{G.spotify}</span> {{track}}',
        paused_text=f'<span foreground="{C.fg_dim}">{G.spotify}</span> {{track}}',
        stopped_text="",
        no_metadata_text="",
        max_track_chars=50,
        # Spotify does broadcast its changes, but not every one of them - a
        # slow poll picks up whatever the signals missed.
        poll_interval=5,
    ),
    widget.Spacer(length=bar.STRETCH),
    widget.Clock(
        format="%b %d, %I:%M:%S %p",
        font=F.normal,
        fontsize=F.icon_size,
        foreground=C.fg_normal,
        padding=2,
    ),
    widget.Spacer(length=bar.STRETCH),
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
    VolumeIcon(
        **_bar_text(padding=5),
        # VolumeIcon would otherwise be addressed as "volumeicon", and
        # remap.py's XF86Audio* keys look the widget up as "volume".
        name="volume",
        emoji=True,
        emoji_list=["\U000f075f", "\U000f057f", "\U000f0580", "\U000f057e"],
        # this box is PipeWire. amixer does work via pipewire-alsa (Master
        # tracks the real sink), but wpctl talks to it directly rather than
        # through the compatibility shim.
        get_volume_command="wpctl get-volume @DEFAULT_AUDIO_SINK@ "
        "| awk '{printf \"%d%%\", $2*100}'",
        check_mute_command="wpctl get-volume @DEFAULT_AUDIO_SINK@",
        check_mute_string="[MUTED]",
        volume_up_command="wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+",
        volume_down_command="wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-",
        mute_command="wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
        step=5,
        # Mouse handling is left to the widget itself: Button1 mutes and scroll
        # nudges the volume. Button3 runs volume_app, which is unset - there is
        # no mixer installed for it to open anyway.
    ),
    NetworkButton(
        **_bar_text(padding=5),
        # network.py's popup finds the widget under this name to anchor itself.
        name="network",
        update_interval=5,
        # Glyph only. show_name=True adds the SSID next to it.
    ),
    # App icons first, then the two things this config draws itself. Both used
    # to be foreign tray icons - ibus's GTK panel and nm-applet - and both are
    # native widgets now, so they sit outside the trays and follow the palette
    # in theme.py like everything else on the bar.
    KeyboardLayout(
        **_bar_text(padding=5),
        # remap.py's mod+shift+space drives this widget by name.
        name="keyboard",
        # (ibus engine id, label), in cycle order. `ibus list-engine` lists all
        # 983 of them; the Chinese IMEs installed on this box are libpinyin
        # (pinyin), chewing (zhuyin) and the ibus-table engines (cangjie, wubi).
        #
        # Note that "cn" is deliberately not here. GNOME's input-sources list
        # on this box still reads [('xkb','us'), ('xkb','cn')], but ibus
        # registers no xkb:cn engine at all, so that entry was never selectable
        # - see the README note. libpinyin is the working Chinese input method.
        engines=[("xkb:us::eng", "US"), ("libpinyin", "CN")],
        # Nothing polls usefully here: the widget re-reads on its own switch,
        # and this only catches a switch made behind its back.
        update_interval=30,
    ),
    # Divides all of that from the group numbers.
    _sep(),
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
    _sep(),
    widget.Battery(
        **_bar_text(padding=5),
        # Pin the ACPI name. qtile's autodetect walks /sys/class/power_supply
        # and takes the first dir exposing a "capacity" file, which on this box
        # can be hidpp_battery_2 — the MX Master 3S. The mouse reports capacity
        # but no energy_now, so the widget dies with "Unable to read status for
        # energy_now_file" whenever the mouse sorts ahead of BAT0.
        battery="BAT0",
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
    PowerButton(
        G.power,
        **_bar_text(padding=8),
        mouse_callbacks={"Button1": power_menu},
    ),
    _pill_end(),
]

# ═══ desktop ═════════════════════════════════════════════════════════════════
screens = [
    Screen(
        wallpaper="/home/nick/.local/share/backgrounds/2025-11-27-08-48-14-puppycat_sleeping.jpg",
        wallpaper_mode="fill",
        # margin is [N E S W]: the gutter on three sides, nothing below.
        top=bar.Bar(
            bar_widgets,
            B.height,
            background=C.bg_topbar,
            margin=[B.gutter, B.gutter, 0, B.gutter],
        ),
    ),
]

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


@hook.subscribe.startup_once
def _start_systemd_session():
    """Hand session lifetime to systemd --user (see qtile-session.target)."""
    subprocess.run(
        ["systemctl", "--user", "start", "qtile-session.target"], check=False
    )


@hook.subscribe.shutdown
def _stop_systemd_session():
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
        top.show(scr.group.layout.name not in _BARLESS_LAYOUTS)


@hook.subscribe.layout_change
def _bar_follows_layout(new_layout, group):
    _sync_bar_to_layout()


@hook.subscribe.setgroup
def _bar_follows_group():
    _sync_bar_to_layout()
