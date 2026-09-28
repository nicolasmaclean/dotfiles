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
    model: ScriptModel {
      values: Hyprland.workspaces.values.filter(w => w.monitor?.name === root.screen.name)
    }

    orientation: ListView.Horizontal
    interactive: false

    spacing: 4
    implicitWidth: contentWidth
    implicitHeight: contentItem.childrenRect.height

    delegate: Rectangle {
      id: workspace
      required property HyprlandWorkspace modelData

      property bool fresh: true
      Timer {
        running: true
        interval: 100
        onTriggered: workspace.fresh = false
      }

      onImplicitWidthChanged: console.log(name, "implicitWidth", implicitWidth, "fresh", fresh)

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
      id: displaced

      NumberAnimation {
        property: "x"
        duration: displaced.ViewTransition.item?.fresh ? 0 : 200
        easing.type: Easing.OutCubic
      }

      ScriptAction {
        script: console.log("displaced", displaced.ViewTransition.item.name)
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
