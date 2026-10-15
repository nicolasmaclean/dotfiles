pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

Row {
  id: root

  spacing: 5
  readonly property real contentHeight: Math.max(system.contentHeight, sliders.contentHeight)
  readonly property Region inputMask: Region {
    Region {
      x: system.x
      y: system.topMargin
      width: system.width
      height: system.contentHeight
    }
    Region {
      x: sliders.x
      y: sliders.topMargin
      width: sliders.width
      height: sliders.contentHeight
    }
  }

  OsdList {
    id: system
    model: ScriptModel {
      values: Osd.quickEntries.filter(e => e.shown)
    }

    delegate: Loader {
      required property var modelData
      width: ListView.view.width
      height: Math.max(Theme.osdRowHeight, item?.implicitHeight ?? 0)

      sourceComponent: ({
          [Osd.Kind.Power]: powerCard,
          [Osd.Kind.Wifi]: wifiCard,
          [Osd.Kind.Bluetooth]: bluetoothCard
        })[modelData.kind]
    }

    visible: contentItem.children.length > 0
    width: Theme.osdSystemColumnWidth

    Component {
      id: powerCard
      PowerCard {}
    }

    Component {
      id: wifiCard
      WifiCard {}
    }

    Component {
      id: bluetoothCard
      BluetoothCard {}
    }
  }

  OsdList {
    id: sliders
    model: ScriptModel {
      values: Osd.entries.filter(e => e.shown).sort((a, b) => a.shownAt - b.shownAt)
    }

    delegate: Loader {
      id: card
      required property var modelData
      width: ListView.view.width
      height: Math.max(Theme.osdRowHeight, item?.implicitHeight ?? 0)

      sourceComponent: ({
          [Osd.Kind.Volume]: volumeCard,
          [Osd.Kind.Mic]: micCard,
          [Osd.Kind.Nightlight]: nightlightCard,
          [Osd.Kind.Brightness]: brightnessCard
        })[modelData.kind]

      HoverHandler {
        onHoveredChanged: card.modelData.hovered = hovered
      }
    }

    width: Theme.notificationWidth

    // OSD Cards
    Component {
      id: volumeCard
      SliderCard {
        title: "Volume"
        value: Audio.volume
        onMoved: value => Audio.setVolume(value)

        header: AudioDeviceDropdown {
          devices: Audio.sinks
          current: Audio.sink
          onPicked: n => Audio.setSink(n)
        }
      }
    }

    Component {
      id: micCard
      SliderCard {
        title: "Mic"
        value: Audio.sourceVolume
        onMoved: value => Audio.setSourceVolume(value)

        header: AudioDeviceDropdown {
          devices: Audio.sources
          current: Audio.source
          onPicked: n => Audio.setSource(n)
        }
      }
    }

    Component {
      id: brightnessCard
      SliderCard {
        title: "Brightnesss"
        value: Brightness.value
        onMoved: value => Brightness.setValue(value)
      }
    }

    Component {
      id: nightlightCard
      SliderCard {
        title: "Night light"
        value: Nightlight.temperature
        onMoved: value => Nightlight.setTemperature(value)

        from: 2500
        to: 6500
        stepSize: 100
        format: v => v >= 6500 ? "Night light: off" : `Night light: ${Math.round(v)}K`
      }
    }
  }

  component OsdList: ListView {
    interactive: false

    spacing: 5
    topMargin: 10
    anchors {
      top: parent.top
      bottom: parent.bottom
    }

    // animations
    add: Transition {
      id: slideIn
      NumberAnimation {
        property: "y"
        from: -(slideIn.ViewTransition.item.height + system.topMargin)
        easing.type: Easing.OutCubic
      }
    }

    remove: Transition {
      id: slideOut
      NumberAnimation {
        property: "y"
        to: -(slideOut.ViewTransition.item.height + system.topMargin)
        easing.type: Easing.OutCubic
      }
    }

    displaced: Transition {
      NumberAnimation {
        property: "y"
      }
    }
  }
}
