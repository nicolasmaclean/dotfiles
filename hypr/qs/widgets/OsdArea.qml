pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services

ListView {
  id: column

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

  implicitWidth: Theme.notificationWidth
  spacing: 5
  interactive: false

  // OSD Cards
  Component {
    id: volumeCard
    SliderCard {
      title: "Volume"
      value: Audio.volume
      onMoved: value => Audio.setVolume(value)
    }
  }

  Component {
    id: micCard
    SliderCard {
      title: "Mic"
      value: 0.5
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
