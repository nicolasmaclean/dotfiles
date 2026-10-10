pragma Singleton

import QtQuick
import Quickshell

Singleton {
  id: root

  readonly property var actions: [
    {
      "label": "Shutdown",
      "icon": "󰐥",
      "run": () => {
        return Quickshell.execDetached(["systemctl", "poweroff"])
      }
    },
    {
      "label": "Reboot",
      "icon": "󰜉",
      "run": () => {
        return Quickshell.execDetached(["systemctl", "reboot"])
      }
    },
    {
      "label": "Logout",
      "icon": "󰍃",
      "run": () => {
        return Quickshell.execDetached(["uwsm", "stop"])
      }
    },
    {
      "label": "Lock",
      "icon": "󰌾",
      "run": () => {
        return Quickshell.execDetached(["loginctl", "lock-session"])
      }
    }
  ]
}
