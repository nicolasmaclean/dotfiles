import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.SystemTray
import Quickshell.Widgets

import qs

Repeater {
  model: SystemTray.items

  delegate: IconImage {
    id: icon
    required property SystemTrayItem modelData

    source: modelData.icon
    implicitSize: Theme.widgetIconSize

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

    HoverHandler {
      cursorShape: Qt.PointingHandCursor
    }

    QsMenuAnchor {
      id: menuAnchor
      menu: icon.modelData.menu
      anchor {
        item: icon
        edges: Edges.Bottom
      }
    }
  }
}
