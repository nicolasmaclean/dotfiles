pragma Singleton

import QtQuick
import Quickshell

Singleton {
  readonly property real taskbarThickness: 40
  readonly property real frameThickness: 8
  readonly property real borderRadiusBig: 25
  readonly property real borderRadius: 8

  readonly property string iconFont: "MesloLGS Nerd Font Mono"
  readonly property real widgetIconSize: 20
  readonly property real trayIconSize: 17

  readonly property real notificationWidth: 350
  readonly property real osdRowHeight: 78
  readonly property real osdSystemColumnWidth: 200
  readonly property real pillPadding: 10
  readonly property real pillSpacing: 5

  readonly property real hoverLighten: 1.2
  readonly property real hoverDarken: 1.5

  readonly property string mainScreenName: "HDMI-A-2"
  readonly property ShellScreen mainScreen: Quickshell.screens.find(s => s.name === mainScreenName)

  readonly property real pillLiftX: 2
  readonly property real pillLiftY: 2
  readonly property real pillLiftDuration: 80

  readonly property real launcherWidth: 550
  readonly property real launcherHeight: 400
  readonly property real launcherPaddingX: 15
  readonly property real launcherPaddingY: 10
}
