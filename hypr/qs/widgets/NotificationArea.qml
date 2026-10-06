import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Hyprland

import qs
import qs.services

ListView {
  id: layout

  model: ScriptModel {
    values: [...Notify.notifications.values]
  }
  delegate: NotificationCard {
    width: ListView.view.width
  }

  implicitWidth: Theme.notificationWidth
  spacing: 5
  interactive: false

  // animations
  add: Transition {
    NumberAnimation {
      property: "opacity"
      from: 0
      to: 1
    }
  }

  remove: Transition {
    NumberAnimation {
      property: "opacity"
      to: 0
      duration: 200
    }
  }

  displaced: Transition {
    NumberAnimation {
      property: "y"
    }
  }
}
