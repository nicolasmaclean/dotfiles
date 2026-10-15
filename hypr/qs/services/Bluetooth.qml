pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Bluetooth as QsBt

Singleton {
  id: root

  enum SwitchState {
    Unavailable,
    Disabled,
    Enabled
  }

  readonly property var adapter: QsBt.Bluetooth.defaultAdapter
  readonly property bool enabled: adapter?.enabled ?? false
  readonly property var connectedDevices: QsBt.Bluetooth.devices.values.filter(d => d.connected)
  readonly property bool anyConnectedDevices: connectedDevices.length > 0

  readonly property string connectivityGlyph: {
    if (!enabled)
      return "󰂲"
    return "󰂯"
  }

  readonly property int switchState: {
    if (adapter === null || adapter.state === QsBt.BluetoothAdapterState.Blocked) {
      return Bluetooth.SwitchState.Unavailable
    }
    if (enabled) {
      return Bluetooth.SwitchState.Enabled
    }

    return Bluetooth.SwitchState.Disabled
  }

  function toggle(): void {
    if (adapter === null)
      return
    adapter.enabled = !adapter.enabled
  }
}
