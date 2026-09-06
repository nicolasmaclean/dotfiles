# ═══ imports ══════════════════════════════════════════════════════════════
import os
import subprocess
from functools import partial
from typing import ClassVar

from libqtile import qtile
from libqtile.command.base import expose_command
from libqtile.widget import base
from qtile_extras.popup.toolkit import PopupAbsoluteLayout, PopupText

from popups import POPUP_KEYMAP, popup_alive
from theme import C, F, G

# ═══ network ══════════════════════════════════════════════════════════════
# Replaces nm-applet. That applet has no configuration surface at all - no
# flags, no settings, and a menu that only follows the ambient GTK theme - so
# the only way to make the network indicator match the rest of the bar is to
# stop docking a foreign widget in the tray and draw it here instead.
#
# Everything goes through nmcli rather than NetworkManager's D-Bus API: the
# readings are a handful of short-lived subprocesses on a 5s poll, which is
# far less machinery than a D-Bus client for the same three facts, and the
# poll runs off the event loop (see NetworkButton).
#
# Scanning is the one slow part, and it never happens on the event loop.
# `nmcli device wifi list --rescan no` is cheap but on this box returns only
# the access point already joined - NetworkManager prunes the cache hard - so
# a useful list needs a real scan, and a real scan takes seconds. So the menu
# opens immediately on the last scan's results and kicks a fresh scan into the
# executor; when that lands, the menu redraws itself in place if it is still
# open and the list actually changed. Nothing scans while the menu is closed.
#
# The menu is the same qtile-extras popup toolkit as power.py, so it inherits
# click-outside dismissal, Escape and arrow-key navigation from that.

NET_W = 280  # popup width
NET_PAD = 6  # inner margin
NET_ROW_H = 30  # one clickable line
NET_RULE_H = 12  # the divider above the footer
MAX_NETWORKS = 8  # SSIDs listed before the list is cut off
NMCLI_TIMEOUT = 5  # seconds before a reading is given up on
SCAN_TIMEOUT = 25  # a scan is slow; give it its own, longer budget
SSID_CHARS = 22  # truncation inside the menu


# ═══ nmcli ════════════════════════════════════════════════════════════════
def _spawn(argv, env=None):
    """Fire and forget. Output is dropped; failures announce themselves."""
    try:
        subprocess.Popen(
            argv,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def _nmcli(*args, timeout=NMCLI_TIMEOUT):
    """Run nmcli and return stdout, or None if it failed in any way."""
    try:
        done = subprocess.run(
            ("nmcli", *args),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # the return code is the reading, not an error
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def _unescape(field):
    r"""Undo nmcli -t's backslash escaping of ':' and '\'."""
    out, escaped = [], False
    for ch in field:
        if escaped:
            out.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        else:
            out.append(ch)
    return "".join(out)


def _rows(fields, *args, timeout=NMCLI_TIMEOUT):
    """Terse nmcli output as a list of field lists.

    -t delimits with ':' and escapes any literal colon in a value, so a field
    that can contain one has to be asked for *last*: split() is given a
    maxsplit that runs out before it reaches that value, leaving it whole.
    Every caller below therefore puts SSID/NAME at the end of `fields`.
    """
    out = _nmcli("-t", "-f", fields, *args, timeout=timeout)
    if out is None:
        return []
    maxsplit = fields.count(",")
    return [
        [_unescape(f) for f in line.split(":", maxsplit)]
        for line in out.splitlines()
        if line
    ]


def _radio_on():
    return (_nmcli("-t", "radio", "wifi") or "").strip() == "enabled"


def _saved_ssids():
    """Names of the stored Wi-Fi profiles.

    Only used to decide whether connecting needs to ask for a password -
    `nmcli device wifi connect` reuses a stored profile on its own.
    """
    return {
        row[1]
        for row in _rows("TYPE,NAME", "connection", "show")
        if len(row) == 2 and row[0] == "802-11-wireless"
    }


# The last scan's results, written from the executor thread and read on the
# event loop. Rebound rather than mutated, so a reader always sees one whole
# list - no lock needed for a plain attribute swap.
_scan_cache = []


def _parse_networks(rows):
    """Scan rows as (in_use, signal, secured, name), best first."""
    best = {}
    for row in rows:
        if len(row) != 4:
            continue
        in_use, signal, security, ssid = row
        if not ssid:
            continue  # a hidden network: nothing here to click
        try:
            strength = int(signal)
        except ValueError:
            strength = 0
        entry = (in_use == "*", strength, bool(security), ssid)
        # One SSID shows up once per band and per access point. Keep the
        # entry we are actually on, else the strongest of them.
        if ssid not in best or entry[:2] > best[ssid][:2]:
            best[ssid] = entry
    return sorted(best.values(), key=lambda e: (not e[0], -e[1]))[:MAX_NETWORKS]


def _scan():
    """Rescan and refresh the cache. Blocking - executor thread only."""
    global _scan_cache
    rows = _rows(
        "IN-USE,SIGNAL,SECURITY,SSID",
        "dev",
        "wifi",
        "list",
        "--rescan",
        "yes",
        timeout=SCAN_TIMEOUT,
    )
    if rows:
        _scan_cache = _parse_networks(rows)
    return _scan_cache


def _active_signal():
    """Signal of the joined access point, without triggering a scan.

    --rescan no is what makes this cheap enough for the 5s poll, and the one
    row it reliably returns is exactly the one wanted here.
    """
    for row in _rows(
        "IN-USE,SIGNAL,SECURITY,SSID", "dev", "wifi", "list", "--rescan", "no"
    ):
        if len(row) == 4 and row[0] == "*":
            try:
                return int(row[1])
            except ValueError:
                return 0
    return 0


def _link():
    """What the box is on: (kind, name, signal, device).

    kind is "ethernet", "wifi", "none" (radio up, nothing joined) or "off".
    """
    wifi = None
    for row in _rows("TYPE,STATE,DEVICE,CONNECTION", "dev", "status"):
        if len(row) != 4:
            continue
        kind, state, device, conn = row
        # Wired wins when both are up: it is the link actually carrying traffic.
        if kind == "ethernet" and state == "connected":
            return ("ethernet", conn, 100, device)
        if kind == "wifi" and wifi is None:
            wifi = (state, device, conn)
    if wifi is None:
        return ("none", "", 0, "")
    if wifi[0] == "connected":
        return ("wifi", wifi[2], _active_signal(), wifi[1])
    return ("none" if _radio_on() else "off", "", 0, wifi[1])


def _signal_glyph(signal):
    if signal >= 75:
        return G.wifi_4
    if signal >= 50:
        return G.wifi_3
    if signal >= 25:
        return G.wifi_2
    return G.wifi_1


# ═══ actions ══════════════════════════════════════════════════════════════
# rofi rather than a control in the popup: the qtile-extras toolkit has no
# text-entry control, and rofi is already the launcher (remap.py), so the
# password prompt looks like the rest of the session for free. The SSID rides
# in on the environment so nothing has to be quoted into the shell.
_ASK_PASSWORD_SH = """\
pw=$(rofi -dmenu -password -lines 0 -p "Wi-Fi" -mesg "Password for $SSID") || exit 0
[ -n "$pw" ] || exit 0
nmcli device wifi connect "$SSID" password "$pw" \
    || notify-send -a qtile "Wi-Fi" "Could not connect to $SSID"
"""


def _refresh(delay=2):
    """Re-poll the bar widget once an action has had time to land."""
    button = qtile.widgets_map.get("network")
    if button is not None:
        qtile.call_later(delay, button.force_update)


def _connect(ssid, secured, saved):
    _close_net_popup()
    if secured and not saved:
        _spawn(["sh", "-c", _ASK_PASSWORD_SH], env={**os.environ, "SSID": ssid})
    else:
        # Covers both the open network and the one whose secret is already
        # stored: this form activates an existing profile when it finds one.
        _spawn(["nmcli", "device", "wifi", "connect", ssid])
    _refresh(3)


def _disconnect(device):
    _close_net_popup()
    if device:
        _spawn(["nmcli", "device", "disconnect", device])
    _refresh()


def _toggle_radio(currently_on):
    _close_net_popup()
    _spawn(["nmcli", "radio", "wifi", "off" if currently_on else "on"])
    _refresh(1)


def _settings():
    _close_net_popup()
    _spawn(["nm-connection-editor"])


# ═══ the menu ═════════════════════════════════════════════════════════════
_net_popup = None


def _close_net_popup():
    global _net_popup
    if popup_alive(_net_popup):
        _net_popup.kill()  # kill() has no re-entry guard, hence the check
    _net_popup = None


def _net_row(offset_y, text, callback=None, foreground=None):
    """One line in the menu. Without a callback it is inert and unfocusable."""
    return PopupText(
        text=text,
        pos_x=NET_PAD,
        pos_y=offset_y,
        width=NET_W - 2 * NET_PAD,
        height=NET_ROW_H,
        font=F.normal,
        fontsize=15,
        foreground=foreground or C.fg_normal,
        # can_focus is left at "auto", which resolves to True only for a
        # control with a Button1 callback - so the divider below stays out of
        # the focus ring, and the arrow keys skip straight over it.
        # Hover lifts the block and brightens the text to white - see the
        # note on Colors.bg_highlight. Every focusable row goes to the same
        # white, so the connected network stops being the only bright one
        # only while the pointer is somewhere else.
        highlight=C.bg_highlight if callback else None,
        foreground_highlighted=C.fg_white if callback else None,
        highlight_method="block" if callback else None,
        h_align="left",
        mouse_callbacks={"Button1": callback} if callback else {},
    )


def _net_rule(offset_y):
    """Divides the networks from the controls under them."""
    return PopupText(
        text="─" * 34,
        pos_x=NET_PAD,
        pos_y=offset_y,
        width=NET_W - 2 * NET_PAD,
        height=NET_RULE_H,
        font=F.normal,
        fontsize=10,
        foreground=C.fg_dim,
        h_align="center",
    )


def _ssid_label(in_use, signal, secured, ssid):
    name = ssid if len(ssid) <= SSID_CHARS else ssid[: SSID_CHARS - 1] + "…"
    marks = f" {G.lock}" if secured else ""
    marks += f"  {G.check}" if in_use else ""
    return f"{_signal_glyph(signal)}  {name}{marks}"


def _menu_rows():
    """Every line of the menu as (text, callback, foreground), top to bottom.

    Built as data first so the background refresh can tell a scan that changed
    something from one that changed nothing, and skip a pointless redraw.
    """
    kind, _name, _signal, device = _link()
    radio = kind != "off"
    networks = _scan_cache if radio else []
    saved = _saved_ssids() if networks else set()

    rows = []
    if radio and not networks:
        rows.append(("  Scanning…", None, C.fg_dim))
    for in_use, signal, secured, ssid in networks:
        rows.append(
            (
                _ssid_label(in_use, signal, secured, ssid),
                partial(_connect, ssid, secured, ssid in saved),
                C.fg_white if in_use else C.fg_normal,
            )
        )
    if rows:
        rows.append((None, None, None))  # the divider
    if kind in ("wifi", "ethernet"):
        rows.append((f"{G.no_network}  Disconnect", partial(_disconnect, device), None))
    rows.append(
        (
            # The glyph tracks the state the label names, not the state a
            # click would move to: the row reads "Wi-Fi: on" beside a live
            # aerial, rather than beside the crossed-out one it turns into.
            f"{G.wifi if radio else G.wifi_off}  Wi-Fi: {'on' if radio else 'off'}",
            partial(_toggle_radio, radio),
            None,
        )
    )
    rows.append((f"{G.cog}  Settings…", _settings, None))
    return rows


def _show_menu(rows):
    """Lay `rows` out and put the popup on screen, replacing any open one."""
    global _net_popup
    _close_net_popup()

    controls, y = [], NET_PAD
    for text, callback, foreground in rows:
        if text is None:
            controls.append(_net_rule(y))
            y += NET_RULE_H
        else:
            controls.append(_net_row(y, text, callback, foreground))
            y += NET_ROW_H
    y += NET_PAD

    # Right-align under the button, clamped to the screen edge: the widget
    # sits near the right end of the bar, so centring would hang the popup
    # off it. widgets_map keys on the widget's name (set in config.py).
    button = qtile.widgets_map.get("network")
    if button is not None:
        x = button.offsetx + button.length - NET_W
    else:
        x = qtile.current_screen.width - NET_W
    x = max(0, min(x, qtile.current_screen.width - NET_W))

    _net_popup = PopupAbsoluteLayout(
        qtile,
        width=NET_W,
        height=y,
        background=C.bg_topbar,
        border=C.bg_topbar_selected,
        border_width=2,
        # Nothing pre-selected: Enter on a freshly opened menu should not
        # join whichever network happens to have sorted to the top.
        initial_focus=None,
        keymap=POPUP_KEYMAP,
        # the row callbacks close the popup themselves, after reading the
        # arguments they were built with
        close_on_click=False,
        # you click the glyph up in the bar, so the pointer is never inside
        # the popup when it opens - mouse-leave would kill it instantly
        hide_on_mouse_leave=False,
        controls=controls,
    )
    _net_popup.show(x=x, y=4, relative_to=1, relative_to_bar=True)
    return rows


def _rescan_into_menu(shown):
    """Scan off the event loop; redraw the open menu if the list moved."""
    future = qtile.run_in_executor(_scan)

    def _done(completed):
        # add_done_callback fires via call_soon, so this is back on the event
        # loop and may safely touch the popup. Asked rather than raised: a
        # scan that failed just leaves the previous list up.
        if completed.cancelled() or completed.exception() is not None:
            return
        if not popup_alive(_net_popup):
            return  # dismissed while the radio was busy
        rows = _menu_rows()
        if [r[0] for r in rows] != [r[0] for r in shown]:
            _show_menu(rows)

    future.add_done_callback(_done)


def network_menu():
    """Button1 on the network glyph: open the menu, or dismiss it if open."""
    if popup_alive(_net_popup):
        _close_net_popup()
        return
    # Opens on the previous scan's results - instantly, and stale by however
    # long ago that was - then refreshes itself once the new scan lands.
    _rescan_into_menu(_show_menu(_menu_rows()))


# ═══ the widget ═══════════════════════════════════════════════════════════
class NetworkButton(base.BackgroundPoll):
    """Link state in the bar: 󰤨 CaffeiN

    BackgroundPoll rather than InLoopPollText: every reading here is an nmcli
    subprocess, and this base runs poll() in an executor instead of on the
    event loop, so a slow or hung nmcli stalls the readout and nothing else.
    """

    defaults: ClassVar = [
        ("show_name", False, "Also show the connection name beside the glyph."),
        ("max_chars", 14, "Truncate that name past this many characters."),
    ]

    def __init__(self, **config):
        base.BackgroundPoll.__init__(self, "", **config)
        self.add_defaults(NetworkButton.defaults)
        self.add_callbacks(
            {
                "Button1": network_menu,
                "Button3": _settings,
            }
        )

    @expose_command()
    def open_menu(self):
        """Open the network menu, or dismiss it if it is already up."""
        network_menu()

    def poll(self):
        kind, name, signal, _device = _link()
        if kind == "ethernet":
            self.foreground = C.fg_normal
            return self._label(G.ethernet, name)
        if kind == "wifi":
            self.foreground = C.fg_normal
            return self._label(_signal_glyph(signal), name)
        if kind == "off":
            self.foreground = C.fg_dim
            return self._label(G.wifi_off, "Wi-Fi off")
        # Radio up and nothing joined. Orange rather than dim: the radio being
        # off is a state you chose, but this one you probably did not.
        self.foreground = C.fg_orange
        return self._label(G.wifi_alert, "Offline")

    def _label(self, glyph, name):
        """The glyph alone by default - the four glyphs already say which
        state this is, and the SSID is one click away in the menu, where it
        carries a check mark. show_name=True puts it back on the bar."""
        if not self.show_name or not name:
            return glyph
        if len(name) > self.max_chars:
            name = name[: self.max_chars - 1] + "…"
        return f"{glyph} {name}"
