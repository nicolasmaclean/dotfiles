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

    anchors.fill: parent
    text: Net.connectionGlyph
    font.pixelSize: Theme.widgetIconSize
    color: MyColors.oonSecondaryContainer
    font.family: Theme.iconFont
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.wifi.toggle()
  }

  TapHandler {
    acceptedButtons: Qt.RightButton
    onTapped: nmtui.running = !nmtui.running
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }

  Process {
    id: nmtui
    command: Apps.wifitui
  }
}
