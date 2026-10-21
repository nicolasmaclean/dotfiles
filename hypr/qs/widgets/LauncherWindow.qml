import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets

import qs
import qs.services

Rectangle {
  id: root

  readonly property real maxHeight: search.height + Theme.launcherHeight + Theme.launcherPaddingY * 2

  implicitWidth: Theme.launcherWidth
  implicitHeight: layout.implicitHeight + 2 * Theme.launcherPaddingY
  color: MyColors.background
  radius: Theme.borderRadiusBig

  ColumnLayout {
    id: layout
    anchors.left: parent.left
    anchors.right: parent.right

    anchors.top: parent.top
    anchors.topMargin: Theme.launcherPaddingY
    anchors.bottomMargin: Theme.launcherPaddingY
    anchors.leftMargin: Theme.launcherPaddingX
    anchors.rightMargin: Theme.launcherPaddingX

    TextInput {
      id: search

      // escape to exit the launcher
      focus: true
      Keys.onEscapePressed: Launcher.close()

      // propagate input to the launcher service
      onTextChanged: {
        Launcher.query = text
        appEntries.currentIndex = 0
      }

      // use arrows to select app entry
      Keys.onUpPressed: appEntries.decrementCurrentIndex()
      Keys.onDownPressed: appEntries.incrementCurrentIndex()

      // enter to execute the current entry
      Keys.onReturnPressed: {
        const e = appEntries.currentItem?.modelData
        if (e === null)
          return
        Launcher.executeEntry(e)
        Launcher.close()
      }
    }

    ListView {
      id: appEntries

      spacing: 2
      model: ScriptModel {
        values: Launcher.results
      }
      delegate: Rectangle {
        id: appEntry
        required property var modelData
        radius: Theme.borderRadiusBig
        color: {
          let c = ListView.isCurrentItem ? MyColors.tertiaryContainer : MyColors.background
          if (appEntryHover.hovered) {
            c = Qt.darker(c, Theme.hoverDarken)
          }
          return c
        }

        width: ListView.view.width
        implicitHeight: row.implicitHeight + 12

        RowLayout {
          id: row

          anchors.verticalCenter: parent.verticalCenter
          anchors.left: parent.left
          anchors.leftMargin: 10

          IconImage {
            source: Quickshell.iconPath(appEntry.modelData.icon, true)
            implicitSize: 20
          }

          Text {
            id: label
            text: appEntry.modelData.name
            Layout.fillWidth: true
            elide: Text.ElideRight
          }
        }

        HoverHandler {
          id: appEntryHover
        }

        TapHandler {
          acceptedButtons: Qt.LeftButton
          onTapped: {
            Launcher.executeEntry(appEntry.modelData)
            Launcher.close()
          }
        }
      }

      Behavior on Layout.preferredHeight {
        NumberAnimation {
          duration: 250
          easing.type: Easing.OutCubic
        }
      }

      Layout.fillWidth: true
      Layout.preferredHeight: Math.min(contentHeight, Theme.launcherHeight)
      clip: true
    }
  }

  // TODO: all instances of this component are getting clipped by their parent...
  CardShadow {
    target: root
  }
}
