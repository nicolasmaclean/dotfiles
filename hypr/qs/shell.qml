//patch in default fonts (as opposed to symlink from .config to here)
//pragmas must come before any import or quickshell silently ignores them
//@ pragma Env FONTCONFIG_FILE=~/dotfiles/hypr/qs/fonts.conf
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

import qs.widgets

Scope {
  id: root

  property bool taskbarVisible: true
  NotificationArea {}

  Variants {
    model: Quickshell.screens

    // draw taskbar
    Scope {
      id: screenScope

      required property var modelData

      Frame {
        screen: screenScope.modelData
        topInset: root.taskbarVisible ? 40 : thickness
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
