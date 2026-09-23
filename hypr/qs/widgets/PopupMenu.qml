import Quickshell
import Quickshell.Wayland
import QtQuick

import qs

// TODO: AI SLOP, refactor or review later
// fullscreen transparent overlay above everything (including the taskbar)
// children are shown in a box under anchorItem
// clicking anywhere outside the box or pressing escape closes it
PanelWindow {
  id: popup

  // the item the box is positioned under (usually the button that opens it)
  required property Item anchorItem
  property real padding: 8
  property real gap: 6

  default property alias content: contentArea.data

  function open() { visible = true }
  function close() { visible = false }
  function toggle() { visible = !visible }

  visible: false
  screen: anchorItem.QsWindow.window?.screen ?? null

  anchors {
    top: true
    bottom: true
    left: true
    right: true
  }
  exclusionMode: ExclusionMode.Ignore
  color: "transparent"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

  MouseArea {
    anchors.fill: parent
    onClicked: popup.close()
  }

  Rectangle {
    id: box
    focus: true
    Keys.onEscapePressed: popup.close()

    // centered under the anchor, clamped to the screen edges
    // the taskbar sits at the top of the screen, so its window coords line up with this fullscreen window's coords
    property point anchorPos: popup.visible ? popup.anchorItem.mapToItem(null, 0, 0) : Qt.point(0, 0)
    x: Math.max(8, Math.min(anchorPos.x + (popup.anchorItem.width - width) / 2, popup.width - width - 8))
    y: anchorPos.y + popup.anchorItem.height + popup.gap

    width: contentArea.childrenRect.width + popup.padding * 2
    height: contentArea.childrenRect.height + popup.padding * 2
    radius: 6
    color: Theme.frame

    // swallow clicks so they don't reach the close-on-click area behind
    MouseArea {
      anchors.fill: parent
    }

    Item {
      id: contentArea
      x: popup.padding
      y: popup.padding
      width: childrenRect.width
      height: childrenRect.height
    }
  }
}
