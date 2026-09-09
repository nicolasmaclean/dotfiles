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
