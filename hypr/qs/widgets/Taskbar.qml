import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

PanelWindow {
  id: window

  required property bool isMainScreen
  required property bool showContent

  color: MyColors.background

  anchors {
    top: true
    left: true
    right: true
  }

  RowLayout {
    visible: window.showContent

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: 28
    anchors.rightMargin: 28
    anchors.bottom: parent.bottom
    anchors.bottomMargin: (Theme.taskbarThickness - implicitHeight) / 2

    // left widget group
    RowLayout {
      visible: window.isMainScreen

      Pill {
        color: MyColors.errorContainer
        PowerWidget {}
        BatteryWidget {}
      }
      Pill {
        color: MyColors.secondaryContainer

        WifiWidget {}
        BluetoothWidget {}
      }

      Pill {
        color: MyColors.tertiaryContainer

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
          TrayWidget {}
        }

        Pill {
          color: MyColors.tertiaryContainer

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
          color: MyColors.secondaryContainer
          TrayIcon {
            modelData: Tray.getItem(Tray.ids.one_password)
          }
          TrayIcon {
            modelData: Tray.getItem(Tray.ids.proton_vpn)
          }
        }

        Pill {
          ClockWidget {}
        }
      }
    }
  }

  // center widget group
  // this is separate so if left/right are varying sizes, this group will stay center
  RowLayout {
    visible: window.showContent
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    anchors.bottomMargin: (Theme.taskbarThickness - implicitHeight) / 2

    WorkspacesWidget {
      screen: window.screen
    }
  }
}
