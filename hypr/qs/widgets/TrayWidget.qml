import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.SystemTray
import Quickshell.Widgets

import qs
import qs.services

Repeater {
  model: ScriptModel {
    values: SystemTray.items.values.filter(i => !Tray.has(i.id))
  }

  delegate: TrayIcon {}
}
