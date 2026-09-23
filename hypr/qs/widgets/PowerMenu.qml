import Quickshell
import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts

Item {
  id: root
  implicitWidth: 28
  implicitHeight: 28

  Text {
    anchors.centerIn: parent
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
          { label: "Shutdown", run: () => print("shutdown")},//Quickshell.execDetached(["systemctl", "poweroff"]) },
          { label: "Reboot",   run: () => print("reboot")},//Quickshell.execDetached(["systemctl", "reboot"]) },
          { label: "Logout",   run: () => print("logout")},//Hyprland.dispatch("exit") },
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

          HoverHandler { id: hover }
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
