import QtQuick
import Quickshell

import qs
import qs.services

Text {
  text: `${(Battery.value * 100).toFixed(0)}%`
  visible: Battery.available
  font.family: Theme.iconFont
  font.pixelSize: 13
  color: MyColors.oonTertiaryContainer
}
