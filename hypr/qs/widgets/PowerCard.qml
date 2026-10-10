pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

Item {
  id: root

  readonly property real padding: 13

  implicitWidth: card.implicitWidth
  implicitHeight: card.implicitHeight

  Rectangle {
    id: card

    color: Theme.frame
    radius: Theme.borderRadiusBig
    width: parent.width
    implicitWidth: cardLayout.implicitWidth + 20
    implicitHeight: cardLayout.implicitHeight + 2 * root.padding

    ColumnLayout {
      id: cardLayout

      spacing: 0
      anchors {
        top: card.top
        left: card.left
        right: card.right
        topMargin: root.padding
        leftMargin: 10
        rightMargin: 10
      }

      Repeater {
        model: Power.actions
        delegate: Rectangle {
          id: actionEntry
          required property var modelData

          Layout.fillWidth: true
          implicitWidth: actionText.implicitWidth + 16
          implicitHeight: 32
          radius: implicitHeight / 2
          color: hover.hovered ? Theme.hover : "transparent"

          Text {
            id: actionText
            x: 8
            anchors.verticalCenter: parent.verticalCenter
            text: `${actionEntry.modelData.icon}  ${actionEntry.modelData.label}`
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
        }
      }
    }
  }
}
