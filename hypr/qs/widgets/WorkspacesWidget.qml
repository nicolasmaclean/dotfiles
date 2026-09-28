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

  ListView {
    id: workspaces

    readonly property var liveWorkspaces: Hyprland.workspaces.values.filter(w => w.monitor?.name === root.screen.name)
    property var shownWorkspaces: liveWorkspaces
    onLiveWorkspacesChanged: batchTimer.restart()

    Timer {
      id: batchTimer
      interval: 30
      onTriggered: workspaces.shownWorkspaces = workspaces.liveWorkspaces
    }

    model: ScriptModel {
      values: workspaces.shownWorkspaces
    }

    orientation: ListView.Horizontal
    interactive: false

    spacing: 4
    implicitWidth: contentWidth
    implicitHeight: contentItem.childrenRect.height

    Behavior on implicitWidth {
      NumberAnimation {
        duration: 200
        easing.type: Easing.OutCubic
      }
    }

    delegate: Rectangle {
      id: workspace
      required property HyprlandWorkspace modelData

      // during remove animation, these are frozen to prevent null derefence when workspace is destroyed
      property string name: modelData?.name ?? ""
      property bool active: modelData?.active ?? false
      property var appIds: [...new Set(workspace.modelData?.toplevels.values.map(t => t.wayland?.appId).filter(id => id) ?? [])]

      Binding on name {
        when: workspace.modelData
        value: workspace.modelData?.name ?? ""
        restoreMode: Binding.RestoreNone
      }

      Binding on active {
        when: workspace.modelData
        value: workspace.modelData?.active ?? false
        restoreMode: Binding.RestoreNone
      }

      Binding on appIds {
        when: workspace.modelData
        value: [...new Set(workspace.modelData?.toplevels.values.map(t => t.wayland?.appId).filter(id => id) ?? [])]
        restoreMode: Binding.RestoreNone
      }

      color: Theme.accent
      readonly property real hPadding: 12
      readonly property real vPadding: 4
      radius: height / 2

      implicitWidth: row.implicitWidth + hPadding * 2
      implicitHeight: row.implicitHeight + vPadding * 2

      RowLayout {
        id: row
        x: workspace.hPadding
        anchors.verticalCenter: parent.verticalCenter

        Text {
          text: workspace.name
          color: Theme.text
        }

        Repeater {
          model: ScriptModel {
            values: workspace.appIds
          }
          delegate: IconImage {
            required property string modelData

            readonly property string iconName: {
              DesktopEntries.applications.values
              return DesktopEntries.heuristicLookup(modelData)?.icon ?? ""
            }
            source: Quickshell.iconPath(iconName, "application-x-executable")
            implicitSize: Theme.widgetIconSize

            // fade icons in as pill grows
            opacity: 0
            Component.onCompleted: opacity = 1
            Behavior on opacity {
              NumberAnimation {
                duration: 200
              }
            }
          }
        }
      }
      // animate workspace with change (added/remove app icon(s))
      property real animatedWidth: implicitWidth
      width: animatedWidth
      Behavior on animatedWidth {
        NumberAnimation {
          duration: 200
          easing.type: Easing.OutCubic
        }
      }
    }

    // animate workspace add, remove
    displaced: Transition {
      NumberAnimation {
        property: "x"
        duration: 200
        easing.type: Easing.OutCubic
      }

      // if displaced interrupts add, this will make sure opacity is still animated
      NumberAnimation {
        property: "opacity"
        to: 1
        duration: 200
      }
    }

    add: Transition {
      NumberAnimation {
        property: "opacity"
        from: 0
        to: 1
        duration: 150
      }
    }

    remove: Transition {
      NumberAnimation {
        property: "opacity"
        to: 0
        duration: 150
      }
    }
  }
}
