pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell

import qs.services

ColumnLayout {
  id: root

  required property var devices
  required property var current
  property string suffix
  property bool expanded: false
  signal picked(var node)

  property var format: n => `${Audio.nodeLabel(n)}: ${Math.round(n.audio.volume * 100)}%`

  Text {
    Layout.fillWidth: true
    horizontalAlignment: Qt.AlignHCenter
    text: root.format(root.current).concat(" ", root.expanded ? "󰅃" : "󰅀")

    TapHandler {
      acceptedButtons: Qt.LeftButton
      onTapped: root.expanded = !root.expanded
    }
  }

  ColumnLayout {
    // visible: root.expanded
    spacing: 2

    Repeater {
      model: ScriptModel {
        values: root.devices.filter(d => d !== root.current)
      }

      delegate: Rectangle {
        id: deviceEntry
        required property var modelData

        Layout.fillWidth: true
        implicitHeight: deviceLabel.implicitHeight + 16
        radius: 12
        color: "transparent"

        Text {
          id: deviceLabel
          anchors.fill: parent
          anchors.leftMargin: 8
          anchors.rightMargin: 8
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
          text: root.format(deviceEntry.modelData)
        }

        TapHandler {
          acceptedButtons: Qt.LeftButton
          onTapped: {
            root.expanded = false
            root.picked(deviceEntry.modelData)
          }
        }

        HoverHandler {
          cursorShape: Qt.PointingHandCursor
        }
      }
    }

    clip: true
    Layout.preferredHeight: root.expanded ? implicitHeight : 0
    Behavior on Layout.preferredHeight {
      NumberAnimation {
        duration: 250
        easing.type: Easing.OutCubic
      }
    }
  }
}
