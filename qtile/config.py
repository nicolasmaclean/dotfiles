# qtile config — X11 backend
# Docs: https://docs.qtile.org/en/latest/
#
# Bar styling is a port of williampsena's "ebenezer" theme:
#   https://github.com/williampsena/dotfiles/tree/main/qtile
# His version drives everything from YAML via the qtile-ebenezer PyPI package;
# this rebuilds the same look on stock qtile widgets.

from libqtile import bar, layout, qtile, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.widget import base

# qtile core has no popup toolkit; the volume slider below needs qtile-extras.
# Installed into the same env as qtile:
#   uv tool install qtile --with psutil --with qtile-extras
# Its version tracks qtile's exactly (0.37.0 <-> 0.37.0) — upgrade them together.
from qtile_extras.popup.toolkit import (
    PopupAbsoluteLayout,
    PopupRelativeLayout,
    PopupSlider,
    PopupText,
)

import subprocess
import time

from libqtile.backend.base import window as backend_window
from functools import partial

mod = "mod1"  # Alt: keyboard modifier for every Key() binding
# Super stays on the mouse so Alt+drag keeps working inside 3D viewports
# (usdview, Blender) and other apps that use the Maya camera convention.
mod_mouse = "mod4"  # Super / Windows key
terminal = "alacritty"  # only terminal installed on this box
launcher = "rofi -show drun"  # app search; styled in ~/.config/rofi/config.rasi
runner = "rofi -show run"  # arbitrary command, no .desktop entry needed


# ═══ launch-into-stack ═══════════════════════════════════════════════════
# Columns decides where a new window goes when the client is managed: while
# fewer than num_columns exist it opens a *new* column, and after that it
# splits the current one. Neither puts the new window on top of the focused
# one. So the keybinding can only record the intent -- the hook below, which
# fires once the layout has already placed the client, does the actual move.
_stack_next = None  # (group name, window to stack onto, time.monotonic())
_STACK_NEXT_TIMEOUT = 60  # seconds; forget the intent if the launch is cancelled


def spawn_stacked(qtile, cmd):
    """Spawn cmd; the window it produces stacks on top of the focused one."""
    global _stack_next
    win = qtile.current_window
    if qtile.current_layout.name == "columns" and win is not None and not win.floating:
        _stack_next = (qtile.current_group.name, win, time.monotonic())
    else:
        _stack_next = None
    qtile.spawn(cmd)


@hook.subscribe.client_managed
def _stack_onto_anchor(client):
    global _stack_next
    if _stack_next is None:
        return
    group_name, anchor, when = _stack_next

    # create_internal() routes through qtile.manage(), so the tab strips below
    # fire this hook too. They are Internal, not Window, and have none of the
    # attributes read past this point.
    if not isinstance(client, backend_window.Window):
        return
    if time.monotonic() - when > _STACK_NEXT_TIMEOUT:
        _stack_next = None
        return
    # The launcher itself is not the window we are waiting for.
    if any("rofi" in c.lower() for c in (client.get_wm_class() or ())):
        return
    if client.floating or client.group is None or client.group.name != group_name:
        return

    _stack_next = None
    lay = client.group.layout
    if lay.name != "columns":
        return
    target = next((c for c in lay.columns if anchor in c), None)
    source = next((c for c in lay.columns if client in c), None)
    if target is None or source is None:
        return

    if target is not source:
        source.remove(client)
        if len(source) == 0 and len(lay.columns) > 1:
            lay.remove_column(source)
        target.add_client(client)  # insert_position puts it just above the anchor
    target.split = False  # stacked: only the focused window of the column draws
    lay.current = lay.columns.index(target)
    target.focus(client)
    lay.group.layout_all()


keys = [
    # --- window focus ---
    Key([mod], "h", lazy.layout.left(), desc="Move focus left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move focus to next window"),
    # --- move windows ---
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # --- resize ---
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset window sizes"),
    Key(
        [mod, "shift"],
        "s",
        lazy.layout.toggle_split(),
        desc="Stack/unstack the current column",
    ),
    # --- launching ---
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    Key([mod], "r", lazy.spawn(launcher), desc="Search and launch an app"),
    Key(
        [mod, "shift"],
        "r",
        lazy.function(spawn_stacked, launcher),
        desc="Search and launch an app, stacked over the focused window",
    ),
    Key(
        [mod, "shift"],
        "Return",
        lazy.function(spawn_stacked, terminal),
        desc="Launch terminal, stacked over the focused window",
    ),
    # --- layout / window management ---
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating"),
    # --- session ---
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shut down qtile"),
]

groups = [Group(i) for i in "123456789"]
for i in groups:
    keys.extend(
        [
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(),
                desc=f"Switch to group {i.name}",
            ),
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=True),
                desc=f"Move focused window to group {i.name}",
            ),
        ]
    )


# ═══ theme ═══════════════════════════════════════════════════════════════
# Palette lifted from ebenezer's colors.default.yml.
C = dict(
    fg_normal="#e0e0e0",
    fg_urgent="#ff6b6b",
    fg_blue="#007acc",
    fg_light_blue="#80d3ff",
    fg_yellow="#ffcc00",
    fg_orange="#ff9500",
    fg_grey="#b0b0b0",  # was fg_purple: the memory readout icon
    fg_dim="#7a7a7a",  # groups other than the current one
    fg_white="#ffffff",
    bg_topbar="#1e1e1e",  # bar background
    bg_topbar_selected="#9e9e9e",  # accent: popup borders, separator, slider
    bg_topbar_arrow="#3a3a3a",  # the slab on the right
    border_focus="#aa00ff",
    border_normal="#4a4a4a",  # unfocused windows
    border_focus_stack="#ffcc00",  # focused window of a stacked column
    border_normal_stack="#5c4a00",  # unfocused stacked column
)

# He uses Fira Code Nerd Font; 0xProto is the Nerd Font already on this box and
# covers the same glyphs. Symbols Nerd Font is installed as a fallback.
FONT = "0xProto Nerd Font"
FONT_BOLD = "0xProto Nerd Font Bold"
FONT_SIZE = 14
ICON_SIZE = 16
ARROW_SIZE = 30

# Nerd Font glyphs as escapes, not literals. Codepoints below U+F900 sit in the
# BMP private-use area and get silently eaten by a lot of tooling; escapes are
# the only form that reliably survives a copy-paste or a patch.
G_ARROW = ""  # powerline left-facing triangle
G_THERMAL = "\U000f10c2"  # thermometer
G_CPU = ""  # chip
G_MEMORY = "\U000f0127"  # memory sticks
G_POWER = "\uf011"  # power symbol (session menu)


# ═══ tabbed columns ══════════════════════════════════════════════════════
# A stacked column draws only its focused window, which leaves no clue what
# else is in the stack. TabbedColumns reserves a strip at the top of each
# stacked column and draws one tab per window in it.
#
# This cannot be a widget -- widgets only live in a bar. It needs an internal
# window with its own Drawer per column, which is the machinery TreeTab uses
# for its sidebar (libqtile/layout/tree.py).


def _as_int(value, fallback=0):
    """Pin a Configurable option to an int; they resolve dynamically."""
    return fallback if value is None else int(value)


class _TabStrip:
    """One internal window + Drawer, drawing the tab strip for one column."""

    def __init__(self, lay):
        self.lay = lay
        self.col = None
        self.hits = []  # [(x0, x1, window)], for routing clicks back to windows
        self.drawer = None
        self.text = None
        self.win = lay.group.qtile.core.create_internal(0, 0, 1, _as_int(lay.tab_height, 22))
        self.win.keep_below(enable=True)
        self.win.process_window_expose = self.redraw
        self.win.process_button_click = self.on_click

    def place(self, x, y, width, height):
        self.win.place(x, y, width, height, 0, None)
        if self.drawer is None or self.drawer.width != width or self.drawer.height != height:
            self._new_drawer(width, height)
        self.win.unhide()

    def _new_drawer(self, width, height):
        self._drop_drawer()
        self.drawer = self.win.create_drawer(width, height)
        # wrap=False makes pango ellipsize long titles instead of wrapping.
        self.text = self.drawer.textlayout(
            "", self.lay.tab_fg, self.lay.tab_font, self.lay.tab_fontsize, None, wrap=False
        )

    def _drop_drawer(self):
        if self.text is not None:
            self.text.finalize()
            self.text = None
        if self.drawer is not None:
            self.drawer.finalize()
            self.drawer = None

    def draw(self, col):
        self.col = col
        self.redraw()

    def redraw(self, *args):
        d, t, lay, col = self.drawer, self.text, self.lay, self.col
        if d is None or t is None or col is None:
            return
        w, h = d.width, d.height
        d.clear(lay.tab_bg)
        self.hits = []
        clients = list(col.clients)
        if clients:
            gap, pad = _as_int(lay.tab_spacing), _as_int(lay.tab_padding)
            span = (w - gap * (len(clients) - 1)) / len(clients)
            for i, c in enumerate(clients):
                x0 = int(round(i * (span + gap)))
                x1 = int(round(i * (span + gap) + span))
                focused = c is col.cw
                d.set_source_rgb(lay.tab_active_bg if focused else lay.tab_inactive_bg)
                d.fillrect(x0, 0, x1 - x0, h, 1)
                t.text = c.name or ""
                t.colour = lay.tab_active_fg if focused else lay.tab_fg
                t.width = max(1, x1 - x0 - 2 * pad)
                t.draw(x0 + pad, max(0, (h - t.height) // 2))
                self.hits.append((x0, x1, c))
        d.draw(offsetx=0, offsety=0, width=w, height=h)

    def on_click(self, x, y, button):
        if button != 1:
            return
        for x0, x1, c in self.hits:
            if x0 <= x < x1:
                self.lay.group.focus(c, False)
                return

    def hide(self):
        self.win.hide()

    def kill(self):
        self._drop_drawer()
        self.win.kill()


class TabbedColumns(layout.Columns):
    """Columns, with a tab strip along the top of every stacked column."""

    defaults = [
        ("tab_height", 22, "Height in px of the tab strip on a stacked column."),
        ("tab_bg", "#1e1e1e", "Colour behind the tabs; shows through the gaps."),
        ("tab_inactive_bg", "#3a3a3a", "Background of an unfocused tab."),
        ("tab_active_bg", "#1e1e1e", "Background of the focused tab."),
        ("tab_fg", "#b0b0b0", "Text colour of an unfocused tab."),
        ("tab_active_fg", "#ffffff", "Text colour of the focused tab."),
        ("tab_font", "sans", "Tab font."),
        ("tab_fontsize", 12, "Tab font size."),
        ("tab_padding", 8, "Horizontal padding inside a tab."),
        ("tab_spacing", 2, "Gap in px between adjacent tabs."),
        ("tabs_on_single", False, "Draw the strip on a stacked column holding one window."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(TabbedColumns.defaults)
        self._strips = []
        self._tabbed = []
        self._hooked = False

    def clone(self, group):
        c = super().clone(group)
        # Layout.clone is a shallow copy and every group gets its own clone, so
        # the internal windows have to be per-clone or the groups fight over them.
        c._strips = []
        c._tabbed = []
        c._hooked = False
        return c

    # --- geometry ---
    def _margins(self):
        """North, east and west margins; Columns accepts an int or [N E S W]."""
        m = self.margin
        if isinstance(m, (list, tuple)):
            return _as_int(m[0]), _as_int(m[1]), _as_int(m[3])
        return _as_int(m), _as_int(m), _as_int(m)

    def _column_x(self, col, screen_rect):
        """x and width of col, matching Columns.configure's own arithmetic."""
        pos = 0
        for c in self.columns:
            if c is col:
                break
            pos += c.width
        n = len(self.columns)
        width = int(0.5 + col.width * screen_rect.width * 0.01 / n)
        x = screen_rect.x + int(0.5 + pos * screen_rect.width * 0.01 / n)
        return x, width

    def _wants_tabs(self, col):
        return not col.split and (len(col) > 1 or self.tabs_on_single)

    def _is_tabbed(self, col):
        return any(c is col for c in self._tabbed)

    # --- hooking into the layout cycle ---
    def layout(self, windows, screen_rect):
        self._sync_strips(screen_rect)
        super().layout(windows, screen_rect)

    def _sync_strips(self, screen_rect):
        tab_h = _as_int(self.tab_height)
        if not 0 < tab_h < screen_rect.height:
            self._tabbed = []
            self._kill_strips()
            return

        self._tabbed = [c for c in self.columns if self._wants_tabs(c)]
        while len(self._strips) > len(self._tabbed):
            self._strips.pop().kill()
        while len(self._strips) < len(self._tabbed):
            self._strips.append(_TabStrip(self))

        # Focus changes already relayout via Group.focus; title changes do not.
        if self._strips and not self._hooked:
            hook.subscribe.client_name_updated(self._on_name_change)
            self._hooked = True

        north, east, west = self._margins()
        for strip, col in zip(self._strips, self._tabbed):
            x, width = self._column_x(col, screen_rect)
            strip.place(
                x + west,
                screen_rect.y + north,
                max(1, width - west - east),
                tab_h,
            )
            strip.draw(col)

    def configure(self, client, screen_rect):
        col = next((c for c in self.columns if client in c), None)
        if col is not None and self._is_tabbed(col):
            # vsplit only moves y and shrinks height, so the column widths
            # Columns derives from screen_rect.x/width come out unchanged.
            screen_rect = screen_rect.vsplit(_as_int(self.tab_height))[1]
        super().configure(client, screen_rect)

    # --- lifecycle ---
    def _on_name_change(self, *args):
        for strip in self._strips:
            strip.redraw()

    def _kill_strips(self):
        while self._strips:
            self._strips.pop().kill()

    def hide(self):
        for strip in self._strips:
            strip.hide()

    def remove(self, client):
        res = super().remove(client)
        if not self.get_windows():
            # An empty group never calls layout(), so clean up here instead.
            self._tabbed = []
            self._kill_strips()
        return res

    def finalize(self):
        if self._hooked:
            hook.unsubscribe.client_name_updated(self._on_name_change)
            self._hooked = False
        self._kill_strips()
        super().finalize()


_COLUMN_OPTS = dict(
    border_focus=C["border_focus"],
    border_normal=C["border_normal"],
    border_focus_stack=C["border_focus_stack"],
    border_normal_stack=C["border_normal_stack"],
    border_width=2,
    margin=4,
)

layouts = [
    TabbedColumns(
        tab_height=22,
        tab_bg=C["bg_topbar"],
        tab_inactive_bg=C["bg_topbar_arrow"],
        tab_active_bg=C["bg_topbar"],
        tab_fg=C["fg_grey"],
        tab_active_fg=C["fg_white"],
        tab_font=FONT_BOLD,
        tab_fontsize=FONT_SIZE - 2,
        **_COLUMN_OPTS,
    ),
    # Plain Columns kept as a fallback: mod+Tab reaches a known-good layout if
    # the tab strips ever misbehave.
    layout.Columns(**_COLUMN_OPTS),
    layout.Max(),
]

widget_defaults = dict(font=FONT_BOLD, fontsize=FONT_SIZE, padding=3)
extension_defaults = widget_defaults.copy()


# ═══ custom widgets ══════════════════════════════════════════════════════
# Stock qtile has no threshold colouring on CPU/Memory, no glyph-based layout
# indicator, and no icon substitution in TaskList. These three fill those gaps.


class _Thresholded:
    """Recolour a polled widget as its reading crosses the medium/high marks."""

    def _colorize(self, value, text):
        if value > self.threshold_high:
            self.foreground = C["fg_orange"]
            return f"🔥 {text}"
        if value > self.threshold_medium:
            self.foreground = C["fg_yellow"]
            return text
        self.foreground = C["fg_normal"]
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


# ═══ popup keyboard ══════════════════════════════════════════════════════
# A popup is an Internal window that takes input focus while open, so every
# keystroke goes to it and not to whatever you were typing in. The toolkit's
# default keymap binds bare letters for that - h/j/k/l to navigate and space to
# select - which turns ordinary typing into menu operation. Arrows, Enter and
# Escape only.

POPUP_KEYMAP = {
    "left": ["Left"],
    "right": ["Right"],
    "up": ["Up"],
    "down": ["Down"],
    "select": ["Return"],
    "step": ["Tab"],
    "close": ["Escape"],
}


# ═══ volume slider popup ═════════════════════════════════════════════════
# Left-clicking the volume glyph opens a draggable slider under it.
# PopupSlider tracks the pointer while the button is held and hands the final
# value to drag_callback on release.

SINK = "@DEFAULT_AUDIO_SINK@"
POPUP_W, POPUP_H = 250, 86


def _volume_get():
    out = subprocess.run(
        ["wpctl", "get-volume", SINK], capture_output=True, text=True
    ).stdout
    return float(out.split()[1])  # "Volume: 0.76 [MUTED]"


def _volume_set(value):
    subprocess.run(
        ["wpctl", "set-volume", "-l", "1.0", SINK, f"{round(value * 100)}%"],
        check=False,
    )


VOLUME_LABEL = "Volume   {}%"


class LabelledSlider(PopupSlider):
    """PopupSlider that keeps a sibling PopupText in step while dragging.

    The stock control only reports its value through drag_callback on release,
    so the readout would sit stale until you let go.
    """

    def __init__(self, label_name="label", label_format="{}", **config):
        PopupSlider.__init__(self, **config)
        self._label_name = label_name
        self._label_format = label_format

    def pointer_motion(self, x, y):
        # the parent recomputes self.value from the pointer and repaints the bar
        PopupSlider.pointer_motion(self, x, y)
        if self._drag:
            self._sync_label()

    def _sync_label(self):
        label = next(
            (c for c in self.container.controls if c.name == self._label_name), None
        )
        if label is None:
            return
        text = self._label_format.format(round(self.value * 100))
        # motion fires far faster than the value changes a whole percent, so
        # only repaint when the text actually differs
        if label.text != text:
            label.text = text
            self.container.draw()  # clears and repaints every control


_volume_popup = None


def _volume_popup_alive():
    """True only if the popup is both un-killed and still a live window.

    Checking _killed alone is not enough: it is only set by the toolkit's own
    kill(), so a popup whose window went away by any other route would leave a
    stale reference here and the next click would close nothing.
    """
    if _volume_popup is None or getattr(_volume_popup, "_killed", True):
        return False
    win = getattr(getattr(_volume_popup, "popup", None), "win", None)
    return win is not None and win.wid in qtile.windows_map


def _toggle_volume_slider():
    """Button1 on the volume widget: open the slider, or dismiss it if open."""
    global _volume_popup

    if _volume_popup_alive():
        _volume_popup.kill()
        _volume_popup = None
        return
    _volume_popup = None

    vol = _volume_get()

    # centre the popup under the volume glyph, clamped to the screen edge
    # NB: offsetx, not offset — info() reports it as "offset" but the attribute
    # on the widget is offsetx.
    vol_widget = qtile.widgets_map.get("volume")
    if vol_widget is not None:
        x = vol_widget.offsetx + vol_widget.length // 2 - POPUP_W // 2
    else:
        x = 0
    x = max(0, min(x, qtile.current_screen.width - POPUP_W))

    _volume_popup = PopupRelativeLayout(
        qtile,
        width=POPUP_W,
        height=POPUP_H,
        background=C["bg_topbar"],
        border=C["bg_topbar_selected"],
        border_width=2,
        initial_focus=None,
        keymap=POPUP_KEYMAP,
        close_on_click=False,  # a click here starts a drag; don't dismiss on it
        # Not hide_on_mouse_leave: you click the glyph up in the bar, so the
        # pointer is never inside the popup when it opens and it reads as an
        # immediate "leave" — the popup dies before it can be seen. Dismiss is
        # a second click on the glyph, or Escape.
        hide_on_mouse_leave=False,
        controls=[
            PopupText(
                text=VOLUME_LABEL.format(round(vol * 100)),
                name="label",
                pos_x=0.06,
                pos_y=0.14,
                width=0.88,
                height=0.28,
                font=FONT,
                fontsize=15,
                foreground=C["fg_normal"],
                h_align="center",
            ),
            LabelledSlider(
                name="volume",
                label_name="label",
                label_format=VOLUME_LABEL,
                value=vol,
                # The toolkit derives keyboard_navigation from whether any
                # control is focusable, overwriting the layout's own setting.
                # Without a focusable control it never calls set_hooks(), so
                # nothing watches focus and the popup can only be dismissed by
                # clicking the glyph again. can_focus arms the focus hooks,
                # which is what closes it on a click elsewhere (and on Escape).
                can_focus=True,
                # ...but focusable controls also highlight on hover, in a teal
                # that clashes badly. Match the popup background to hide it.
                highlight=C["bg_topbar"],
                pos_x=0.09,
                pos_y=0.52,
                width=0.82,
                height=0.30,
                colour_below=C["bg_topbar_selected"],
                colour_above=C["bg_topbar_arrow"],
                marker_colour=C["fg_normal"],
                marker_size=14,
                bar_size=6,
                bar_border_size=0,
                end_margin=0,
                drag_callback=_volume_set,
            ),
        ],
    )
    # relative_to=1 anchors to the screen's top-left, so x/y are plain screen
    # coordinates; relative_to_bar drops y below the bar. Note relative_to=0
    # is NOT absolute — it ignores x/y and places the popup at the pointer.
    _volume_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)


# ═══ bar ═════════════════════════════════════════════════════════════════
# Left: groups + task list. Centre: clock. Right: a #3e0d5c slab entered
# through a powerline arrow, holding the system readouts.
#
# The slab is not a real powerline — it's one oversized G_ARROW glyph coloured
# to match, followed by ordinary widgets that all share that background.


def _slab(**kwargs):
    """Shared styling for everything sitting on the purple slab."""
    return dict(
        font=FONT,
        fontsize=ICON_SIZE,
        background=C["bg_topbar_arrow"],
        foreground=C["fg_normal"],
        **kwargs,
    )


def _slab_icon(glyph, color):
    """An accent-coloured icon on the slab, paired with the readout after it."""
    return widget.TextBox(f"{glyph} ", **{**_slab(padding=2), "foreground": color})


# ═══ power menu ══════════════════════════════════════════════════════════
# Clicking the power glyph opens a menu built with the same qtile-extras popup
# toolkit as the volume slider, so it inherits click-outside dismissal, Escape
# and arrow-key navigation from that machinery.
#
# Every entry confirms before acting: the menu opens directly under the button,
# where the logout text button used to be, so a misclick is a real power-off.
# polkit already allows poweroff and reboot for a local active session, so
# neither prompts for a password.

G_LOGOUT = "\U000f0343"
G_REBOOT = "\U000f0709"
G_SHUTDOWN = "\U000f0425"
G_CANCEL = "\U000f0156"

POWER_W = 210  # popup width
POWER_PAD = 6  # inner margin
POWER_ROW_H = 34  # one clickable line
POWER_TITLE_H = 30  # "Are you sure?" header


def _logout():
    # qtile's own shutdown rather than `loginctl terminate-session`: it fires
    # the shutdown hook, which is what stops qtile-session.target.
    qtile.shutdown()


def _reboot():
    subprocess.Popen(["systemctl", "reboot"])


def _poweroff():
    subprocess.Popen(["systemctl", "poweroff"])


# glyph, menu label, confirmation label, action
POWER_ACTIONS = [
    (G_SHUTDOWN, "Shut down", "Yes, shut down", _poweroff),
    (G_REBOOT, "Reboot", "Yes, reboot", _reboot),
    (G_LOGOUT, "Log out", "Yes, log out", _logout),
]

_power_popup = None


def _power_popup_alive():
    # same reasoning as _volume_popup_alive: _killed alone would go stale if the
    # window went away by some route other than the toolkit's own kill()
    if _power_popup is None or getattr(_power_popup, "_killed", True):
        return False
    win = getattr(getattr(_power_popup, "popup", None), "win", None)
    return win is not None and win.wid in qtile.windows_map


def _close_power_popup():
    global _power_popup
    if _power_popup_alive():
        _power_popup.kill()  # kill() has no re-entry guard, hence the check
    _power_popup = None


def _power_row(index, glyph, label, callback, danger=False, offset_y=0):
    """One clickable line in the menu."""
    return PopupText(
        text=f"{glyph}  {label}",
        pos_x=POWER_PAD,
        pos_y=POWER_PAD + offset_y + index * POWER_ROW_H,
        width=POWER_W - 2 * POWER_PAD,
        height=POWER_ROW_H,
        font=FONT,
        fontsize=15,
        foreground=C["fg_urgent"] if danger else C["fg_normal"],
        # can_focus is left at "auto", which resolves to True for any control
        # with a Button1 callback. That is what arms the layout's focus hooks -
        # without a focusable control the toolkit never calls set_hooks() and
        # neither click-outside nor Escape would work.
        highlight=C["bg_topbar_selected"],
        foreground_highlighted=C["bg_topbar"],
        highlight_method="block",
        h_align="left",
        mouse_callbacks={"Button1": callback},
    )


def _show_power_popup(controls, height, initial_focus=None):
    global _power_popup
    _close_power_popup()

    # centre under the power glyph, clamped to the screen edge. The widget is a
    # named subclass because widgets_map keys on the class name and a plain
    # TextBox would collide with the other text boxes in the bar.
    btn = qtile.widgets_map.get("powerbutton")
    x = btn.offsetx + btn.length // 2 - POWER_W // 2 if btn is not None else 0
    x = max(0, min(x, qtile.current_screen.width - POWER_W))

    _power_popup = PopupAbsoluteLayout(
        qtile,
        width=POWER_W,
        height=height,
        background=C["bg_topbar"],
        border=C["bg_topbar_selected"],
        border_width=2,
        # The menu pre-selects its first row so one Down doesn't skip it: with
        # nothing focused, the first key press adopts row 0 and *then* moves.
        # The confirmation passes None instead, so Enter can't fire an action
        # you never selected.
        initial_focus=initial_focus,
        keymap=POPUP_KEYMAP,
        # the row callbacks decide what happens next (confirm, act, or close),
        # so don't let the toolkit tear the popup down underneath them
        close_on_click=False,
        # you click the glyph up in the bar, so the pointer is never inside the
        # popup when it opens - mouse-leave would kill it instantly
        hide_on_mouse_leave=False,
        controls=controls,
    )
    _power_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)


def _confirm_power(glyph, confirm_label, action):
    """Second stage: swap the menu for a yes/cancel prompt."""

    def _do():
        _close_power_popup()
        action()

    controls = [
        PopupText(
            text="Are you sure?",
            pos_x=POWER_PAD,
            pos_y=POWER_PAD,
            width=POWER_W - 2 * POWER_PAD,
            height=POWER_TITLE_H,
            font=FONT,
            fontsize=14,
            foreground=C["fg_normal"],
            h_align="center",
        ),
        _power_row(0, glyph, confirm_label, _do, danger=True, offset_y=POWER_TITLE_H),
        _power_row(1, G_CANCEL, "Cancel", _close_power_popup, offset_y=POWER_TITLE_H),
    ]
    # Focus Cancel, not the action: focusable_controls is built in control
    # order, so index 1 is the Cancel row. Enter on this popup backs out.
    _show_power_popup(
        controls,
        POWER_PAD * 2 + POWER_TITLE_H + 2 * POWER_ROW_H,
        initial_focus=1,
    )


def _power_menu():
    """Button1 on the power glyph: open the menu, or dismiss it if open."""
    if _power_popup_alive():
        _close_power_popup()
        return

    controls = [
        _power_row(i, glyph, label, partial(_confirm_power, glyph, confirm, act))
        for i, (glyph, label, confirm, act) in enumerate(POWER_ACTIONS)
    ]
    _show_power_popup(
        controls,
        POWER_PAD * 2 + len(POWER_ACTIONS) * POWER_ROW_H,
        initial_focus=0,
    )


class PowerButton(widget.TextBox):
    """TextBox under its own name, so the popup can locate it in widgets_map."""


bar_widgets = [
    widget.GroupBox(
        margin_y=3,
        margin_x=3,
        padding=1,
        borderwidth=0,
        font=FONT,
        fontsize=ICON_SIZE,
        active=C["fg_dim"],
        inactive=C["fg_dim"],
        foreground=C["fg_dim"],
        this_current_screen_border=C["fg_white"],
        this_screen_border=C["fg_blue"],
        other_current_screen_border=C["fg_white"],
        highlight_color=C["fg_white"],
        highlight_method="text",
        rounded=False,
        urgent_alert_method="border",
        urgent_border=C["fg_urgent"],
    ),
    # Divides the groups from the task list. bg_topbar_arrow (#3e0d5c) is the
    # slab colour and is all but invisible against the #1e1e1e bar, so this
    # uses the same accent purple as the active group.
    widget.Sep(
        foreground=C["bg_topbar_selected"], padding=24, linewidth=1, size_percent=55
    ),
    IconTaskList(
        icon_size=0,
        margin_y=4,
        margin_x=5,
        padding=0,
        spacing=18,
        highlight_method="border",
        border=C["fg_normal"],
        borderwidth=0,
        font=FONT,
        fontsize=ICON_SIZE - 2,
        foreground=C["fg_normal"],
        max_title_width=180,
        # The base class prefixes a state marker: 'V ' floating, '[] ' maximized,
        # '_ ' minimized. Cleared so the entry is only the glyph and the app.
        txt_floating="",
        txt_maximized="",
        txt_minimized="",
    ),
    widget.Spacer(length=5),
    widget.Clock(
        format="%b %d, %I:%M %p",
        font=FONT,
        fontsize=ICON_SIZE,
        foreground=C["fg_normal"],
        padding=2,
    ),
    widget.Spacer(length=bar.STRETCH),
    widget.TextBox(
        G_ARROW,
        font=FONT,
        fontsize=ARROW_SIZE,
        foreground=C["bg_topbar_arrow"],
        padding=0,
    ),
    _slab_icon(G_THERMAL, C["fg_light_blue"]),
    widget.ThermalSensor(
        **_slab(padding=2),
        tag_sensor="Package id 0",
        format="{temp:.0f}{unit} ",
        threshold=75,
        foreground_alert=C["fg_orange"],
    ),
    _slab_icon(G_CPU, C["fg_yellow"]),
    ColorizedCPU(**_slab(padding=2), format="{load_percent}% "),
    _slab_icon(G_MEMORY, C["fg_grey"]),
    ColorizedMemory(**_slab(padding=2), format="{MemUsed:.0f}{mm} "),
    widget.Battery(
        **_slab(padding=5),
        # Pin the ACPI name. qtile's autodetect walks /sys/class/power_supply
        # and takes the first dir exposing a "capacity" file, which on this box
        # can be hidpp_battery_2 — the MX Master 3S. The mouse reports capacity
        # but no energy_now, so the widget dies with "Unable to read status for
        # energy_now_file" whenever the mouse sorts ahead of BAT0.
        battery="BAT0",
        format="{char} {percent:2.0%}",
        charge_char="",  # plug
        discharge_char="",  # battery draining
        empty_char="",
        full_char="",
        not_charging_char="\U000f06a6",
        unknown_char="\U000f06c4",
        low_percentage=0.15,
        low_foreground=C["fg_urgent"],
    ),
    widget.Volume(
        **_slab(padding=5),
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
        # Button1 defaults to mute; the slider is more useful there, so mute
        # moves to right-click (its default Button3 action, run_app, is a no-op
        # anyway — no mixer installed). Scroll still nudges the volume.
        mouse_callbacks={
            "Button1": _toggle_volume_slider,
            "Button3": lambda: subprocess.run(
                ["wpctl", "set-mute", SINK, "toggle"], check=False
            ),
        },
    ),
    widget.Systray(**_slab(padding=4)),  # nm-applet etc. dock here
    PowerButton(G_POWER, **_slab(padding=8), mouse_callbacks={"Button1": _power_menu}),
    # tail of the slab: without the background it reverts to the bar colour
    # and leaves a gap between the power button and the screen edge
    widget.Spacer(length=5, background=C["bg_topbar_arrow"]),
]

screens = [
    Screen(
        wallpaper="/home/nick/.local/share/backgrounds/2025-11-27-08-48-14-puppycat_sleeping.jpg",
        wallpaper_mode="fill",
        top=bar.Bar(bar_widgets, 34, background=C["bg_topbar"]),
    ),
]

mouse = [
    Drag(
        [mod_mouse],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod_mouse],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
    Click([mod_mouse], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False

floating_layout = layout.Floating(
    border_focus=C["border_focus"],
    border_normal=C["border_normal"],
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
