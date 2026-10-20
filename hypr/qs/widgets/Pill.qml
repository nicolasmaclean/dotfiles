import QtQuick
import QtQuick.Layouts
import Quickshell

import qs

RaisedButtonBase {
  default property alias content: pillRow.data

  implicitWidth: pillRow.implicitWidth + Theme.pillPadding * 2
  implicitHeight: pillRow.implicitHeight
  radius: height / 2
  color: MyColors.surfaceDim

  RowLayout {
    id: pillRow
    anchors.centerIn: parent
  }
}
