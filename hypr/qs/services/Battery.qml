pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Services.UPower

Singleton {
  id: root

  readonly property var device: UPower.displayDevice
  readonly property bool available: device !== null && device.ready && device.isLaptopBattery
  readonly property real value: device?.percentage ?? 0
  readonly property bool charging: device?.state === UPowerDeviceState.Charging || device?.state === UPowerDeviceState.FullyCharged
  readonly property string glyph: {
    if (!available) {
      return "\u{f0091}"
    }

    // percentage is 0-1, glyph arrays are indexed in tens
    const level = Math.max(0, Math.min(10, Math.round(value * 10)))
    return charging ? _charging[level] : _discharging[level]
  }

  // indexed by charge level in tens, 0% through 100%
  readonly property list<string> _discharging: ["\u{f008e}", "\u{f007a}", "\u{f007b}", "\u{f007c}", "\u{f007d}", "\u{f007e}", "\u{f007f}", "\u{f0080}", "\u{f0081}", "\u{f0082}", "\u{f0079}"]
  readonly property list<string> _charging: ["\u{f089f}", "\u{f089c}", "\u{f0086}", "\u{f0087}", "\u{f0088}", "\u{f089d}", "\u{f0089}", "\u{f089e}", "\u{f008a}", "\u{f008b}", "\u{f0085}"]
}
