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
    font.family: Theme.iconFont
    color: MyColors.oonTertiaryContainer
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.volume.toggle()
  }

  TapHandler {
    acceptedButtons: Qt.RightButton
    onTapped: Audio.toggleMuted()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
