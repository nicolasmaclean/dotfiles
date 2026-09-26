import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland

import qs

RowLayout {
  id: root
  required property ShellScreen screen

  Repeater {
    model: Hyprland.workspaces
    delegate: Text {
      required property HyprlandWorkspace modelData
      readonly property bool onThisMonitor: modelData.monitor?.name === root.screen.name
      readonly property bool active: modelData.active

      text: modelData.name
      color: Theme.text
      visible: onThisMonitor
    }
  }
}
