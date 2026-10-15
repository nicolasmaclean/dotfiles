import QtQuick
import Quickshell
import Quickshell.Services.SystemTray
import Quickshell.Widgets

import qs

Item {
  id: root
  required property SystemTrayItem modelData

  visible: root.modelData != null
  implicitWidth: Theme.trayIconSize
  implicitHeight: Theme.trayIconSize + 8

  IconImage {
    id: icon

    source: root.modelData?.icon ?? ""
    anchors.fill: parent

    // handle clicks
    TapHandler {
      acceptedButtons: Qt.LeftButton
      onTapped: root.modelData.activate()
    }

    TapHandler {
      acceptedButtons: Qt.RightButton
      onTapped: {
        if (root.modelData.hasMenu) {
          menuAnchor.open()
        }
      }
    }

    QsMenuAnchor {
      id: menuAnchor
      menu: root.modelData?.menu
      anchor {
        item: icon
        edges: Edges.Bottom
      }
    }

    // swap cursor on hover
    HoverHandler {
      cursorShape: Qt.PointingHandCursor
    }
  }
}
