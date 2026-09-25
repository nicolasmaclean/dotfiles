import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import Quickshell
import qs

PanelWindow {
  implicitHeight: 40
  color: Theme.frame

  anchors {
    top: true
    left: true
    right: true
  }

  RowLayout {
    anchors.fill: parent
    anchors.leftMargin: 8
    anchors.rightMargin: 8

    // left widget group
    RowLayout {}

    Item {
      Layout.fillWidth: true
    }

    // right widget group
    RowLayout {
      MicWidget {}
      VolumeWidget {}
      BluetoothWidget {}
      WifiWidget {}
      PowerWidget {}
    }
  }

  // center widget group
  // this is separate so if left/right are varying sizes, this group will stay center
  RowLayout {
    anchors.centerIn: parent

    ClockWidget {}
  }
}
