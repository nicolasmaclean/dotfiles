import QtQuick
import Quickshell

import qs
import qs.services

Item {
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    text: "\u{f05a8}"
    font.pixelSize: Theme.widgetIconSize
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.brightness.toggle()
  }

  TapHandler {
    acceptedButtons: Qt.RightButton
    onTapped: Brightness.resetBrightness()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
