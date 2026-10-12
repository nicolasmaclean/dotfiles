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

  component Pill: Rectangle {
    default property alias content: pillRow.data

    implicitWidth: pillRow.implicitWidth + Theme.pillPadding * 2
    implicitHeight: pillRow.implicitHeight
    radius: height / 2

    RowLayout {
      id: pillRow
      anchors.centerIn: parent
    }
  }
}
