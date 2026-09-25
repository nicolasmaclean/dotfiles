import Quickshell
import QtQuick
import QtQuick.Shapes
import QtQuick.Layouts

import qs

PanelWindow {
  anchors {
    top: true
    left: true
    right: true
  }

  implicitHeight: 40
  color: Theme.frame

  RowLayout {
    anchors.fill: parent
    anchors.leftMargin: 8
    anchors.rightMargin: 8

    // left widget group
    RowLayout {
    }

    Item {
      Layout.fillWidth: true
    }

    // right widget group
    RowLayout {
      WifiWidget { } 
      PowerWidget { }
    }
  }

  // center widget group
  // this is separate so if left/right are varying sizes, this group will stay center
  RowLayout {
    anchors.centerIn: parent
    ClockWidget { }
  }
}

