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
    color: Bluetooth.anyConnectedDevices ? Theme.text : Theme.textDim
    font.pixelSize: Theme.widgetIconSize
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: bluetui.running = !bluetui.running
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }

  Process {
    id: bluetui
    command: Apps.bluetui
  }
}
