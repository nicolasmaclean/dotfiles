pragma Singleton

import QtQuick
import Quickshell

import qs.theme

Singleton {
  readonly property color frame: Colors.surfaceContainer
  readonly property color hover: Colors.surfaceContainerHigh
  readonly property color text: Colors.oonSurface
  readonly property color textDim: Colors.oonSurfaceVariant
  readonly property color accent: Colors.primary
  readonly property color urgent: Colors.error

  readonly property real taskbarThickness: 40
  readonly property real frameThickness: 8
  readonly property real borderRadiusBig: 25
  readonly property real widgetIconSize: 18
  readonly property real notificationWidth: 350
}
