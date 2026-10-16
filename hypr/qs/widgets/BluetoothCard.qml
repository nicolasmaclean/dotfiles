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

    if (Bluetooth.switchState === Bluetooth.SwitchState.Enabled) {
      c = MyColors.primaryContainer
    } else if (Bluetooth.switchState === Bluetooth.SwitchState.Disabled) {
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

    color: MyColors.oonBackground
    elide: Text.ElideRight
    text: {
      let str = `${Bluetooth.connectivityGlyph} ‧ `
      if (Bluetooth.switchState === Bluetooth.SwitchState.Unavailable) {
        str += "Unavailable"
      } else if (Bluetooth.switchState === Bluetooth.SwitchState.Disabled) {
        str += "Off"
      } else {
        let deviceCount = Bluetooth.connectedDevices.length
        if (deviceCount === 1) {
          let device = Bluetooth.connectedDevices[0]
          str += device.name
          if (device.batteryAvailable) {
            str += ` ${Math.round(device.battery * 100)}%`
          }
        } else {
          str += `${deviceCount} devices`
        }
      }
      return str
    }
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Bluetooth.toggle()
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
}
