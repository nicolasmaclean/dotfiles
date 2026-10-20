import QtQuick
import QtQuick.Effects
import Quickshell

import qs

RectangularShadow {
  required property Rectangle target
  anchors.fill: target
  radius: target.radius
  z: -1

  color: MyColors.shadow
  blur: 12
  offset.x: 3
  offset.y: 3
}
