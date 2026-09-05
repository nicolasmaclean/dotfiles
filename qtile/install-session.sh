#!/bin/bash
# Installs the Qtile session for GDM. Run with: sudo ~/.config/qtile/install-session.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "run me with sudo" >&2; exit 1; }

install -Dm644 /home/nick/.config/qtile/qtile.desktop /usr/share/xsessions/qtile.desktop
echo "installed /usr/share/xsessions/qtile.desktop"

# Optional: log straight into qtile at boot, no greeter.
if [ "${1:-}" = "--autologin" ]; then
    cp -n /etc/gdm3/custom.conf /etc/gdm3/custom.conf.bak
    sed -i \
      -e 's/^#\s*AutomaticLoginEnable\s*=.*/AutomaticLoginEnable = true/' \
      -e 's/^#\s*AutomaticLogin\s*=.*/AutomaticLogin = nick/' \
      /etc/gdm3/custom.conf
    echo "enabled GDM autologin for nick (backup: /etc/gdm3/custom.conf.bak)"
    grep -E '^Automatic' /etc/gdm3/custom.conf
fi
