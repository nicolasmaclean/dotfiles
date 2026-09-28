pragma Singleton

import Quickshell

Singleton {
  readonly property var wifitui: ["uwsm", "app", "--", "alacritty", "--class", "nmtui", "-e", "nmtui", "connect"]
  readonly property var bluetui: ["uwsm", "app", "--", "alacritty", "--class", "bluetui", "-e", "bluetui", "-c", Quickshell.env("HOME") + "/dotfiles/hypr/bluetui/config.toml"]
  readonly property var calendar: ["uwsm", "app", "--", "gsimplecal"]

  function icon(appId): string {
    if (!appId)
      return fallbackIcon

    let key = appId.toLowerCase().replace(/_status_icon_\d+$/, "")
    key = aliases[key] ?? key

    if (icons[key])
      return icons[key]

    for (const prefix in prefixes) {
      if (key.startsWith(prefix))
        return icons[prefixes[prefix]] ?? fallbackIcon
    }

    return fallbackIcon
  }

  readonly property string fallbackIcon: String.fromCodePoint(0xf0614) // md-application_outline

  readonly property var prefixes: ({
      "steam_app_": "steam"
    })
  readonly property var aliases: ({
      "spotify-client": "spotify"
    })

  // keys are lowercased window classes / app ids (check with `hyprctl clients | grep class`)
  readonly property var icons: ({
      // browsers
      "firefox": String.fromCodePoint(0xf0239) // md-firefox
      ,
      "google-chrome": String.fromCodePoint(0xf02af) // md-google_chrome

      ,

      // terminal + custom-class TUIs
      "alacritty": String.fromCodePoint(0xf018d) // md-console
      ,
      "nmtui": String.fromCodePoint(0xf05a9) // md-wifi
      ,
      "bluetui": String.fromCodePoint(0xf00af) // md-bluetooth
      ,
      "gsimplecal": String.fromCodePoint(0xf00ed) // md-calendar

      ,

      // chat + mail
      "discord": String.fromCodePoint(0xf066f) // md-discord
      ,
      "slack": String.fromCodePoint(0xf04b1) // md-slack
      ,
      "signal": String.fromCodePoint(0xf0b79) // md-chat (no Signal logo in the font)
      ,
      "mailspring": String.fromCodePoint(0xf01f0) // md-email_outline

      ,

      // dev
      "code": String.fromCodePoint(0xf0a1e) // md-microsoft_visual_studio_code
      ,
      "gitkraken": String.fromCodePoint(0xf2ac) // fa-gitkraken
      ,
      "org.gnome.meld": String.fromCodePoint(0xf08aa) // md-file_compare
      ,
      "unityhub": String.fromCodePoint(0xf06af) // md-unity

      ,

      // media
      "spotify": String.fromCodePoint(0xf04c7) // md-spotify
      ,
      "vlc": String.fromCodePoint(0xf057c) // md-vlc
      ,
      "com.obsproject.studio": String.fromCodePoint(0xf044b) // md-record_rec
      ,
      "obs": String.fromCodePoint(0xf044b) // md-record_rec (X11 class)
      ,
      "org.flameshot.flameshot": String.fromCodePoint(0xf0e51) // md-monitor_screenshot
      ,
      "flameshot": String.fromCodePoint(0xf0e51) // md-monitor_screenshot
      ,
      "org.pulseaudio.pavucontrol": String.fromCodePoint(0xf057e) // md-volume_high

      ,

      // games
      "steam": String.fromCodePoint(0xf04d3) // md-steam
      ,
      "net.lutris.lutris": String.fromCodePoint(0xf0297) // md-gamepad_variant

      ,

      // system + utilities
      "org.kde.dolphin": String.fromCodePoint(0xf024b) // md-folder
      ,
      "1password": String.fromCodePoint(0xf0881) // md-onepassword
      ,
      "protonvpn-app": String.fromCodePoint(0xf0582) // md-vpn
      ,
      "onlyoffice": String.fromCodePoint(0xf0219) // md-file_document
      ,
      "org.cachyos.hello": String.fromCodePoint(0xf385) // linux-cachyos
    })
}
