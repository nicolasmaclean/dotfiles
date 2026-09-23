# qtile → Hyprland: features to recreate

## Session / startup
- [ ] Session entry for the display manager + launcher script (replaces `qtile/session/qtile-session`, `qtile.desktop.j2`)
- [ ] Export env to systemd/dbus: `QT_QPA_PLATFORMTHEME=gtk3`, `GTK_IM_MODULE`/`QT_IM_MODULE`/`XMODIFIERS=ibus`
- [ ] Session target that starts/stops these user services: dunst, flameshot (or Wayland replacement), ibus, polkit-gnome agent, Proton VPN (`--start-minimized`), 1Password (`--silent`). picom is not needed.
- [ ] Monitor layout on cnick: HDMI-1 on the left rotated to portrait at 0x0, DP-1 in the middle as primary at 1080x0, HDMI-0 on the right at 3000x0, all top-aligned
- [ ] Wallpaper on every screen from `wallpapers/`, with a solid bar colour as fallback
- [ ] Hotplug: a bar appears on a newly connected monitor
- [ ] Ansible role wiring (the `hyprland` role, plus the display-manager entry)

## Workspaces
- [ ] 5 workspaces (1–5), shared across monitors in qtile's way: each monitor shows any workspace, and switching to one already shown on another monitor swaps it over
- [ ] `alt+N` switches to workspace N; `alt+shift+N` moves the window there and follows it

## Layout (TabbedColumns)
- [ ] At most 2 columns; the next window stacks into the current column
- [ ] Stacked columns show a tab strip, one tab per window with its title
- [ ] Portrait monitor: columns become stacked rows
- [ ] Alternative layouts to cycle through with `alt+Tab`: plain even columns, then max
- [ ] 4px gaps (between windows and at screen edges), 2px borders; focused, unfocused and stacked windows each get their own border colour
- [ ] Floating rules: flameshot, gsimplecal, pinentry, ssh-askpass, git dialogs (confirmreset, makebranch, maketag, branchdialog), plus the usual dialogs

## Keybindings (mod = Alt)
- [ ] `h/l`: move focus left/right, crossing to the neighbouring monitor at the edge (always crosses on the portrait monitor)
- [ ] `j/k`: move focus down/up; `space`: focus the next window
- [ ] `shift+hjkl`: move the window; `ctrl+hjkl`: grow it; `n`: reset sizes
- [ ] `shift+s`: stack/unstack the column
- [ ] `Return`: alacritty; `r`: `rofi -show drun`; `shift+r`: rofi with `-drun-show-actions`
- [ ] `ctrl+a`: run ansible-playbook for this host in a terminal
- [ ] `Tab`: next layout; `w`: close window; `f`: fullscreen; `t`: toggle floating
- [ ] `d`: toggle the bar (overrides the per-layout default)
- [ ] `shift+space`: cycle the ibus engine (US ↔ libpinyin)
- [ ] `ctrl+r`: reload config; `ctrl+q`: quit the session
- [ ] Media keys: volume up/down/mute and mic mute (wpctl); brightness up/down (brightnessctl `-e4`, minimum 10%, dunst progress bar); play/pause/next/prev
- [ ] `Print`: region screenshot with annotation, copied to the clipboard; `shift+Print`: full-screen screenshot to the clipboard
- [ ] Mouse, with **Super** (not Alt): drag with left button moves, drag with right button resizes, middle click raises

## Behaviour
- [ ] Focus follows the mouse; clicking doesn't raise; the cursor doesn't warp
- [ ] Floating windows stay above tiled ones
- [ ] Apps that ask for fullscreen get it; activation requests use a "smart" focus policy
- [ ] Bar hides automatically in the max layout
- [ ] Active monitor indicator: 2px purple stripe along the top of that monitor's bar

## Bar (waybar or similar)
- [ ] Pill-shaped: a gutter on the top, left and right; flat opaque background; square ends; dim thin separators; theme colours and fonts from `qtile/theme.py`
- [ ] Per-monitor contents:
  - **Middle (DP-1):** clock, trays, volume, network, input source, separator, workspaces, battery, power
  - **Left (HDMI-1):** CPU temperature, CPU %, workspaces
  - **Right (HDMI-0):** workspaces, now playing
- [ ] Workspace indicator: blue = shown on this monitor, white = shown on another monitor, grey = not shown; urgent workspaces get a border
- [ ] Clock `%b %d, %I:%M:%S %p`: click opens gsimplecal, scroll changes the month, and the popup must sit above everything
- [ ] Tray: StatusNotifierItem (Proton VPN, Discord, 1Password) with a right-click menu; hide Spotify's item
- [ ] Volume: icon by level; click mutes; scroll changes it by 5% (capped at 100%); right click opens an output-device menu (from `wpctl status`)
- [ ] Network: icon; click opens a Wi-Fi menu (nmcli, rescans in the background, up to 8 SSIDs)
- [ ] Input source label: US/CN from ibus; ibus's own tray icon stays hidden
- [ ] CPU temperature: auto-detected sensor, orange above 75°
- [ ] CPU %: fixed width, coloured at 65% and 85%
- [ ] Battery (only when there is one): must pick the real battery, not the mouse's; glyphs; red below 15%
- [ ] Power button: menu with logout, reboot and poweroff, each asking for confirmation first
- [ ] Now playing: Spotify over MPRIS, green when playing and dim when paused, cut to 50 chars. When nothing plays locally, fall back to the Spotify Web API (`spotify_web.py`/`spotify_auth.py`) and show a glyph for the device it's playing on

## Popups / keyboard
- [ ] Popup menus respond only to arrows, Enter, Tab and Escape (bare letters do nothing); clicking outside closes them

## Other
- [ ] Per-host detection (battery, backlight, thermal sensor, wallpaper) with env/JSON overrides, like `qtile/hardware.py`
- [ ] Java apps need a workaround (qtile sets `wmname = "LG3D"`); probably unnecessary on Wayland/XWayland
- [ ] A nested/test mode that doesn't start or stop the real session's services (`bin/qtile-nested`)
