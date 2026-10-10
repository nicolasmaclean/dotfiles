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

      sourceComponent: ({
          [Osd.Kind.Power]: powerCard
        })[modelData.kind]
    }

    // fit this column to width of the widest card
    width: Array.prototype.reduce.call(contentItem.children, (w, c) => Math.max(w, c.implicitWidth), 0)

    Component {
      id: powerCard
      PowerCard {}
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
        to: -(slideIn.ViewTransition.item.height + system.topMargin)
        easing.type: Easing.OutCubic
      }
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
    spacing: 5
    interactive: false
    anchors {
      top: parent.top
      bottom: parent.bottom
    }
    topMargin: 10

    // animations
    add: Transition {
      NumberAnimation {
        property: "opacity"
        from: 0
        to: 1
      }
    }

    remove: Transition {
      NumberAnimation {
        property: "opacity"
        to: 0
        duration: 200
      }
    }

    displaced: Transition {
      NumberAnimation {
        property: "y"
      }
    }
  }

  move: Transition {
    NumberAnimation {
      property: "x"
      duration: 200
      easing.type: Easing.OutCubic
    }
  }
}
