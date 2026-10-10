// pragmas must come before any import or quickshell silently ignores them
//
// patch in default fonts (as opposed to symlink from .config to here)
//@ pragma Env FONTCONFIG_FILE=~/dotfiles/hypr/qs/fonts.conf
//
// quickshell must be run as QApplication to use native menu widget for the system tray
// TODO: remove after I have custom menu ui
//@ pragma UseQApplication
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

import qs
import qs.services
import qs.widgets

Scope {
  id: root

  property bool taskbarVisible: true
  property real inset: taskbarVisible ? Theme.taskbarThickness : Theme.frameThickness

  PanelWindow {
    id: osd

    WlrLayershell.namespace: "qs-osd"
    screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null
    exclusionMode: ExclusionMode.Ignore
    mask: osdArea.inputMask

    color: "transparent"
    anchors {
      top: true
      left: true
      bottom: true
    }
    margins {
      top: root.inset + 10
      left: 16
    }

    property real maxWidth: Math.max(Theme.notificationWidth * 2, osdArea.implicitWidth)
    implicitWidth: maxWidth
    OsdArea {
      id: osdArea
      anchors.fill: parent

      onImplicitWidthChanged: osd.maxWidth = Math.max(osd.maxWidth, implicitWidth)
      // HyprlandFocusGrab {
      //   active: Osd.pinned
      //   windows: [osd]
      //   onCleared: Osd.shown = Osd.pinned = false
      // }
    }
  }

  PanelWindow {
    id: notifications

    WlrLayershell.namespace: "qs-notifications"
    screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null
    exclusionMode: ExclusionMode.Ignore
    mask: Region {
      width: notificationArea.width
      height: notificationArea.contentHeight
    }

    color: "transparent"
    anchors {
      top: true
      right: true
      bottom: true
    }
    margins {
      top: root.inset + 10
      right: 16
    }

    implicitWidth: notificationArea.implicitWidth
    NotificationArea {
      id: notificationArea
      anchors.fill: parent
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
