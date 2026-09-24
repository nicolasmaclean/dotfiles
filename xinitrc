#!/bin/sh
# Used only by startx/xinit. A display manager ignores this file entirely - it
# runs /usr/share/xsessions/qtile.desktop instead, which is rendered from
# qtile/qtile.desktop.j2 and points at the same launcher.
#
# Symlinked to ~/.xinitrc. The launcher lives in /usr/local/bin rather than
# ~/.local/bin so the greeter (running as its own user) can stat it with the
# home directory at mode 700 - see qtile/qtile.desktop.j2.
exec /usr/local/bin/qtile-session
