import QtQuick
import Quickshell

import qs
import qs.services

Item {
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    text: Audio.micGlyph
    font.pixelSize: Theme.widgetIconSize
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.mic.toggle()
  }

  TapHandler {
    acceptedButtons: Qt.RightButton
    onTapped: Audio.toggleSourceMuted()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
