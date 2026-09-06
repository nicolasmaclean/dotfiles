# ═══ imports ══════════════════════════════════════════════════════
# qtile core
from libqtile import hook, layout

# internal
from theme import T


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
        self.win = lay.group.qtile.core.create_internal(
            0, 0, 1, _as_int(lay.tab_height, 22)
        )
        self.win.keep_below(enable=True)
        self.win.process_window_expose = self.redraw
        self.win.process_button_click = self.on_click

    def place(self, x, y, width, height):
        self.win.place(x, y, width, height, 0, None)
        if (
            self.drawer is None
            or self.drawer.width != width
            or self.drawer.height != height
        ):
            self._new_drawer(width, height)
        self.win.unhide()

    def _new_drawer(self, width, height):
        self._drop_drawer()
        self.drawer = self.win.create_drawer(width, height)
        # wrap=False makes pango ellipsize long titles instead of wrapping.
        self.text = self.drawer.textlayout(
            "",
            self.lay.tab_fg,
            self.lay.tab_font,
            self.lay.tab_fontsize,
            None,
            wrap=False,
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

    # Values live in theme.py (Tabs); only the descriptions are here.
    defaults = [
        ("tab_height", T.height, "Height in px of the tab strip on a stacked column."),
        ("tab_bg", T.bg, "Colour behind the tabs; shows through the gaps."),
        ("tab_inactive_bg", T.inactive_bg, "Background of an unfocused tab."),
        ("tab_active_bg", T.active_bg, "Background of the focused tab."),
        ("tab_fg", T.fg, "Text colour of an unfocused tab."),
        ("tab_active_fg", T.active_fg, "Text colour of the focused tab."),
        ("tab_font", T.font, "Tab font."),
        ("tab_fontsize", T.fontsize, "Tab font size."),
        ("tab_padding", T.padding, "Horizontal padding inside a tab."),
        ("tab_spacing", T.spacing, "Gap in px between adjacent tabs."),
    ]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(TabbedColumns.defaults)
        self._strips = []
        self._tabbed = []
        self._hooked = False

    # --- stacking policy ---
    # With num_columns=2, once both columns exist a new window is handed to the
    # current column. Columns' own default is to split it, halving everyone's
    # height; stack it instead, so the extra window becomes another tab.
    #
    # The invariant this keeps is the same one _wants_tabs tests: a column is
    # stacked exactly while it holds more than one window. Dropping back to one
    # window re-splits, which is a no-op for placement but restores the plain
    # border colours (Columns paints a non-split column with border_*_stack).
    def add_client(self, client):
        will_add_column = len(self.cc) > 0 and len(self.columns) < self.num_columns
        if len(self.cc) > 0 and not will_add_column:
            self.cc.split = False
        super().add_client(client)

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
        return not col.split and len(col) > 1

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
        for col in self.columns:
            if len(col) <= 1:
                col.split = True
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
