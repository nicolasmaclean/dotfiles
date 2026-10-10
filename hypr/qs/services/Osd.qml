pragma Singleton

import QtQuick
import Quickshell

import qs.services

Singleton {
  id: root

  enum Kind {
    Volume,
    Mic,
    Brightness,
    Nightlight,
    Power,
    Wifi,
    Bluetooth
  }

  component Entry: QtObject {
    id: entry

    required property int kind
    property bool pinned: false
    property bool shown: false
    property bool hovered: false
    property int shownAt

    function show(pin): void {
      pinned = pinned || pin
      if (!shown) {
        if (pinned) {
          entry.shownAt = --Osd._pinSeq
        } else {
          entry.shownAt = ++Osd._notificationSeq
        }
      }
      shown = true
      if (timer.running)
        timer.restart()
    }

    function dismiss() {
      pinned = false
      shown = false
    }

    function toggle() {
      if (shown) {
        dismiss()
        return
      }
      show(true)
    }

    readonly property Timer timer: Timer {
      interval: 2000
      running: entry.shown && !entry.pinned && !entry.hovered
      onTriggered: entry.dismiss()
    }
  }

  property int _notificationSeq: 0
  property int _pinSeq: 0

  readonly property Entry volume: Entry {
    kind: Osd.Kind.Volume
  }
  readonly property Entry mic: Entry {
    kind: Osd.Kind.Mic
  }
  readonly property Entry nightlight: Entry {
    kind: Osd.Kind.Nightlight
  }
  readonly property Entry brightness: Entry {
    kind: Osd.Kind.Brightness
  }
  readonly property Entry power: Entry {
    kind: Osd.Kind.Power
  }

  readonly property list<Entry> entries: [volume, mic, nightlight, brightness]
  readonly property list<Entry> quickEntries: [power]

  Connections {
    id: audioConnections
    target: Audio
    property var _lastSink

    function onVolumeChanged() {
      notify()
    }
    function onMutedChanged() {
      notify()
    }

    function notify(): void {
      if (!Audio.sink?.ready || Audio.sink !== audioConnections._lastSink) {
        audioConnections._lastSink = Audio.sink?.ready ? Audio.sink : null
        return
      }
      root.volume.show(false)
    }
  }
}
