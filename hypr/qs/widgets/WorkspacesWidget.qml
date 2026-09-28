import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Widgets

import qs

RowLayout {
  id: root
  required property ShellScreen screen
  Layout.fillWidth: false

  Repeater {
    model: Hyprland.workspaces
    delegate: RowLayout {
      id: workspace
      required property HyprlandWorkspace modelData
      readonly property bool onThisMonitor: modelData.monitor?.name === root.screen.name
      readonly property bool active: modelData.active
      readonly property var appIds: [...new Set(modelData.toplevels.values.map(t => t.wayland?.appId).filter(id => id))]

      visible: onThisMonitor

      Text {
        text: workspace.modelData.name
        color: Theme.text
      }

      Repeater {
        model: workspace.appIds
        delegate: IconImage {
          required property string modelData

          readonly property string iconName: {
            DesktopEntries.applications.values
            return DesktopEntries.heuristicLookup(modelData)?.icon ?? ""
          }
          source: Quickshell.iconPath(iconName, "application-x-executable")

          implicitSize: Theme.widgetIconSize
        }
      }
    }
  }
}
