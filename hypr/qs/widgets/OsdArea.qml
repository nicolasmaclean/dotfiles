import QtQuick
import Quickshell

import qs.services

Item {
  implicitWidth: card.implicitWidth
  implicitHeight: card.implicitHeight
  visible: Osd.shown

  SliderCard {
    id: card
    title: "Volume"
    value: Audio.volume
    onMoved: value => Audio.setVolume(value)
  }
}
