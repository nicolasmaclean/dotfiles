pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
  id: root

  property real value
  property bool hasBacklight: false

  function setValue(v): void {
    // clamp 0-1
    value = Math.max(0, Math.min(1, v))

    if (hasBacklight) {
      Quickshell.execDetached(["brightnessctl", "-c", "backlight", "set", "-e4", `${Math.round(value * 100)}%`])
    } else {
      Quickshell.execDetached(["hyprctl", "hyprsunset", "gamma", String(Math.round(value * 100))])
    }
  }

  function resetBrightness(): void {
    if (hasBacklight) {
      setValue(0.7)
    } else {
      setValue(1)
    }
  }

  Process {
    id: getProcess
    command: root.hasBacklight ? ["brightnessctl", "-c", "backlight", "-m", "-e4"] : ["hyprctl", "hyprsunset", "gamma"]

    stdout: StdioCollector {
      onStreamFinished: {
        let v
        if (root.hasBacklight) {
          // "intel_backlight,backlight,12000,63%,19200"
          const f = text.trim().split("\n")[0].split(",")
          v = parseInt(f[3]) / 100
        } else {
          // "100"
          v = parseFloat(text) / 100
        }
        if (!isNaN(v))
          root.value = v
      }
    }
  }

  Process {
    id: checkForBacklightProcess
    command: ["brightnessctl", "-c", "backlight", "-m"]

    running: true // read once at startup
    stdout: StdioCollector {
      onStreamFinished: {
        const f = text.trim().split("\n")[0].split(",")
        if (f.length >= 5 && f[1] === "backlight") {
          root.hasBacklight = true
        }

        // seed initial brightness now we now if backlit
        getProcess.running = true
      }
    }
  }
}
