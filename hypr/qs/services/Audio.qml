pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Services.Pipewire

Singleton {
  id: root

  readonly property var sink: Pipewire.defaultAudioSink
  readonly property var source: Pipewire.defaultAudioSource
  readonly property var sinks: Pipewire.nodes.values.filter(n => n.audio && n.isSink && !n.isStream)
  readonly property var sources: Pipewire.nodes.values.filter(n => n.audio && !n.isSink && !n.isStream)

  readonly property real volume: sink?.audio?.volume ?? 0
  readonly property bool muted: sink?.audio?.muted ?? true
  readonly property real sourceVolume: source?.audio?.volume ?? 0
  readonly property bool sourceOn: (!source?.audio?.muted) ?? false

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
    return sourceOn ? "󰍬" : "󰍭"
  }

  function nodeLabel(n): string {
    return n?.description ?? n?.nickname ?? n?.name ?? "???"
  }

  function setVolume(v) {
    if (sink?.audio)
      sink.audio.volume = v
  }

  function setSink(n) {
    Pipewire.preferredDefaultAudioSink = n
  }

  function toggleMuted() {
    if (sink?.audio)
      sink.audio.muted = !sink.audio.muted
  }

  function setSourceVolume(v) {
    if (source?.audio)
      source.audio.volume = v
  }

  function toggleSourceMuted() {
    if (source?.audio)
      source.audio.muted = !source.audio.muted
  }

  function setSource(n) {
    Pipewire.preferredDefaultAudioSource = n
  }

  // make sure pipewire properties live (propagate changes automatically)
  PwObjectTracker {
    objects: [Pipewire.defaultAudioSink, Pipewire.defaultAudioSource]
  }
}
