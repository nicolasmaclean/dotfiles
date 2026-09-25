import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland

Item {
  id: root

  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  Text {
    id: icon
    font.pixelSize: 18
    text: "⏻"
  }

  MouseArea {
    anchors.fill: parent
    onClicked: menu.open()
  }

  PopupMenu {
    id: menu

    anchorItem: root

    ColumnLayout {
      spacing: 2

      Repeater {
        model: [
          {
            "label": "Shutdown",
            "run": () => {
              return Quickshell.execDetached(["systemctl", "poweroff"])
            }
          },
          {
            "label": "Reboot",
            "run": () => {
              return Quickshell.execDetached(["systemctl", "reboot"])
            }
          },
          {
            "label": "Logout",
            "run": () => {
              return Quickshell.execDetached(["uwsm", "stop"])
            }
          },
          {
            "label": "Lock",
            "run": () => {
              return Quickshell.execDetached(["loginctl", "lock-session"])
            }
          }
        ]

        Rectangle {
          id: entry

          required property var modelData

          implicitWidth: 120
          implicitHeight: 28
          radius: 4
          color: hover.hovered ? "#dddddd" : "transparent"

          Text {
            anchors.verticalCenter: parent.verticalCenter
            x: 8
            text: entry.modelData.label
          }

          HoverHandler {
            id: hover
          }

          TapHandler {
            onTapped: {
              menu.close()
              entry.modelData.run()
            }
          }
        }
      }
    }
  }
}
