import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

PanelWindow {
  id: window

  required property bool isMainScreen

  implicitHeight: Theme.taskbarThickness
  color: Theme.frame

  anchors {
    top: true
    left: true
    right: true
  }

  RowLayout {
    anchors.fill: parent
    anchors.leftMargin: 28
    anchors.rightMargin: 28

    // left widget group
    RowLayout {
      visible: window.isMainScreen

      Pill {
        color: "#CCCCCC"
        PowerWidget {}
        BatteryWidget {}
      }
      Pill {
        color: "#CCCCCC"

        WifiWidget {}
        BluetoothWidget {}
      }

      Pill {
        color: "#CCCCCC"

        VolumeWidget {}
        MicWidget {}
      }

      OsdToggle {}
    }

    Item {
      Layout.fillWidth: true
    }

    // right widget group
    Loader {
      active: window.isMainScreen
      sourceComponent: RowLayout {

        Pill {
          color: "#CCCCCC"
          TrayWidget {}
        }

        Pill {
          color: "#CCCCCC"

          TrayIcon {
            modelData: Tray.getItem(Tray.ids.mailspring)
          }

          TrayIcon {
            modelData: Tray.getItem(Tray.ids.discord)
          }

          TrayIcon {
            modelData: Tray.getItem(Tray.ids.signal)
          }
        }

        Pill {
          color: "#CCCCCC"

          TrayIcon {
            modelData: Tray.getItem(Tray.ids.one_password)
          }
          TrayIcon {
            modelData: Tray.getItem(Tray.ids.proton_vpn)
          }
        }

        Pill {
          color: "#CCCCCC"

          ClockWidget {}
        }
      }
    }
  }

  // center widget group
  // this is separate so if left/right are varying sizes, this group will stay center
  RowLayout {
    anchors.centerIn: parent

    WorkspacesWidget {
      screen: window.screen
    }
  }
}
