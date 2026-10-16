import QtQuick
import Quickshell
import Quickshell.Io

import qs
import qs.services

Item {
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    text: Bluetooth.connectivityGlyph
    color: MyColors.oonSecondaryContainer
    font.pixelSize: Theme.widgetIconSize - 4
    font.family: Theme.iconFont
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.bluetooth.toggle()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }

  Process {
    id: bluetui
    command: Apps.bluetui
  }
}
