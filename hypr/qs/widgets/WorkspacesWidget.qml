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

      // change workspace on click
      TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: workspace.modelData?.activate()
      }

      // close workspace on right click
      TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: {
          for (const t of workspace.modelData?.toplevels.values ?? [])
            Hyprland.dispatch(`hl.dsp.window.close({ window = "address:0x${t.address}" })`)
        }
      }

      HoverHandler {
        cursorShape: Qt.PointingHandCursor
      }

      property real lift: workspace.active ? 2 : 0
      Behavior on lift {
        NumberAnimation {
          duration: 80
        }
      }
      transform: Translate {
        y: -workspace.lift
        x: -workspace.lift
      }

      Rectangle {
        z: -1
        width: parent.width
        height: parent.height
        radius: parent.radius
        color: Qt.darker(parent.color, 1.5)
        y: workspace.lift
        x: workspace.lift
      }

      // formatting
      // color: workspace.active ? MyColors.secondaryContainer : MyColors.tertiaryContainer
      color: MyColors.tertiaryContainer
      readonly property real hPadding: 12
      readonly property real vPadding: 4
      radius: height / 2

      implicitWidth: row.implicitWidth + hPadding * 2
      implicitHeight: row.implicitHeight + vPadding * 2

      // show workspace content (title + app icons)
      RowLayout {
        id: row
        x: workspace.hPadding
        anchors.verticalCenter: parent.verticalCenter

        Text {
          text: workspace.name
          color: workspace.active ? MyColors.oonSecondaryContainer : MyColors.oonTertiaryContainer
        }

        Repeater {
          model: ScriptModel {
            values: workspace.appIds
          }
          delegate: IconImage {
            required property string modelData

            readonly property string iconName: {
              // leave this expression statement, it forces this binding dependency
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

      ListView.onAdd: addAnimation.start()
      ParallelAnimation {
        id: addAnimation
        NumberAnimation {
          target: workspace
          property: "opacity"
          from: 0
          to: 1
          duration: 100
        }
        NumberAnimation {
          target: workspace
          property: "scale"
          from: 0.4
          to: 1
          duration: 200
          easing.type: Easing.OutBack
          easing.overshoot: 5
        }
      }

      ListView.onRemove: removeAnimation.start()
      SequentialAnimation {
        id: removeAnimation

        PropertyAction {
          target: workspace
          property: "ListView.delayRemove"
          value: true
        }

        ParallelAnimation {
          NumberAnimation {
            target: workspace
            property: "opacity"
            to: 0
            duration: 150
          }
          NumberAnimation {
            target: workspace
            property: "scale"
            to: 0
            duration: 120
            easing.type: Easing.InBack
          }
        }

        PropertyAction {
          target: workspace
          property: "ListView.delayRemove"
          value: false
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
  }

  Rectangle {
    radius: height / 2
    color: MyColors.tertiaryContainer
    implicitWidth: addButtonText.implicitWidth + 12
    implicitHeight: addButtonText.implicitHeight + 4

    Text {
      id: addButtonText
      text: "+"
      color: MyColors.oonTertiaryContainer
      anchors.centerIn: parent
    }

    TapHandler {
      acceptedButtons: Qt.LeftButton
      onTapped: Hyprland.dispatch(`hl.dsp.focus({ workspace = "emptym" })`)
    }

    HoverHandler {
      cursorShape: Qt.PointingHandCursor
    }
  }
}
