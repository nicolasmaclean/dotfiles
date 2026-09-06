# ═══ imports ═══════════════════════════════════════════════════════════════
from dataclasses import dataclass


# ═══ theme ═══════════════════════════════════════════════════════════════
# Palette lifted from ebenezer's colors.default.yml.
@dataclass(frozen=True)
class Colors:
    fg_normal: str = "#e0e0e0"
    fg_urgent: str = "#ff6b6b"
    fg_blue: str = "#007acc"
    fg_light_blue: str = "#80d3ff"
    fg_yellow: str = "#ffcc00"
    fg_orange: str = "#ff9500"
    fg_grey: str = "#b0b0b0"  # was fg_purple: the memory readout icon
    fg_dim: str = "#7a7a7a"  # groups other than the current one
    fg_white: str = "#ffffff"
    # The bar body, and so the bar background. Keep it fully opaque: an alpha
    # channel here is what Systray is handed as its visual, and tray icons then
    # show the desktop through their own transparent pixels.
    bg_topbar: str = "#1e1e1e"
    # accent: popup borders
    bg_topbar_selected: str = "#2a2a2a"
    # The hovered/selected row in a popup menu. A lifted surface rather than
    # an inversion: #333 reads clearly against the #1e1e1e body (1.32:1) while
    # still carrying white text at 12.6:1 and the red of a destructive row at
    # 4.55:1. Anything lighter pushes that red under the 4.5:1 floor.
    bg_highlight: str = "#333333"
    border_focus: str = "#aa00ff"
    border_normal: str = "#4a4a4a"  # unfocused windows
    border_focus_stack: str = "#ffcc00"  # focused window of a stacked column
    border_normal_stack: str = "#5c4a00"  # unfocused stacked column


@dataclass(frozen=True)
class Fonts:
    normal: str = "0xProto Nerd Font"
    bold: str = "0xProto Nerd Font Bold"
    size: int = 14  # bar text
    icon_size: int = 16  # glyphs, which need a touch more to match the text


# Nerd Font glyphs as escapes, not literals. Codepoints below U+F900 sit in the
# BMP private-use area and get silently eaten by a lot of tooling; escapes are
# the only form that reliably survives a copy-paste or a patch.
@dataclass(frozen=True)
class Glyphs:
    brightness: str = "\U000f00e0"  # md-brightness_7, a full sun
    thermal: str = "\U000f10c2"  # thermometer
    cpu: str = "\uf4bc"  # chip
    memory: str = "\U000f0127"  # memory sticks
    power: str = "\uf011"  # power symbol (session menu)
    # --- power menu entries ---
    logout: str = "\U000f0343"
    reboot: str = "\U000f0709"
    shutdown: str = "\U000f0425"
    cancel: str = "\U000f0156"
    # --- network (nf-md-wifi_strength_*, which step 1-4 by signal) ---
    wifi_1: str = "\U000f091f"
    wifi_2: str = "\U000f0922"
    wifi_3: str = "\U000f0925"
    wifi_4: str = "\U000f0928"
    wifi_alert: str = "\U000f092b"  # radio up, nothing joined
    wifi: str = "\U000f05a9"  # radio up, in the menu's toggle row
    wifi_off: str = "\U000f05aa"  # radio down
    ethernet: str = "\U000f0200"
    no_network: str = "\U000f0319"  # md-lan_disconnect: no device at all
    lock: str = "\U000f033e"  # a secured SSID, in the network menu
    cog: str = "\U000f0493"  # "Settings..."
    check: str = "\U000f012c"  # the network you are actually on
    # --- input sources ---
    keyboard: str = "\U000f030c"


# ═══ the bar ═════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class TopBar:
    height: int = 34
    # Inset on three sides, so the bar reads as a pill floating over the
    # wallpaper rather than a band welded to the top edge. Nothing below: the
    # layout's own 4px window margin already opens that gap.
    gutter: int = 6


# ═══ tabbed columns ══════════════════════════════════════════════════════
# Defaults for TabbedColumns (tabbed_column.py). Here rather than in the layout
# so the tab strip tracks the bar's palette instead of carrying its own hex
# literals: a tab is meant to read as an extension of the bar.
@dataclass(frozen=True)
class Tabs:
    height: int = 22
    bg: str = Colors.bg_topbar  # shows through the gaps between tabs
    inactive_bg: str = Colors.bg_topbar
    active_bg: str = Colors.bg_topbar  # focused tab melts into the strip
    fg: str = Colors.fg_grey
    active_fg: str = Colors.fg_white
    font: str = Fonts.bold
    fontsize: int = Fonts.size - 2  # a step down from the bar text
    padding: int = 8  # horizontal, inside a tab
    spacing: int = 2  # gap between adjacent tabs


C = Colors()
F = Fonts()
G = Glyphs()
B = TopBar()
T = Tabs()
