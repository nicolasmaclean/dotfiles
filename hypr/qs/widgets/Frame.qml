import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import Quickshell
import Quickshell.Wayland
import qs

PanelWindow {
  id: root
  anchors {
    top: true
    bottom: true
    left: true
    right: true
  }
  color: "transparent"

  property real topInset: 40
  property alias thickness: frame.thickness

  // sit under the taskbar and don't effect layout at all
  exclusionMode: ExclusionMode.Ignore
  exclusiveZone: 0
  // frame doesn't consume any mouse input
  WlrLayershell.layer: WlrLayer.Bottom

  Shape {
    id: frame

    property real thickness: 8
    property real innerRadius: 25

    anchors.fill: parent
    preferredRendererType: Shape.CurveRenderer
    // shadow under frame
    layer.enabled: true

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
        y: root.topInset
        width: frame.width - frame.thickness * 2
        height: frame.height - root.topInset - frame.thickness
        radius: frame.innerRadius
      }
    }

    layer.effect: MultiEffect {
      shadowEnabled: true
      shadowColor: Qt.alpha("#000000", 1)
      // shadowBlur: 0.5
      blurMax: 40
      shadowScale: 0.995
    }
  }

  mask: Region {}
}
