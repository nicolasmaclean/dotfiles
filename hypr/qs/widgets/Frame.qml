import QtQuick
import QtQuick.Shapes
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland

import qs

PanelWindow {
  anchors {
    top: true
    bottom: true
    left: true
    right: true
  }

  // sit under the taskbar and don't effect layout at all
  exclusionMode: ExclusionMode.Ignore
  exclusiveZone: 0

  // frame doesn't consume any mouse input
  WlrLayershell.layer: WlrLayer.Bottom
  mask: Region { }

  // draw frame and taskbar background
  color: "transparent"
  Shape {
    id: frame
    anchors.fill: parent
    preferredRendererType: Shape.CurveRenderer

    property real thickness: 8
    property real innerRadius: 25

    ShapePath {
      fillColor: Theme.frame
      strokeWidth: 0
      fillRule: ShapePath.OddEvenFill

      // outer edge
      // paint the frame as a rectangle across the whole screen
      PathRectangle {
        x: 0
        y: 0
        width: frame.width
        height: frame.height
      }

      // inner edge
      // cut out the square (with rounded corners) from the frame
      PathRectangle {
        x: frame.thickness
        y: 40
        width: frame.width - frame.thickness * 2
        height: frame.height - 40 - frame.thickness
        radius: frame.innerRadius
      }
    }

    // shadow under frame
    layer.enabled: true
    layer.effect: MultiEffect {
      shadowEnabled: true
      shadowColor: Qt.alpha("#000000", 1)
      // shadowBlur: 0.5
      blurMax: 40
      shadowScale: 0.995
    }
  }
}

