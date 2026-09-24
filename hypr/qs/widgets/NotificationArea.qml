import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Hyprland

import qs.services

PanelWindow {
  screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null

  color: "transparent"
  anchors {
    top: true
    right: true
  }

  margins {
    top: 10
    right: 18
  }

  // fit notification area to the notifications its showing
  implicitWidth: layout.implicitWidth
  implicitHeight: layout.implicitHeight

  ColumnLayout {
    id: layout

    Repeater {
      model: ScriptModel {
        values: [...Notify.notifications.values].reverse()
      }

      Component {
        id: notificationDelegate
        NotificationCard { }
      }
    }
  }
}

