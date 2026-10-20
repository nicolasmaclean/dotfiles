import QtQuick
import Quickshell
import Quickshell.Io

import qs
import qs.services

Text {
  text: Time.time
  font.pixelSize: 13
  font.family: Theme.iconFont
  color: MyColors.oonSurface
  padding: 4

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: Calendar.toggle()
  }
}
