import QtQuick
import Quickshell

import qs

Item {
  id: root

  property alias color: face.color
  property alias radius: face.radius
  default property alias content: face.data

  readonly property bool hovered: hover.hovered
  property bool raised: hovered
  property real liftX: root.raised ? Theme.pillLiftX : 0
  property real liftY: root.raised ? Theme.pillLiftY : 0

  Rectangle {
    id: shadow
    anchors.fill: parent
    color: Qt.darker(face.color, Theme.hoverDarken)
    visible: root.liftX > 0 || root.liftY > 0
    radius: face.radius
  }

  Rectangle {
    id: face
    anchors.fill: parent
    transform: Translate {
      x: -root.liftX
      y: -root.liftY
    }
  }

  HoverHandler {
    id: hover
  }

  Behavior on liftX {
    NumberAnimation {
      duration: Theme.pillLiftDuration
    }
  }
  Behavior on liftY {
    NumberAnimation {
      duration: Theme.pillLiftDuration
    }
  }
}
