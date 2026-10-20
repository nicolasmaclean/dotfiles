pragma Singleton

import QtQuick
import Quickshell

Singleton {
  id: root

  property bool open: false

  function toggle(): void {
    open = !open
  }
}
