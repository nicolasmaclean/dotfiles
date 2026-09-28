pragma Singleton

import QtQuick
import Quickshell

Singleton {
  id: root

  property bool shown: false
  property bool pinned: false
  property var _lastSink: null

  function pin(): void {
    shown = !shown
    pinned = shown
    timer.stop()
    // TODO: update visibility
  }

  function notify(): void {
    if (!Audio.sink?.ready || Audio.sink !== _lastSink) {
      _lastSink = Audio.sink?.ready ? Audio.sink : null
      return
    }
    if (pinned)
      return
    shown = true
    if (timer.running) {
      timer.restart()
    } else {
      timer.start()
    }
  }

  Connections {
    target: Audio

    function onVolumeChanged() {
      root.notify()
    }
    function onMutedChanged() {
      root.notify()
    }
  }

  Timer {
    id: timer
    interval: 2000
    onTriggered: root.shown = false
  }
}
