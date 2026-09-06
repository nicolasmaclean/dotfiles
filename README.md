# My dotfiles!

## Alacritty

`ln -s ~/dotfiles/alacritty.toml ~/.alacritty.toml`

## Qtile

`ln -s ~/dotfiles/qtile ~/.config/qtile`

Then, as yourself — *not* with sudo, it calls sudo for the two steps that need it:

`~/.config/qtile/install-session.sh`

That installs the launcher (`~/.local/bin/qtile-session`), the GDM session entry,
the `systemd --user` units the session is made of (`qtile-session.target`,
`picom.service`), and the ibus input sources the bar's keyboard widget cycles
through. Pass `--autologin` to skip the greeter; run `set-default-session.sh` to
make autologin land in qtile rather than GNOME.
