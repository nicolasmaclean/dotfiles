pragma Singleton

import Quickshell

Singleton {
  readonly property var wifitui: ["uwsm", "app", "--", "alacritty", "--class", "nmtui", "-e", "nmtui", "connect"]
  readonly property var bluetui: ["uwsm", "app", "--", "alacritty", "--class", "bluetui", "-e", "bluetui", "-c", Quickshell.env("HOME") + "/dotfiles/hypr/bluetui/config.toml"]
  readonly property var calendar: ["uwsm", "app", "--", "gsimplecal"]
}
