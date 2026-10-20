pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

Rectangle {
  id: root

  readonly property real padding: 13

  implicitWidth: content.implicitWidth + padding * 2
  implicitHeight: Math.max(Theme.osdRowHeight, content.implicitHeight + 2 * padding)

  radius: Theme.borderRadiusBig
  color: {
    // default to wifi hardware switch set to off
    let c = MyColors.surfaceDim

    if (Net.switchState === Net.SwitchState.On) {
      c = MyColors.primaryContainer
    } else if (Net.switchState === Net.SwitchState.Off) {
      c = MyColors.secondaryContainer
    }

    if (hover.hovered) {
      c = Qt.lighter(c, Theme.hoverLighten)
    }

    return c
  }

  Text {
    id: content

    x: root.padding
    width: parent.width - root.padding * 2
    anchors.verticalCenter: parent.verticalCenter

    elide: Text.ElideRight
    text: `${Net.connectionGlyph}  ‧ ${Net.ssid !== "" ? Net.ssid : "Disconnected"}`
    color: MyColors.oonBackground
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Net.toggleWifi()
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
    target: root
  }
}
