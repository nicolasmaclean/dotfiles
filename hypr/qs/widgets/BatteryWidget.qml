import QtQuick
import Quickshell

import qs
import qs.services

Text {
  text: `${Battery.glyph} ${(Battery.value * 100).toFixed(0)}%`
  visible: Battery.available
  font.family: Theme.iconFont
  font.pixelSize: Theme.widgetIconSize
  color: MyColors.oonTertiaryContainer
}
