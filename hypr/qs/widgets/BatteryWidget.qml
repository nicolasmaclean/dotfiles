import QtQuick
import Quickshell

import qs.services

Text {
  text: `${Battery.glyph} ${(Battery.value * 100).toFixed(0)}%`
  visible: Battery.available
}
