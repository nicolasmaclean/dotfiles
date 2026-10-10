import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

Item {
  id: root

  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    font.pixelSize: Theme.widgetIconSize
    text: "⏻"
    color: Theme.text
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.power.toggle()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
