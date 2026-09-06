# ═══ imports ══════════════════════════════════════════════════════════════
from libqtile import hook, widget
from libqtile.widget import base

from theme import C, G

# ═══ custom widgets ══════════════════════════════════════════════════════
# Stock qtile has no threshold colouring on CPU/Memory, no glyph-based layout
# indicator, and no icon substitution in TaskList. These three fill those gaps.


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


class ColorizedMemory(_Thresholded, widget.Memory):
    def __init__(self, threshold_medium=65, threshold_high=85, **config):
        self.threshold_medium = threshold_medium
        self.threshold_high = threshold_high
        widget.Memory.__init__(self, **config)

    def poll(self):
        import psutil

        text = widget.Memory.poll(self)
        return self._colorize(psutil.virtual_memory().percent, text)


# ═══ meters ═══════════════════════════════════════════════════════════════
# After rodrigokimura/qtile-config: instead of a glyph or a bare percentage, a
# reading is drawn inline as a run of block characters, so it reads at a glance
# without opening anything.
#
# Both halves of the meter are U+2588 FULL BLOCK and the empty one is dimmed
# with markup, rather than the usual U+2593 DARK SHADE. The shade characters
# are dither patterns - a grid of dots is what the glyph *is*, in every font -
# so they read as texture next to the solid run. One character for both halves
# also keeps the meter exactly as wide at 0% as at 100%.


class _BlockMeter:
    """Draws a 0-100 reading as a run of blocks: ██████████

    A mixin rather than a widget, so it can sit on top of whichever stock
    widget already knows how to read the value being metered.
    """

    def _init_meter(self, config):
        """Take the meter's own options out of a widget's **config."""
        self.segments = config.pop("segments", 10)
        self.block = config.pop("block", "\u2588")
        self.empty_foreground = config.pop("empty_foreground", C.fg_dim)

    def _meter(self, percent):
        filled = min(self.segments, max(0, round(percent * self.segments / 100)))
        meter = self.block * filled
        if filled < self.segments:
            # markup, not a second widget: the whole meter has to stay one
            # string so it draws as an unbroken run of cells
            meter += (
                f'<span foreground="{self.empty_foreground}">'
                f"{self.block * (self.segments - filled)}</span>"
            )
        return meter


class VolumeBar(_BlockMeter, widget.Volume):
    """Volume as a block meter, the empty run dimmed: 󰕾 ██████████

    No percentage: the meter carries the level, and dropping the readout also
    makes the widget one fixed width, so nothing to its left shifts as the
    volume changes.

    The stock widget's own text is kept as the leading icon - with emoji=True
    that is the speaker glyph, which shows mute. Mute reads as zero here rather
    than as the level waiting behind it, so the meter agrees with the icon.
    """

    def __init__(self, **config):
        self._init_meter(config)
        widget.Volume.__init__(self, **config)

    def _update_drawer(self):
        # sets self.text to the icon and recolours for mute
        widget.Volume._update_drawer(self)
        icon = self.text if (self.emoji or self.theme_path) else ""
        # get_volume() reports -1 when the mixer command fails
        volume = 0 if self.is_mute else max(0, self.volume or 0)
        self.text = f"{icon} {self._meter(volume)}".strip()


class BrightnessBar(_BlockMeter, widget.Backlight):
    """Screen brightness on the same meter as VolumeBar: 󰃠 ██████████

    Reported on brightnessctl's -e curve rather than as the raw sysfs ratio,
    which is what remap.py's XF86MonBrightness keys move along. The two scales
    are far apart - a panel at raw 30% is 74% of the way up the curve - so a
    raw meter would sit still through several presses near the bottom and then
    leap by segments near the top.

    Everything else (scroll, min_brightness) then works in curve percent too,
    because it all goes through _get_info.
    """

    def __init__(self, icon=G.brightness, exponent=4, **config):
        self._init_meter(config)
        self.icon = icon
        self.exponent = exponent
        # the stock default drives xbacklight, which isn't installed here
        config.setdefault("change_command", "brightnessctl -e set {0:.0f}%")
        config.setdefault("step", 5)  # matches the keys in remap.py
        widget.Backlight.__init__(self, **config)

    def _get_info(self):
        """Position along the -e curve, 0.0-1.0, from the raw sysfs ratio."""
        return widget.Backlight._get_info(self) ** (1 / self.exponent)

    def poll(self):
        try:
            percent = 100 * self._get_info()
        except RuntimeError:  # backlight device went away
            percent = 0
        return f"{self.icon} {self._meter(percent)}"


# Only the two layouts actually configured above; extend if you add more.
LAYOUT_ICONS = {
    "tabbedcolumns": "\U000f0322",  # nf-md-tab
    "columns": "",
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
