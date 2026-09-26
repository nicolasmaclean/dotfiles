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

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
