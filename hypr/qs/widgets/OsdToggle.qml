import QtQuick
import Quickshell

import qs
import qs.services

Item {
  id: root
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  readonly property string stateGlyph: Osd.hasShown ? (Osd.allShown ? "●" : "◐") : "○"

  Text {
    id: icon
    text: root.stateGlyph
    font.pixelSize: Theme.widgetIconSize
    font.family: Theme.iconFont
    color: MyColors.surfaceDim
  }

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Osd.toggleAll()
  }

  HoverHandler {
    cursorShape: Qt.PointingHandCursor
  }
}
