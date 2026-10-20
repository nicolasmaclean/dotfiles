pragma ComponentBehavior: Bound
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
  property var format: v => `${root.title} - ${Math.round(v * 100)}%`
  readonly property real padding: 13

  // event for slider to apply value changes
  signal moved(real value)

  implicitWidth: card.implicitWidth
  implicitHeight: card.implicitHeight

  property Component header: Text {
    horizontalAlignment: Text.AlignHCenter
    text: root.format(root.value)
  }

  Rectangle {
    id: card

    radius: Theme.borderRadiusBig
    implicitWidth: Theme.notificationWidth
    implicitHeight: cardLayout.implicitHeight + 2 * root.padding
    color: {
      let c = MyColors.background
      if (hover.hovered) {
        c = Qt.lighter(c, Theme.hoverLighten)
      }
      return c
    }

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

      Loader {
        sourceComponent: root.header
        Layout.fillWidth: true
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
          color: {
            let c = MyColors.tertiary
            if (slider.pressed) {
              c = Qt.lighter(c, Theme.hoverLighten)
            }
            return c
          }
        }
        background: Rectangle {
          x: slider.leftPadding
          y: slider.topPadding + (slider.availableHeight - height) / 2
          implicitWidth: 200
          implicitHeight: 6
          width: slider.availableWidth
          height: implicitHeight
          radius: 3
          color: MyColors.surfaceContainerHighest  // unfilled
          scale: slider.mirrored ? -1 : 1

          Rectangle {
            width: slider.position * parent.width
            height: 6
            radius: 3
            color: MyColors.tertiaryContainer
          }
        }
      }
    }

    HoverHandler {
      id: hover
    }

    // simple fade animation when changing card color
    Behavior on color {
      ColorAnimation {
        duration: 100
      }
    }

    CardShadow {
      target: card
    }
  }
}
