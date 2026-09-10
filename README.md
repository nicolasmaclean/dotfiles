# My dotfiles!

You're welcome to take peek or try out my dotfiles/pc setup. I have some old instructions for how to mealpiece each software, but I'm switching to having my setup configured with ansible so that documentation may be stale. In the future, I'll improve documentation for how to grab parts of the ansible setup, maybe. 

## Config fresh CachyOS install with ansible/

1. Install CachyOS to your machine or VM
   - no desktop environment
   - name the pc 'cnick' for desktop or 'unick' for laptop (or add a new ansible/inventory host)
   - bootloader doesn't matter
2. Run the bootstrap as yourself (NOT with sudo), it will call sudo and prompt for password later:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasmaclean/dotfiles/main/ansible/bootstrap.sh | bash
```

    - this will install ansible, clone this repo to `~/dotfiles`, and run ansbile.
    - it will run sudo and ask for your password once.
    - if you are overwriting your setup, consider a dry run `ansible/bootstrap.sh --check --diff`.
3. The run pauses once: at the Spotify prompt, either follow the four
   steps it prints or press ENTER to skip — the widget degrades to MPRIS-only.
4. Reboot. LightDM comes up; pick the **qtile** session.

Re-runs are idempotent.

Individual roles: `cd ansible && ansible-playbook site.yml --limit "$(hostname)" --ask-become-pass --tags qtile`.

---

## Alacritty

`ln -s ~/dotfiles/alacritty.toml ~/.config/alacritty/alacritty.toml`

## Qtile

`ln -s ~/dotfiles/qtile ~/.config/qtile`

Three more the install script does not link, because nothing in the session
starts them from here — the compositor unit, the launcher and the power menu
find them at the XDG paths:

```
ln -s ~/dotfiles/picom ~/.config/picom
ln -s ~/dotfiles/rofi  ~/.config/rofi
ln -s ~/dotfiles/bin/qtile-nested     ~/.local/bin/qtile-nested
ln -s ~/dotfiles/bin/rofi-power-menu  ~/.local/bin/rofi-power-menu
```

The session expects four packages — `install-session.sh`'s own header lists
them, and the Print key and the bar clock are dead without the last two:
`sudo apt install policykit-1-gnome dunst flameshot gsimplecal`.

Then, as yourself — *not* with sudo, it calls sudo for the two steps that need it:

`~/.config/qtile/install-session.sh`

That installs the launcher (`~/.local/bin/qtile-session`), the greeter's session
entry (rendered from `qtile/qtile.desktop.j2` — a `.desktop` file cannot expand
`$HOME`, so the launcher path is substituted in), the `systemd --user` units the
session is made of (`qtile-session.target`, `picom.service`, `protonvpn.service`,
`polkit-agent.service`, `dunst.service`, `flameshot.service`), the `~/.config`
symlinks for dunst, flameshot and gsimplecal, and the ibus input sources the
bar's keyboard widget cycles through. Pass `--autologin` to skip the greeter.

For `startx`/`xinit` rather than a greeter: `ln -s ~/dotfiles/xinitrc ~/.xinitrc`.

The one path still written in absolute is `flameshot/flameshot.ini`'s `savePath`.
Flameshot expands neither `$HOME` nor `~` in it — verified: with either, a
capture saves nothing at all — so it stays absolute and Ansible sets it per host.

## What this box has

`qtile/hardware.py` works out at runtime what `config.py` used to hardcode:
which battery, which backlight, which temperature sensor, which wallpaper, and
how many screens. That is what lets one config serve a laptop and a desktop.

    python3 ~/.config/qtile/hardware.py    # print what it detected

Nothing in it can raise — every probe is wrapped in `@safe(fallback)`, because a
config exception drops qtile into its own `default_config` (mod4 bindings, no
bar, no groups), which is a dead session on a machine you may have no other way
into.

Each fact can be overridden, highest precedence first: `QTILE_<NAME>` in the
environment, then `~/.config/qtile-host.json` (optional, normally absent), then
detection. An **empty** environment value is a real answer meaning "this box has
none", which is what makes the desktop testable from the laptop:

    QTILE_BATTERY= QTILE_THERMAL= qtile-nested   # the batteryless desktop path
    QTILE_FAKE_OUTPUTS=3 qtile-nested            # three screens on one panel

Missing hardware removes widgets rather than showing broken ones: no battery
means no battery widget *and* no orphaned separator beside it, and no usable CPU
sensor means no thermometer glyph either. Screens come from `generate_screens`,
so a monitor plugged in mid-session grows a bar onto it; the Screen objects are
cached by index and re-handed, because rebuilding them silently drops the
systray and leaks a bar window on every replug.

## Notifications

`dunst/dunstrc`, symlinked to `~/.config/dunst` by `install-session.sh` and run
by `dunst.service`. Nothing else in a bare qtile session answers
`org.freedesktop.Notifications`, so without it every `notify-send` fails.

Ported from a dunstrc written for dunst 1.12; noble ships 1.9.2, and the six
settings that only exist in the newer one are marked inline in the file.

    notify-send "hello" "body text"          # test it
    dunstctl set-paused toggle               # do-not-disturb, all-or-nothing on 1.9.2
    dunstctl history-pop                      # bring the last one back

## Calendar

Clicking the bar clock opens `gsimplecal`; scrolling on it pages through months.
`gsimplecal/config`, symlinked to `~/.config/gsimplecal` by
`install-session.sh`.

It is a separate program rather than another `qtile_extras` popup (as the power
and network menus are) because it already toggles itself — running it a second
time kills the first, so one `lazy.spawn` on the clock both opens and closes it
— and `prev_month`/`next_month` start it if it is not up, which is what lets a
scroll on the clock open the calendar already moved by a month.

Two things about the placement are worth knowing before touching the offsets.
It positions itself on the pointer, so it lands under the clock you clicked
without qtile placing it; and because GTK clamps the window into the monitor
*before* applying `mainwindow_yoffset`, that offset ends up being the window's
absolute distance from the top of the screen rather than a nudge. The file
explains both inline.

    gsimplecal                  # toggle it
    gsimplecal next_month       # open it, or page a month if already open

The month header sits in the same band as a `TabbedColumns` tab strip, and a
tab strip is an Internal window, so it paints over the popup. `config.py`'s
`_raise_calendar_popup` hook raises the popup once it is managed.

## Now playing

The bar's track readout reads Spotify's MPRIS interface over dbus, which only
ever knows about players running on this machine. Playing from the phone left
it blank, so it falls back to Spotify's Web API — that answers for the
*account*, and so covers every device signed into it. MPRIS stays the primary
source wherever it has an answer: it is pushed and instant, where the API is
polled every ten seconds.

Whichever source is actually *playing* wins, rather than local-always. The
desktop client stays on the bus when you start playing from the phone — paused,
still holding the last track it played — so preferring it there would leave the
bar naming a song that stopped an hour ago.

The fallback needs credentials, which are deliberately not in this repo. Without
them the widget logs one line and carries on as a plain MPRIS readout.

1. At <https://developer.spotify.com/dashboard>, **Create app**. Any name; tick
   **Web API**; set the redirect URI to `http://127.0.0.1:8888/callback` and
   click **Add**. It has to be the loopback IP — Spotify rejects `localhost` as
   a hostname. Leave the app in development mode: that caps it at 25 authorised
   users and you are already one of them as the owner.
2. Put the client ID and secret in `~/.config/qtile-spotify/credentials.json`
   (mode 0600, alongside the `redirect_uri` above).
3. Run the login once. It opens a browser, takes the approval, and writes a
   refresh token to `~/.config/qtile-spotify/token.json`:

        python3 ~/.config/qtile/spotify_auth.py

The refresh token does not expire, so step 3 is a one-off — the widget trades it
for an hour-long access token as it goes and rewrites the file atomically, a
torn write there being the one thing that would send you back to the browser.
Re-run it if you ever revoke the app's access or change the account password.

The poll is well inside Spotify's rate limit, which is a rolling 30-second
window. A failed request means *unknown*, not *stopped*, so the last known track
is held for three polls before the bar clears — otherwise a flaky link would
flicker it every ten seconds.
