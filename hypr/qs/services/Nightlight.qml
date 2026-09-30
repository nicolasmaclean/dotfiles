pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
  id: root

  property real temperature

  function refresh(): void {
    getProc.running = true
  }

  function setTemperature(k): void {
    k = Math.round(k)
    if (k > 6400) {
      resetTemperature()
    } else {
      root.temperature = k
      Quickshell.execDetached(["hyprctl", "hyprsunset", "temperature", String(k)])
    }
  }

  function resetTemperature(): void {
    Quickshell.execDetached(["hyprctl", "hyprsunset", "identity"])
    root.temperature = 6500
  }

  Process {
    id: getProc
    command: ["hyprctl", "hyprsunset", "temperature"]
    running: true // read once at startup

    stdout: StdioCollector {
      onStreamFinished: {
        const k = parseInt(text)
        if (!isNaN(k))
          root.temperature = k
      }
    }
  }
}
