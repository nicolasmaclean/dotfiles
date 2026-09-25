pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Bluetooth as QsBt

Singleton {
  id: root

  readonly property bool enabled: QsBt.Bluetooth.defaultAdapter?.enabled ?? false
  readonly property var anyConnectedDevices: QsBt.Bluetooth.devices.values.some(d => d.connected)

  readonly property string connectivityGlyph: {
    if (!enabled)
      return "󰂲"
    return "󰂯"
  }
}
