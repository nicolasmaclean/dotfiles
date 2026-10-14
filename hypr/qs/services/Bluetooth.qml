pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Bluetooth as QsBt

Singleton {
  id: root

  readonly property bool enabled: QsBt.Bluetooth.defaultAdapter?.enabled ?? false
  readonly property var connectedDevices: QsBt.Bluetooth.devices.values.filter(d => d.connected)
  readonly property bool anyConnectedDevices: connectedDevices.length > 0

  readonly property string connectivityGlyph: {
    if (!enabled)
      return "󰂲"
    return "󰂯"
  }
}
