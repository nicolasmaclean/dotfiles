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

# ═══ imports ═══════════════════════════════════════════════════════════════
import subprocess

from libqtile import bar, hook, layout, widget
from libqtile.config import Group, Match, Screen

from power import PowerButton, power_menu
from remap import group_keys, keys, mouse  # noqa: F401
from tabbed_column import TabbedColumns
from theme import C, F, G
from widgets import BrightnessBar, ColorizedCPU, ColorizedMemory, VolumeBar

# ═══ groups ══════════════════════════════════════════════════════════════
groups = [Group(i) for i in "12345"]
keys += group_keys(groups)


# ═══ layouts ═════════════════════════════════════════════════════════════
_COLUMN_OPTS = {
    # Two columns, and no more: past that, TabbedColumns stacks the new window
    # into the current column instead of splitting it.
    "num_columns": 2,
    "border_focus": C.border_focus,
    "border_normal": C.border_normal,
    "border_focus_stack": C.border_focus_stack,
    "border_normal_stack": C.border_normal_stack,
    "border_width": 2,
    "margin": 4,
}

layouts = [
    # Tab styling comes from theme.py (Tabs); pass tab_* here to override it.
    TabbedColumns(**_COLUMN_OPTS),
    # Plain Columns kept as a fallback: mod+Tab reaches a known-good layout if
    # the tab strips ever misbehave.
    layout.Columns(**_COLUMN_OPTS),
    layout.Max(),
]

floating_layout = layout.Floating(
    border_focus=C.border_focus,
    border_normal=C.border_normal,
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),
        Match(wm_class="makebranch"),
        Match(wm_class="maketag"),
        Match(wm_class="ssh-askpass"),
        Match(title="branchdialog"),
        Match(title="pinentry"),
    ],
)


widget_defaults = {"font": F.bold, "fontsize": F.size, "padding": 3}
extension_defaults = widget_defaults.copy()


# ═══ taskbar ═════════════════════════════════════════════════════════════════
# Left: groups, then the thermal / CPU / memory readouts. Centre: clock.
# Right: two bands running out to the screen edge —
#   bg_topbar_tray        the two trays
#   bg_topbar (unbanded)  brightness, volume, battery, then the power button
#
# None of this is a real powerline — a band is an oversized arrow glyph drawn
# over whatever background precedes it, followed by ordinary widgets that all
# share that background. The two right-hand bands run to the edge and open with
# a G.arrow point; the readouts sit mid-bar and instead read as a right-pointing
# banner, G.arrow_close at both ends: the opening one is drawn in the *bar*
# colour over the slab, so it cuts a chevron in rather than sticking a point out.
def _slab(bg, **kwargs):
    """Shared styling for everything sitting on the slab coloured `bg`."""
    return dict(
        font=F.normal,
        fontsize=F.icon_size,
        background=bg,
        foreground=C.fg_normal,
        **kwargs,
    )


def _slab_icon(glyph, color, bg):
    """An accent-coloured icon on a slab, paired with the readout after it."""
    return widget.TextBox(f"{glyph} ", **{**_slab(bg, padding=2), "foreground": color})


def _slab_arrow(bg, over=None, glyph=G.arrow):
    """A `bg` triangle capping a band. `over` is the background behind it."""
    return widget.TextBox(
        glyph,
        font=F.normal,
        fontsize=F.arrow_size,
        foreground=bg,
        background=over,
        padding=0,
    )


bar_widgets = [
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
    # Divides the groups from the readouts. The band colours are all but
    # invisible against the #1e1e1e bar, so this uses the accent instead.
    widget.Sep(
        foreground=C.bg_topbar_selected, padding=24, linewidth=1, size_percent=55
    ),
    # ── the readouts banner: a band that closes again, not one that runs to
    # the edge, so it is capped at both ends — both pointing right ──
    _slab_arrow(C.bg_topbar, over=C.bg_topbar_tray, glyph=G.arrow_close),
    _slab_icon(G.thermal, C.fg_light_blue, C.bg_topbar_tray),
    widget.ThermalSensor(
        **_slab(C.bg_topbar_tray, padding=2),
        tag_sensor="Package id 0",
        format="{temp:.0f}{unit} ",
        threshold=75,
        foreground_alert=C.fg_orange,
    ),
    _slab_icon(G.cpu, C.fg_yellow, C.bg_topbar_tray),
    ColorizedCPU(**_slab(C.bg_topbar_tray, padding=2), format="{load_percent}% "),
    _slab_icon(G.memory, C.fg_grey, C.bg_topbar_tray),
    ColorizedMemory(**_slab(C.bg_topbar_tray, padding=2), format="{MemUsed:.0f}{mm} "),
    _slab_arrow(C.bg_topbar_tray, glyph=G.arrow_close),
    widget.Spacer(length=bar.STRETCH),
    widget.Clock(
        format="%b %d, %I:%M %p",
        font=F.normal,
        fontsize=F.icon_size,
        foreground=C.fg_normal,
        padding=2,
    ),
    widget.Spacer(length=bar.STRETCH),
    # ── first slab: the trays ──
    _slab_arrow(C.bg_topbar_tray),
    # Two tray protocols, two widgets: Systray speaks XEmbed, StatusNotifier
    # speaks StatusNotifierItem/AppIndicator. Apps pick one or the other, so
    # dropping either loses its icons. StatusNotifier needs dbus-fast, and
    # pyxdg for items that publish an icon name instead of a pixmap.
    widget.Systray(**_slab(C.bg_topbar_tray, padding=4)),  # nm-applet etc. dock here
    widget.StatusNotifier(
        **_slab(C.bg_topbar_tray, padding=4), icon_size=20
    ),  # Proton VPN etc.
    # ── dark slab: the two meters, battery and power, out to the edge ──
    _slab_arrow(C.bg_topbar, over=C.bg_topbar_tray),
    BrightnessBar(
        **_slab(C.bg_topbar, padding=5),
        # remap.py's XF86MonBrightness keys drive this widget by name, so they
        # and a scroll over it step the backlight identically.
        name="brightness",
        segments=5,
        # A floor, because nothing below it has one: brightnessctl clamps
        # neither its relative nor its absolute form, and the curve collapses
        # anything under ~7% to a raw 0 - a black panel with no way back except
        # the keys you cannot see to find. 10% of the curve is the dimmest the
        # panel still lights at.
        min_brightness=10,
    ),
    VolumeBar(
        **_slab(C.bg_topbar, padding=5),
        # VolumeBar would otherwise be addressed as "volumebar", and remap.py's
        # XF86Audio* keys look the widget up as "volume".
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
    widget.Battery(
        **_slab(C.bg_topbar, padding=5),
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
        **_slab(C.bg_topbar, padding=8),
        mouse_callbacks={"Button1": power_menu},
    ),
    # tail of the slab: without the background it reverts to the bar colour
    # and leaves a gap between the power button and the screen edge
    widget.Spacer(length=5, background=C.bg_topbar),
]

# ═══ desktop ═════════════════════════════════════════════════════════════════
screens = [
    Screen(
        wallpaper="/home/nick/.local/share/backgrounds/2025-11-27-08-48-14-puppycat_sleeping.jpg",
        wallpaper_mode="fill",
        top=bar.Bar(bar_widgets, 34, background=C.bg_topbar),
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
