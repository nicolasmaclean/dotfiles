# My dotfiles!

## Alacritty

`ln -s ~/dotfiles/alacritty.toml ~/.config/alacritty/alacritty.toml`

Must be this path, not `~/.alacritty.toml`. Alacritty checks
`~/.config/alacritty/alacritty.toml` first and stops at the first hit, so a file
there shadows the home-directory one completely rather than merging with it.

## Qtile

`ln -s ~/dotfiles/qtile ~/.config/qtile`

The session expects two packages: `sudo apt install policykit-1-gnome dunst`.

Then, as yourself — *not* with sudo, it calls sudo for the two steps that need it:

`~/.config/qtile/install-session.sh`

That installs the launcher (`~/.local/bin/qtile-session`), the GDM session entry,
the `systemd --user` units the session is made of (`qtile-session.target`,
`picom.service`, `protonvpn.service`, `polkit-agent.service`, `dunst.service`),
the `~/.config/dunst` symlink that points dunst at this repo's `dunstrc`, and the
ibus input sources the bar's keyboard widget cycles through. Pass `--autologin` to skip the greeter; run `set-default-session.sh` to
make autologin land in qtile rather than GNOME.

## Notifications

`dunst/dunstrc`, symlinked to `~/.config/dunst` by `install-session.sh` and run
by `dunst.service`. Nothing else in a bare qtile session answers
`org.freedesktop.Notifications`, so without it every `notify-send` fails.

Ported from a dunstrc written for dunst 1.12; noble ships 1.9.2, and the six
settings that only exist in the newer one are marked inline in the file.

    notify-send "hello" "body text"          # test it
    dunstctl set-paused toggle               # do-not-disturb, all-or-nothing on 1.9.2
    dunstctl history-pop                      # bring the last one back
