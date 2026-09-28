import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.SystemTray
import Quickshell.Widgets

import qs
import qs.services

Repeater {
  model: ScriptModel {
    values: [...SystemTray.items.values].sort((a, b) => TrayOrder.rank(a.id) - TrayOrder.rank(b.id))
  }

  delegate: IconImage {
    id: icon
    required property SystemTrayItem modelData

    source: modelData.icon
    implicitSize: Theme.widgetIconSize

    // handle clicks
    TapHandler {
      acceptedButtons: Qt.LeftButton
      onTapped: icon.modelData.activate()
    }

    TapHandler {
      acceptedButtons: Qt.RightButton
      onTapped: {
        if (icon.modelData.hasMenu) {
          menuAnchor.open()
        }
      }
    }

    QsMenuAnchor {
      id: menuAnchor
      menu: icon.modelData.menu
      anchor {
        item: icon
        edges: Edges.Bottom
      }
    }

    // swap cursor on hover
    HoverHandler {
      cursorShape: Qt.PointingHandCursor
    }

    // drag to reorder tray icons
    Drag.active: dragHandler.active
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: height / 2
    z: dragHandler.active ? 1 : 0

    DragHandler {
      id: dragHandler
      yAxis.enabled: false
      onActiveChanged: {
        if (dragHandler.active === false)
          TrayOrder.commit()
      }
    }

    DropArea {
      anchors.fill: parent
      onEntered: ev => {
        if (ev.source === icon)
          return
        TrayOrder.move(ev.source.modelData.id, icon.modelData.id)
      }
    }
  }
}
