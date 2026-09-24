import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import Quickshell.Services.Notifications

import qs
import qs.services

// Mouse:
//   left click    run the default action if there is one, otherwise dismiss
//   middle click  dismiss
//   right click   dismiss every notification
//   drag right    dismiss
// Hovering pauses the expire timer.
Item {
  id: root
  required property var modelData

  readonly property bool critical: modelData.urgency === NotificationUrgency.Critical
  readonly property var defaultAction: Array.from(modelData.actions).find(a => a.identifier === "default") ?? null
  readonly property var buttonActions: Array.from(modelData.actions).filter(a => a.identifier !== "default")

  // optional progress bar (0-100 or null)
  // this allows notification to reused for volume/brightness
  readonly property var progress: modelData.hints.value ?? null

  implicitWidth: 350
  implicitHeight: card.implicitHeight

  readonly property int timeoutMs: {
    // use expiration time from notification
    if (modelData.expireTimeout > 0) return modelData.expireTimeout 

    // never expire 
    if (modelData.expireTimeout === 0 || critical) return 0

    // default expiration times
    return modelData.urgency === NotificationUrgency.Low ? 4000 : 6000
  }

  PauseAnimation {
    id: expire
    duration: root.timeoutMs
    paused: running && hover.hovered
    onFinished: root.modelData.expire()
  }

  function restartExpire() {
    if (timeoutMs > 0) expire.restart()
    else expire.stop()
  }

  Component.onCompleted: restartExpire()

  // volume/brightness can update notification in place
  // restart expiration timer when updated
  Connections {
    target: root.modelData
    function onSummaryChanged() { root.restartExpire() }
    function onBodyChanged() { root.restartExpire() }
    function onHintsChanged() { root.restartExpire() }
    function onExpireTimeoutChanged() { root.restartExpire() }
  }

  // visuals
  // TODO: this is ai slop :skull:
  Rectangle {
    id: card
    width: parent.width
    implicitHeight: content.implicitHeight + padding * 2

    property real padding: 10

    radius: 6
    color: Theme.frame
    border.width: root.critical ? 2 : 0
    border.color: Theme.urgent

    // fade out as it's dragged away
    opacity: 1 - Math.max(0, x) / width

    Behavior on x {
      enabled: !mouse.drag.active
      NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
    }

    // a handler rather than the MouseArea's containsMouse so hovering the
    // action buttons (which sit on top of it) still counts
    HoverHandler { id: hover }

    MouseArea {
      id: mouse
      anchors.fill: parent
      acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton

      drag.target: card
      drag.axis: Drag.XAxis
      drag.minimumX: 0

      // a drag shouldn't also count as a click on release
      property bool dragged: false
      onPressed: dragged = false
      drag.onActiveChanged: if (drag.active) dragged = true

      onReleased: {
        if (!dragged) return
        if (card.x > card.width / 3) root.modelData.dismiss()
        else card.x = 0
      }

      onClicked: event => {
        if (dragged) return
        if (event.button === Qt.RightButton) Notify.dismissAll()
        else if (event.button === Qt.MiddleButton) root.modelData.dismiss()
        // invoking an action closes the notification unless it's resident
        else if (root.defaultAction) root.defaultAction.invoke()
        else root.modelData.dismiss()
      }
    }

    // App icon (theme icon name or file path)
    // Electron apps usually leave this empty so fall back to icon from .desktop
    readonly property string iconSource: {
      const entry = root.modelData.desktopEntry ? DesktopEntries.byId(root.modelData.desktopEntry) : null
      const icon = root.modelData.appIcon || entry?.icon || ""
      if (icon === "" || icon.startsWith("file://")) return icon
      if (icon.startsWith("/")) return "file://" + icon
      return Quickshell.iconPath(icon, true)
    }

    RowLayout {
      id: content
      anchors.fill: parent
      anchors.margins: card.padding
      spacing: 10

      // big image if the notification has one, otherwise the app icon
      Item {
        Layout.preferredWidth: 48
        Layout.preferredHeight: 48
        Layout.alignment: Qt.AlignTop
        visible: root.modelData.image !== "" || card.iconSource !== ""

        Image {
          anchors.fill: parent
          visible: root.modelData.image !== ""
          source: root.modelData.image
          sourceSize: Qt.size(96, 96)
          fillMode: Image.PreserveAspectCrop
        }

        IconImage {
          anchors.fill: parent
          visible: root.modelData.image === ""
          source: card.iconSource
        }
      }

      ColumnLayout {
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop
        spacing: 2

        Text {
          Layout.fillWidth: true
          text: root.modelData.summary
          color: root.critical ? Theme.urgent : Theme.text
          font.bold: true
          elide: Text.ElideRight
        }

        Text {
          Layout.fillWidth: true
          text: root.modelData.body
          color: Theme.textDim
          textFormat: Text.StyledText
          wrapMode: Text.Wrap
          maximumLineCount: 4
          elide: Text.ElideRight
          visible: text !== ""
          onLinkActivated: link => Qt.openUrlExternally(link)
        }

        // progress bar
        Rectangle {
          Layout.fillWidth: true
          Layout.topMargin: 4
          implicitHeight: 6
          radius: 3
          color: Theme.hover
          visible: root.progress !== null

          Rectangle {
            height: parent.height
            width: parent.width * Math.max(0, Math.min(100, root.progress ?? 0)) / 100
            radius: parent.radius
            color: root.critical ? Theme.urgent : Theme.accent
          }
        }

        // action buttons
        RowLayout {
          Layout.fillWidth: true
          Layout.topMargin: 4
          spacing: 4
          visible: root.buttonActions.length > 0

          Repeater {
            model: root.buttonActions

            Rectangle {
              id: button
              required property var modelData
              Layout.fillWidth: true
              implicitHeight: 24
              radius: 4
              color: buttonMouse.containsMouse ? Theme.hover : "transparent"
              border.width: 1
              border.color: Theme.hover

              Text {
                anchors.centerIn: parent
                width: parent.width - 8
                horizontalAlignment: Text.AlignHCenter
                text: button.modelData.text
                color: Theme.text
                elide: Text.ElideRight
              }

              MouseArea {
                id: buttonMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: button.modelData.invoke()
              }
            }
          }
        }
      }
    }
  }
}
