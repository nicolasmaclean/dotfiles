#!/bin/bash
# Make autologin land in Qtile instead of GNOME.
# Run with: sudo ~/.config/qtile/set-default-session.sh [qtile|ubuntu]
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "run me with sudo" >&2; exit 1; }
SESSION="${1:-qtile}"
F=/var/lib/AccountsService/users/nick

[ -f "$F" ] || { printf '[User]\nSession=\nXSession=\n' > "$F"; }
cp -n "$F" "$F.bak" 2>/dev/null || true

if grep -q '^XSession=' "$F"; then
    sed -i "s|^XSession=.*|XSession=$SESSION|" "$F"
else
    sed -i "/^\[User\]/a XSession=$SESSION" "$F"
fi
# GNOME-era key; keep the two consistent.
if grep -q '^Session=' "$F"; then
    sed -i "s|^Session=.*|Session=$SESSION|" "$F"
fi

echo "--- $F now reads ---"; cat "$F"
echo "--- restarting accounts-daemon so GDM picks it up ---"
systemctl restart accounts-daemon
