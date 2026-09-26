pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Services.Pipewire

Singleton {
  id: root

  readonly property var sink: Pipewire.defaultAudioSink
  readonly property var source: Pipewire.defaultAudioSource

  readonly property real volume: sink?.audio?.volume ?? 0
  readonly property bool muted: sink?.audio?.muted ?? true
  readonly property bool source_on: !source?.audio?.muted ?? false

  readonly property string volumeGlyph: {
    if (muted) {
      return "󰝟"
    }
    if (volume === 0) {
      return "󰕿"
    }
    if (volume < 0.5) {
      return "󰖀"
    }
    return "󰕾"
  }

  readonly property string micGlyph: {
    return source_on ? "󰍬" : "󰍭"
  }

  function setVolume(v) {
    if (sink?.audio)
      sink.audio.volume = v
  }

  // make sure pipewire properties live (propagate changes automatically)
  PwObjectTracker {
    objects: [Pipewire.defaultAudioSink, Pipewire.defaultAudioSource]
  }
}
