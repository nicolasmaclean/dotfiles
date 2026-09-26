import QtQuick
import Quickshell
import Quickshell.Io

import qs
import qs.services

Text {
  text: Time.time
  color: Theme.text

  TapHandler {
    acceptedButtons: Qt.LeftButton
    onTapped: calendar.running = !calendar.running
  }

  Process {
    id: calendar
    command: Apps.calendar
  }
}
