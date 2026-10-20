pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell

import qs

Rectangle {
  id: root

  property int month
  property int year
  readonly property int hPadding: 20
  readonly property int vPadding: 15

  implicitWidth: Theme.notificationWidth
  implicitHeight: layout.implicitHeight + 2 * vPadding

  radius: Theme.borderRadiusBig
  color: MyColors.background

  Component.onCompleted: goToToday()

  function goToToday(): void {
    const d = new Date()
    setDate(d)
  }

  function shift(delta): void {
    const d = new Date(year, month + delta, 1)
    setDate(d)
  }

  function setDate(d): void {
    month = d.getMonth()
    year = d.getFullYear()
  }

  WheelHandler {
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    onWheel: event => root.shift(event.angleDelta.y > 0 ? -1 : 1)
  }

  ColumnLayout {
    id: layout

    spacing: 8
    anchors.fill: parent
    anchors.leftMargin: root.hPadding
    anchors.rightMargin: root.hPadding
    anchors.bottomMargin: root.vPadding
    anchors.topMargin: root.vPadding

    RowLayout {
      id: headerRow
      Layout.fillWidth: true

      NavButton {
        label: "<"
        onClicked: root.shift(-1)
      }

      Text {
        text: grid.title
        color: MyColors.oonBackground
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        TapHandler {
          acceptedButtons: Qt.LeftButton
          onTapped: root.goToToday()
        }
      }

      NavButton {
        label: ">"
        onClicked: root.shift(1)
      }
    }

    GridLayout {
      columns: 2
      columnSpacing: 8
      Layout.fillWidth: true

      Item {}

      DayOfWeekRow {
        Layout.fillWidth: true
      }

      WeekNumberColumn {
        Layout.fillHeight: true

        month: grid.month
        year: grid.year

        delegate: Text {
          required property int weekNumber
          text: weekNumber

          horizontalAlignment: Text.AlignHCenter
          verticalAlignment: Text.AlignVCenter
          color: MyColors.oonBackground
          opacity: 0.6
        }
      }

      MonthGrid {
        id: grid
        Layout.fillWidth: true

        month: root.month
        year: root.year
        spacing: 0

        delegate: Rectangle {
          required property var model
          readonly property bool isToday: model.today

          radius: Theme.borderRadius
          color: {
            let c = isToday ? MyColors.tertiaryContainer : MyColors.background
            if (dayHover.hovered) {
              c = Qt.darker(c, Theme.hoverDarken)
            }
            return c
          }

          implicitWidth: dayText.implicitWidth + 8
          implicitHeight: dayText.implicitHeight + 10

          Text {
            id: dayText
            text: parent.model.day

            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            opacity: parent.model.month === grid.month ? 1 : 0.3
            color: {
              let c = parent.isToday ? MyColors.oonTertiaryContainer : MyColors.oonBackground
              if (dayHover.hovered) {
                c = Qt.darker(c, Theme.hoverDarken)
              }
              return c
            }
          }

          HoverHandler {
            id: dayHover
          }
        }
      }
    }
  }

  component NavButton: Rectangle {
    id: btn

    property alias label: shiftButton.text
    signal clicked

    implicitWidth: shiftButton.implicitWidth + 20
    implicitHeight: shiftButton.implicitHeight + 8
    color: shiftHover.hovered ? MyColors.surfaceDim : MyColors.background
    radius: Theme.borderRadiusBig

    Text {
      id: shiftButton
      text: "<"
      anchors.centerIn: parent
      color: MyColors.oonBackground
    }

    TapHandler {
      acceptedButtons: Qt.LeftButton
      onTapped: btn.clicked()
    }

    HoverHandler {
      id: shiftHover
    }

    Behavior on color {
      ColorAnimation {
        duration: 100
      }
    }
  }
}
