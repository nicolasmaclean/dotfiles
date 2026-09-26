import QtQuick
import Quickshell

import qs
import qs.services

Item {
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    text: Audio.volumeGlyph
    font.pixelSize: Theme.widgetIconSize
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.pin()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
