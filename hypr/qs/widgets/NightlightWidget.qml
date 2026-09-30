import QtQuick
import Quickshell

import qs
import qs.services

Item {
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    text: "\u{f0594}"
    font.pixelSize: Theme.widgetIconSize
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.nightlight.toggle()
  }

  TapHandler {
    acceptedButtons: Qt.RightButton
    onTapped: Nightlight.resetTemperature()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
