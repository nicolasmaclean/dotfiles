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

  // app launcher
  LazyLoader {
    active: Launcher.open
    PanelWindow {
      id: launcher

      screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) ?? null
      WlrLayershell.namespace: "qs-launcher"
      exclusionMode: ExclusionMode.Ignore
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
      mask: Region {
        item: launcherWindow
      }

      readonly property int overshootPad: 30
      implicitWidth: launcherWindow.implicitWidth + overshootPad * 2
      implicitHeight: launcherWindow.maxHeight + overshootPad * 2

      color: "transparent"
      LauncherWindow {
        id: launcherWindow
        x: launcher.overshootPad
        y: launcher.overshootPad
      }

      HyprlandFocusGrab {
        active: true
        windows: [launcher]
        onCleared: Launcher.close()
      }
    }
  }

  // osd (power, wifi, bluetooth, etc.)
  PanelWindow {
    id: osd

    WlrLayershell.namespace: "qs-osd"
    screen: Theme.mainScreen
    exclusionMode: ExclusionMode.Ignore
    mask: osdArea.inputMask

    color: "transparent"
    anchors {
      top: true
      left: true
      bottom: true
    }
    margins.top: root.inset
    margins.left: 16

    property real maxWidth: Math.max(Theme.notificationWidth * 2, osdArea.implicitWidth)
    implicitWidth: maxWidth
    OsdArea {
      id: osdArea
      anchors.fill: parent

      onImplicitWidthChanged: osd.maxWidth = Math.max(osd.maxWidth, implicitWidth)
      HyprlandFocusGrab {
        active: Osd.hasPinned
        windows: [osd]
        onCleared: Osd.dismissPinned()
      }
    }
  }

  // calendar window and notifications
  PanelWindow {
    id: notifications

    WlrLayershell.namespace: "qs-notifications"
    screen: Theme.mainScreen
    exclusionMode: ExclusionMode.Ignore
    mask: Region {
      Region {
        item: calendarCard.visible ? calendarCard : null
      }
      Region {
        x: notificationArea.x
        y: notificationsLayout.y + notificationArea.y
        width: notificationArea.width
        height: notificationArea.contentHeight
      }
    }

    color: "transparent"
    anchors {
      top: true
      right: true
      bottom: true
    }
    margins {
      top: root.inset
      right: 16
    }

    implicitWidth: Math.max(calendarCard.item?.implicitWidth ?? 0, notificationArea.implicitWidth)

    ColumnLayout {
      id: notificationsLayout

      anchors.fill: parent
      anchors.topMargin: 10

      Loader {
        id: calendarCard

        active: Calendar.open || slideOut.running
        visible: active

        states: State {
          name: "open"
          when: Calendar.open
          PropertyChanges {
            slide.y: 0
          }
        }

        transitions: [
          Transition {
            to: "open"
            NumberAnimation {
              target: slide
              property: "y"
              easing.type: Easing.OutElastic
              easing.amplitude: 1
              easing.period: 0.8
              duration: 550
            }
          },
          Transition {
            id: slideOut
            from: "open"
            NumberAnimation {
              target: slide
              property: "y"
              easing.type: Easing.OutCubic
            }
          }
        ]

        transform: Translate {
          id: slide
          y: -(calendarCard.height + 10)
        }

        sourceComponent: CalendarCard {
          HyprlandFocusGrab {
            active: true
            windows: [notifications]
            onCleared: Calendar.open = false
          }
        }
      }
      NotificationArea {
        id: notificationArea
        Layout.fillWidth: true
        Layout.fillHeight: true
      }
    }
  }

  // taskbar and frame
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
        showContent: root.taskbarVisible
        isMainScreen: screenScope.modelData === Theme.mainScreen
        implicitHeight: root.inset
      }
    }
  }

  // IPC for taskbar visibility
  IpcHandler {
    target: "taskbar"

    function toggle(): void {
      root.taskbarVisible = !root.taskbarVisible
    }
  }

  // IPC for launcher
  IpcHandler {
    target: "launcher"

    function toggle(): void {
      Launcher.toggle()
    }
  }
}
