import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell

import qs

Item {
  id: root

  // data to show immediate
  required property string title
  required property real value

  property real from: 0
  property real to: 1
  property real stepSize: 0.05
  property var format: v => `${root.title}: ${Math.round(v * 100)}%`

  // event for slider to apply value changes
  signal moved(real value)

  implicitWidth: card.implicitWidth
  implicitHeight: card.implicitHeight

  Rectangle {
    id: card

    color: Theme.frame
    radius: Theme.borderRadiusBig
    implicitWidth: Theme.notificationWidth
    implicitHeight: 65

    ColumnLayout {
      spacing: 0
      anchors {
        verticalCenter: card.verticalCenter
        left: card.left
        right: card.right
        leftMargin: 10
        rightMargin: 10
      }

      Text {
        Layout.alignment: Qt.AlignHCenter
        text: root.format(root.value)
      }

      Slider {
        id: slider

        wheelEnabled: true
        stepSize: root.stepSize
        from: root.from
        to: root.to
        value: root.value

        // don't worry about root.value being out-of-date, this event will force that to update too
        onMoved: root.moved(value)

        Layout.fillWidth: true
        handle: Rectangle {
          x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
          y: slider.topPadding + (slider.availableHeight - height) / 2
          implicitWidth: 6
          implicitHeight: 18
          radius: 3
          color: slider.pressed ? Theme.hover : Theme.accent
        }
      }
    }
  }
}
