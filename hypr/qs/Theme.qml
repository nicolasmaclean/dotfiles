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
  readonly property color pillColor: Colors.surfaceContainerHigh

  readonly property real taskbarThickness: 40
  readonly property real frameThickness: 8
  readonly property real borderRadiusBig: 25
  readonly property real borderRadius: 8
  readonly property real notificationWidth: 350

  readonly property string iconFont: "MesloLGS Nerd Font Mono"
  readonly property real widgetIconSize: 20
  readonly property real trayIconSize: 17

  readonly property real osdRowHeight: 74
  readonly property real osdSystemColumnWidth: 200
  readonly property real pillPadding: 10
  readonly property real pillSpacing: 5

  readonly property real hoverLighten: 1.5
  readonly property real hoverDarken: 2.0
}
