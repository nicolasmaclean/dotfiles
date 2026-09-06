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
    bg_topbar: str = "#1e1e1e"  # bar background
    # the readouts banner on the left, and the tray band on the right
    bg_topbar_tray: str = "#333333"
    # accent: popup borders and the separator
    bg_topbar_selected: str = "#2a2a2a"
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
    arrow_size: int = 30  # the powerline triangle, sized to the bar height


# Nerd Font glyphs as escapes, not literals. Codepoints below U+F900 sit in the
# BMP private-use area and get silently eaten by a lot of tooling; escapes are
# the only form that reliably survives a copy-paste or a patch.
@dataclass(frozen=True)
class Glyphs:
    arrow: str = "\ue0b2"  # powerline left-facing triangle: opens a band
    arrow_close: str = "\ue0b0"  # right-facing: closes a band short of the edge
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
T = Tabs()
