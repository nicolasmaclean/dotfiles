pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Services.SystemTray

Singleton {
  id: root

  readonly property var ids: ({
      signal: "signal",
      one_password: "1password",
      mailspring: "mailspring",
      discord: "discord",
      proton_vpn: "proton.vpn.app.gtk",
      arch_update: "arch-update"
    })

  function getItem(prefix): SystemTrayItem {
    return SystemTray.items.values.find(i => i.id.toLowerCase().startsWith(prefix)) ?? null
  }

  function has(id): bool {
    return Object.values(root.ids).some(p => id.toLowerCase().startsWith(p))
  }
}
