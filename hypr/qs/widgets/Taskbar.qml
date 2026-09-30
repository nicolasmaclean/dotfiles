import QtQuick
import QtQuick.Layouts
import Quickshell

import qs

PanelWindow {
  id: window

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
      PowerWidget {}
      BatteryWidget {}
      WifiWidget {}
      BluetoothWidget {}
      VolumeWidget {}
      MicWidget {}
    }

    Item {
      Layout.fillWidth: true
    }

    // right widget group
    RowLayout {
      Tray {}
      Text {
        text: " | "
      }
      ClockWidget {}
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
