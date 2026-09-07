#!/bin/bash
# Installs the whole Qtile session, so a fresh box needs nothing but this repo:
#   ~/.local/bin/qtile-session        the launcher GDM execs
#   /usr/share/xsessions/qtile.desktop the entry GDM lists
#   ~/.config/systemd/user/*           the units the session is made of
#   ~/.config/dunst                    symlink to this repo's dunstrc
#   ~/.config/flameshot                symlink to this repo's flameshot.ini
#   ibus                               the input sources the bar's widget cycles
#
# Expects policykit-1-gnome, dunst and flameshot to be installed - the first
# ships the authentication agent polkit-agent.service runs, the second is the
# session's notification daemon, the third is what the Print key drives:
#   sudo apt install policykit-1-gnome dunst flameshot
#
# Run as yourself, NOT with sudo. The user units and the gsettings values below
# belong to your own session - run as root they would land in root's systemd
# manager and root's dconf, where nothing of yours would ever read them. The
# two steps that genuinely need root call sudo themselves, so expect one
# password prompt.
#
#   ~/.config/qtile/install-session.sh [--autologin]

set -euo pipefail

[ "$(id -u)" -ne 0 ] || {
    echo "run me as yourself, not with sudo - see the note at the top" >&2
    exit 1
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNITS="$HOME/.config/systemd/user"

# ═══ the session entry, and the launcher it points at ════════════════════
# The launcher is what publishes DISPLAY to systemd --user and dbus; without
# it the units below would start with no display to draw on.
install -Dm755 "$HERE/session/qtile-session" "$HOME/.local/bin/qtile-session"
echo "installed ~/.local/bin/qtile-session"

sudo install -Dm644 "$HERE/qtile.desktop" /usr/share/xsessions/qtile.desktop
echo "installed /usr/share/xsessions/qtile.desktop"

# ═══ the session's user units ════════════════════════════════════════════
# qtile-session.target is the whole session lifetime in one place: config.py's
# startup_once hook starts it and its shutdown hook stops it, and every service
# here is WantedBy that target, so they come and go with qtile.
install -Dm644 "$HERE/session/qtile-session.target" "$UNITS/qtile-session.target"
install -Dm644 "$HERE/session/picom.service" "$UNITS/picom.service"
install -Dm644 "$HERE/session/protonvpn.service" "$UNITS/protonvpn.service"
# polkit-agent is what lets anything in the session ask for a password. Without
# it polkit can only answer "Authorization requires interaction", and GUI apps
# report that as their own vague failure - App Center calls it "unknown error".
install -Dm644 "$HERE/session/polkit-agent.service" "$UNITS/polkit-agent.service"
# dunst is what answers org.freedesktop.Notifications. Nothing in a bare qtile
# session does, and every notify-send - plus every app that notifies over dbus
# - then fails with "No notification daemon". This unit deliberately shadows
# the one the dunst package ships in /usr/lib/systemd/user.
install -Dm644 "$HERE/session/dunst.service" "$UNITS/dunst.service"
# flameshot has to be resident for the Print key to be able to copy a shot at
# all - the unit itself explains why.
install -Dm644 "$HERE/session/flameshot.service" "$UNITS/flameshot.service"
systemctl --user daemon-reload
systemctl --user enable picom.service protonvpn.service polkit-agent.service \
    dunst.service flameshot.service >/dev/null
echo "installed and enabled: qtile-session.target, picom.service, protonvpn.service,"
echo "                       polkit-agent.service, dunst.service, flameshot.service"

# nm-applet is deliberately not shipped: network.py draws the indicator now,
# and running the applet as well would dock a second one in the tray. This
# only fires on a box still carrying the unit from before that change.
if [ -e "$UNITS/nm-applet.service" ]; then
    systemctl --user disable --now nm-applet.service >/dev/null 2>&1 || true
    echo "disabled the leftover nm-applet.service (network.py replaces it)"
fi

# ═══ dunst's config ══════════════════════════════════════════════════════
# It has to sit at the XDG default path: dbus activation runs a plain
# `dunst` with no way to pass -conf, so a config anywhere else would be read
# by the unit and ignored by every other route into the daemon. Symlinked, not
# copied, so editing the repo is editing the live config.
DUNSTCFG="$HOME/.config/dunst"
if [ -L "$DUNSTCFG" ] || [ ! -e "$DUNSTCFG" ]; then
    ln -sfn "$(dirname "$HERE")/dunst" "$DUNSTCFG"
    echo "linked ~/.config/dunst -> $(dirname "$HERE")/dunst"
else
    echo "warning: ~/.config/dunst is a real directory - left alone. Move it" >&2
    echo "         aside and rerun to pick up this repo's dunstrc." >&2
fi

# ═══ flameshot's config ══════════════════════════════════════════════════
# Same reasoning as dunst: flameshot reads ~/.config/flameshot/flameshot.ini
# and takes no --config flag, so the file has to sit at the XDG path. Note that
# flameshot *rewrites* this file when a setting is changed from its own UI, and
# through the symlink that edits the repo - which is the intent, but it does
# drop the comments.
FLAMECFG="$HOME/.config/flameshot"
if [ -L "$FLAMECFG" ] || [ ! -e "$FLAMECFG" ]; then
    ln -sfn "$(dirname "$HERE")/flameshot" "$FLAMECFG"
    echo "linked ~/.config/flameshot -> $(dirname "$HERE")/flameshot"
else
    echo "warning: ~/.config/flameshot is a real directory - left alone. Move" >&2
    echo "         it aside and rerun to pick up this repo's flameshot.ini." >&2
fi

# ═══ input sources ═══════════════════════════════════════════════════════
# preload-engines is the list ibus honours outside a GNOME session, and it is
# what widgets.py's KeyboardLayout cycles through. GNOME's own
# org.gnome.desktop.input-sources is NOT read here, so an engine missing from
# this key cannot be selected at all - which is why a bare ibus install can
# list a Chinese source that never actually works.
gsettings set org.freedesktop.ibus.general preload-engines "['xkb:us::eng', 'libpinyin']"

# The bar draws its own input-source indicator, so ibus's GTK tray icon would
# be a second one saying the same thing. Only the icon is hidden: ibus-ui-gtk3
# keeps running, because it also draws the pinyin candidate window.
gsettings set org.freedesktop.ibus.panel show-icon-on-systray false
echo "configured ibus: preload-engines + hidden tray icon"

# ═══ optional: skip the greeter ══════════════════════════════════════════
if [ "${1:-}" = "--autologin" ]; then
    sudo cp -n /etc/gdm3/custom.conf /etc/gdm3/custom.conf.bak || true
    sudo sed -i \
      -e 's/^#\s*AutomaticLoginEnable\s*=.*/AutomaticLoginEnable = true/' \
      -e 's/^#\s*AutomaticLogin\s*=.*/AutomaticLogin = nick/' \
      /etc/gdm3/custom.conf
    echo "enabled GDM autologin for nick (backup: /etc/gdm3/custom.conf.bak)"
    grep -E '^Automatic' /etc/gdm3/custom.conf
fi

echo
echo "done. log out and pick Qtile in GDM, or run set-default-session.sh to"
echo "make it the session autologin lands in."
