pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.SystemTray

Singleton {
  id: root
  property list<string> order: []

  function rank(itemId): int {
    let i = order.indexOf(itemId)
    return i === -1 ? order.length : i
  }

  function move(draggedId, targetId): void {
    if (draggedId === targetId)
      return

    // pick up new tray items if they are available
    const ids = [...order]
    for (const item of SystemTray.items.values) {
      if (!ids.includes(item.id))
        ids.push(item.id)
    }

    const from = ids.indexOf(draggedId)
    const to = ids.indexOf(targetId)
    if (from === -1 || to === -1)
      return
    ids.splice(from, 1)
    ids.splice(to, 0, draggedId)
    order = ids
  }

  function commit(): void {
    json.order = root.order
    file.writeAdapter()
  }

  FileView {
    id: file
    path: Quickshell.statePath("tray-order.json")

    onLoaded: root.order = json.order
    onLoadFailed: err => {
      if (err === FileViewError.FileNotFound)
        writeAdapter()
    }

    JsonAdapter {
      id: json
      property list<string> order: []
    }
  }
}
