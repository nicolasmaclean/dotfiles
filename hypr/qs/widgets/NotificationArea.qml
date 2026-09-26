import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Hyprland

import qs.services

ColumnLayout {
  id: layout

  Repeater {
    model: ScriptModel {
      values: [...Notify.notifications.values]
    }

    Component {
      id: notificationDelegate
      NotificationCard {}
    }
  }
}
