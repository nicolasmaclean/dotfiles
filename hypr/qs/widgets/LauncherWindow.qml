import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets

import qs
import qs.services

Rectangle {
  id: root

  readonly property real maxHeight: search.height + Theme.launcherHeight + Theme.launcherPaddingY * 2
  property var actionsFor: null

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

    spacing: 10

    TextInput {
      id: search

      leftPadding: 15

      // escape to exit the launcher
      focus: true
      Keys.onEscapePressed: Launcher.close()

      // propagate input to the launcher service
      onTextChanged: {
        Launcher.query = text
        appEntries.currentIndex = 0
      }

      // use arrows to select app entry
      visible: !root.actionsFor
      Keys.onUpPressed: scroll(false)
      Keys.onDownPressed: scroll(true)
      Keys.onPressed: event => {
        if (!root.actionsFor)
          return
        if (event.key === Qt.Key_J) {
          scroll(true)
          event.accepted = true
        } else if (event.key === Qt.Key_K) {
          scroll(false)
          event.accepted = true
        }
      }

      // use tab or right to view current entry's actions (like firefox private browsing)
      Keys.onTabPressed: appEntries.toggleActions()
      Keys.onRightPressed: appEntries.expandActions()
      Keys.onLeftPressed: appEntries.closeActions()

      // enter to execute the current entry
      Keys.onReturnPressed: {
        const e = appEntries.currentItem?.modelData
        if (e === null)
          return
        if (!root.actionsFor) {
          Launcher.executeEntry(e)
          Launcher.close()
        } else {
          const a = actionEntries.currentItem?.modelData
          if (a === null)
            return
          Launcher.executeAction(e, a)
          Launcher.close()
        }
      }

      function scroll(inc): void {
        let entries = !root.actionsFor ? appEntries : actionEntries
        if (inc) {
          entries.incrementCurrentIndex()
        } else {
          entries.decrementCurrentIndex()
        }
      }
    }

    // show root.actionsFor instead of TextInput when looking at actions
    RowLayout {
      visible: !!root.actionsFor

      Layout.fillWidth: true
      Layout.leftMargin: 15
      Layout.rightMargin: 15

      IconImage {
        source: Quickshell.iconPath(root.actionsFor.icon, true)
        implicitSize: 20
      }

      Text {
        // id: label
        text: root.actionsFor.name
        Layout.fillWidth: true
        elide: Text.ElideRight
      }
    }

    ListView {
      id: appEntries

      visible: !root.actionsFor

      function toggleActions(): void {
        if (!root.actionsFor) {
          expandActions()
        } else {
          closeActions()
        }
      }
      function expandActions(): void {
        if (currentItem?.modelData.actions.length === 0) {
          return
        }
        root.actionsFor = currentItem?.modelData
        actionEntries.currentIndex = 0
      }
      function closeActions(): void {
        root.actionsFor = null
      }

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
          anchors.right: parent.right
          anchors.rightMargin: 10

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

          Text {
            visible: appEntry.modelData.actions.length !== 0
            text: "\uF061"
            color: MyColors.oonBackground
            opacity: 0.6
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
        enabled: root.introDone
        NumberAnimation {
          duration: 200
          easing.type: Easing.OutCubic
        }
      }

      Layout.fillWidth: true
      Layout.preferredHeight: Math.min(contentHeight, Theme.launcherHeight)
      clip: true
    }

    ListView {
      id: actionEntries

      visible: !!root.actionsFor

      spacing: 2
      model: ScriptModel {
        values: root.actionsFor?.actions ?? []
      }

      delegate: Rectangle {
        id: actionEntry
        required property var modelData
        radius: Theme.borderRadiusBig
        color: {
          let c = ListView.isCurrentItem ? MyColors.tertiaryContainer : MyColors.background
          if (actionEntryHover.hovered) {
            c = Qt.darker(c, Theme.hoverDarken)
          }
          return c
        }

        width: ListView.view.width
        implicitHeight: actionLabel.implicitHeight + 12

        Text {
          id: actionLabel
          text: actionEntry.modelData.name
          elide: Text.ElideRight

          anchors.verticalCenter: parent.verticalCenter
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.leftMargin: 10
          anchors.rightMargin: 10
        }

        HoverHandler {
          id: actionEntryHover
        }

        TapHandler {
          acceptedButtons: Qt.LeftButton
          onTapped: {
            Launcher.executeAction(root.actionsFor, actionEntry.modelData)
            Launcher.close()
          }
        }
      }

      Layout.fillWidth: true
      Layout.preferredHeight: Math.min(contentHeight, Theme.launcherHeight)
      clip: true
    }
  }

  CardShadow {
    target: root
  }

  transform: Scale {
    id: introScale
    yScale: 0
    origin.y: root.height / 2
  }

  property bool introDone: false

  NumberAnimation {
    running: true
    onFinished: root.introDone = true
    target: introScale
    property: "yScale"
    from: 0
    to: 1

    easing.type: Easing.OutElastic
    duration: 350
    easing.amplitude: 1
    easing.period: 0.8
  }
}
