//patch in default fonts (as opposed to symlink from .config to here)
//pragmas must come before any import or quickshell silently ignores them
//@ pragma Env FONTCONFIG_FILE=~/dotfiles/hypr/qs/fonts.conf
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

import qs.services
import qs.widgets

Scope {
  id: root

  property bool taskbarVisible: true
  property real inset: taskbarVisible ? Theme.taskbarThickness : Theme.frameThickness

  PanelWindow {
    id: osd

    screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null
    exclusionMode: ExclusionMode.Ignore

    color: "transparent"
    implicitWidth: stack.implicitWidth
    implicitHeight: stack.implicitHeight
    anchors {
      top: true
      right: true
    }
    margins {
      top: root.inset + 10
      right: 16
    }

    ColumnLayout {
      id: stack
      OsdArea {
        HyprlandFocusGrab {
          active: Osd.pinned
          windows: [osd]
          onCleared: Osd.shown = Osd.pinned = false
        }
      }
      NotificationArea {}
    }
  }

  Variants {
    model: Quickshell.screens

    // draw taskbar
    Scope {
      id: screenScope

      required property var modelData

      Frame {
        screen: screenScope.modelData
        topInset: root.inset
      }

      Taskbar {
        screen: screenScope.modelData
        visible: root.taskbarVisible
      }
    }
  }

  IpcHandler {
    target: "taskbar"

    function toggle(): void {
      root.taskbarVisible = !root.taskbarVisible
    }
  }
}
