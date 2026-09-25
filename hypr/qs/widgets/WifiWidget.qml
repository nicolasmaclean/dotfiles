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
    font.pixelSize: 18
    color: Theme.text
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: nmtui.running = !nmtui.running
  }

  Process {
    id: nmtui
    command: Apps.wifitui
  }
}
