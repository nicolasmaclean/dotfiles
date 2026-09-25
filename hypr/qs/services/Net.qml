pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Networking

Singleton {
  id: root

  enum Status {
    Disabled,
    Disconnected,
    Connecting,
    Portal,
    Connected,
    Disconnecting
  }

  readonly property var wifiDevices: Networking.devices.values.filter(d => d.type === DeviceType.Wifi)
  readonly property var wifiDevice: wifiDevices.find(d => d.state === ConnectionState.Connected) ?? null
  readonly property var connectionGlyph: {
    switch (Net.connectivity) {
    case Net.Status.Disabled:
      return "\u{f05aa}"
    case Net.Status.Disconnected:
      return "\u{f092e}"
    case Net.Status.Disconnecting:
      return "\u{f092e}"
    case Net.Status.Connecting:
      return "\u{f092f}"
    case Net.Status.Portal:
      return "\u{f092b}"
    case Net.Status.Connected:
      {
        const strength = Net.signalStrength
        if (strength > 0.75) {
          return "\u{f0928}"
        }
        if (strength > 0.5) {
          return "\u{f0925}"
        }
        if (strength > 0.25) {
          return "\u{f0922}"
        }
        if (strength > 0.1) {
          return "\u{f091f}"
        }
        return "\u{f092f}"
      }
    default:
      return "\u{f092e}"
    }
  }

  readonly property int connectivity: {
    if (!Networking.wifiEnabled || !Networking.wifiHardwareEnabled) {
      return Net.Status.Disabled
    }

    if (wifiDevices.length === 0) {
      return Net.Status.Disabled
    }

    // WARNING: this does not handle having multiple wifi devices connected to
    // the internet if the find happens to find 1st is stuck at portal/no internet
    // while the other one is connected... this is such a niche issue I'm ignoring it
    if (wifiDevice !== null) {
      switch (Networking.connectivity) {
      case NetworkConnectivity.Full:
        return Net.Status.Connected
      case NetworkConnectivity.Portal:
        return Net.Status.Portal
      default:
        return Net.Status.Connected
      }
    }

    const connecting = wifiDevices.some(d => d.state === ConnectionState.Connecting)
    if (connecting) {
      return Net.Status.Connecting
    }

    const disconnecting = wifiDevices.some(d => d.state === ConnectionState.Disconnecting)
    if (disconnecting) {
      return Net.Status.Disconnecting
    }

    return Net.Status.Disconnected
  }

  readonly property real signalStrength: {
    return wifiDevice?.networks.values.find(n => n.connected)?.signalStrength ?? 0
  }
}
