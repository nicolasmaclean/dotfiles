#!/bin/sh
# Used only by startx/xinit. A display manager ignores this file entirely - it
# runs /usr/share/xsessions/qtile.desktop instead, which is rendered from
# qtile/qtile.desktop.j2 and points at the same launcher.
#
# Symlinked to ~/.xinitrc. $HOME rather than a written-in path: unlike a
# .desktop entry, a shell script can expand it.
exec "$HOME/.local/bin/qtile-session"
