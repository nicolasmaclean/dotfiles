pragma Singleton

import Quickshell
import QtQuick
import Quickshell.Io
import Quickshell.Services.Notifications

Singleton {
  id: root
  property bool dnd: false

  NotificationServer {
    id: server
    keepOnReload: true
    actionsSupported: true
    imageSupported: true
    bodyMarkupSupported: true
    bodyHyperlinksSupported: true
    // "value" is the progress bar hint (notify-send -h int:value:40)
    extraHints: ["value"]

    // do not disturb drops everything but critical notifications
    // (untracked notifications are discarded by the server)
    onNotification: n => {
      if (root.dnd && n.urgency !== NotificationUrgency.Critical)
        return
      n.tracked = true
    }
  }
  property alias notifications: server.trackedNotifications

  function dismissAll() {
    // copy first, dismissing removes from the list being iterated
    for (const n of [...server.trackedNotifications.values])
      n.dismiss()
  }

  // qs --path ~/dotfiles/hypr/qs ipc call notifications <fn>
  IpcHandler {
    target: "notifications"

    function dismissAll(): void {
      root.dismissAll()
    }
    function toggleDnd(): bool {
      root.dnd = !root.dnd
      return root.dnd
    }
    function setDnd(on: bool): void {
      root.dnd = on
    }
    function isDnd(): bool {
      return root.dnd
    }
  }
}
