pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

Item {
  id: root

  implicitWidth: card.implicitWidth
  implicitHeight: card.implicitHeight

  GridLayout {
    id: card

    anchors {
      left: parent.left
      right: parent.right
      top: parent.top
    }

    columns: 2
    rowSpacing: 5
    columnSpacing: 5

    Repeater {
      model: Power.actions
      delegate: Rectangle {
        id: actionEntry
        required property var modelData

        Layout.fillWidth: true
        radius: Theme.borderRadiusBig
        color: {
          let c = MyColors.background
          if (hover.hovered) {
            c = Qt.lighter(c, Theme.hoverLighten)
          }
          return c
        }

        implicitWidth: content.implicitWidth
        implicitHeight: Math.max(Theme.osdRowHeight, content.implicitHeight + 16)

        ColumnLayout {
          id: content
          anchors.centerIn: parent
          spacing: 0

          Text {
            text: actionEntry.modelData.icon
            Layout.alignment: Qt.AlignHCenter
            font.pixelSize: 24
            color: MyColors.oonBackground
          }

          Text {
            text: actionEntry.modelData.label
            Layout.alignment: Qt.AlignHCenter
            color: MyColors.oonBackground
          }
        }

        TapHandler {
          acceptedButtons: Qt.LeftButton
          onTapped: () => {
            Osd.power.dismiss()
            actionEntry.modelData.run()
          }
        }

        HoverHandler {
          id: hover
          cursorShape: Qt.PointingHandCursor
        }

        // simple fade animation when changing card color
        Behavior on color {
          ColorAnimation {
            duration: 100
          }
        }
        CardShadow {
          target: actionEntry
        }
      }
    }
  }
}
