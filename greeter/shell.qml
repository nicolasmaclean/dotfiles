pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Services.Greetd

import qs

ShellRoot {
  id: root

  property string prompt: ""
  property bool passwordSent: false
  property bool echoResponse: false

  FloatingWindow {
    Image {
      fillMode: Image.PreserveAspectCrop
      anchors.fill: parent
      source: "login.png"
    }

    ColumnLayout {
      x: (parent.width - width) / 2 - 30
      y: parent.height * 0.53
      width: 300

      GreeterField {
        id: username
        placeholderText: "username"
        icon: "\u{f0009}"
        focus: true
        onAccepted: password.forceActiveFocus()
      }

      GreeterField {
        id: password
        placeholderText: "password"
        icon: "\u{f033e}"
        echoMode: TextInput.Password
        onAccepted: root.submit()
      }

      GreeterField {
        id: answer
        placeholderText: "Prompt"
        icon: "\u{f0306}"
        visible: root.prompt !== ""
        onAccepted: root.submit()
        echoMode: root.echoResponse ? TextInput.Normal : TextInput.Password
      }

      Text {
        id: status
        text: ""
        font.family: "MesloLGS Nerd Font"
        Layout.fillWidth: true
        visible: status.text !== ""
        leftPadding: 35
      }

      Button {
        text: "submit"
        Layout.alignment: Qt.AlignHCenter
        leftPadding: 20
        rightPadding: 34
        onClicked: root.submit()
        Keys.onReturnPressed: clicked()

        Text {
          anchors.right: parent.right
          anchors.rightMargin: 16
          anchors.verticalCenter: parent.verticalCenter
          text: "\u{f0054}"
          color: Theme.textDim
          font.family: "MesloLGS Nerd Font"
        }

        background: Rectangle {
          implicitHeight: 28
          radius: implicitHeight / 2
          color: Theme.frame
          border.width: 2
          border.color: parent.activeFocus ? Theme.accent : "transparent"
        }
      }
    }

    RowLayout {
      anchors.bottom: parent.bottom
      anchors.right: parent.right
      anchors.bottomMargin: 6

      PowerButton {
        buttonText: "\u{F04B2}"
        ToolTip.text: "suspend"
        onClicked: Quickshell.execDetached(["systemctl", "suspend"])
      }

      PowerButton {
        buttonText: "\u{F0709}"
        ToolTip.text: "reboot"
        onClicked: Quickshell.execDetached(["systemctl", "reboot"])
      }

      PowerButton {
        buttonText: "\u{F0425}"
        ToolTip.text: "shutdown"
        onClicked: Quickshell.execDetached(["systemctl", "poweroff"])
      }
    }
  }

  component GreeterField: TextField {
    property string icon

    Layout.fillWidth: true
    color: Theme.text
    placeholderTextColor: Theme.textDim
    leftPadding: 36
    topPadding: 6
    bottomPadding: 6

    Text {
      anchors.left: parent.left
      anchors.leftMargin: 16
      anchors.verticalCenter: parent.verticalCenter
      text: parent.icon
      color: Theme.textDim
      font.family: "MesloLGS Nerd Font"
    }

    background: Rectangle {
      implicitHeight: 34
      radius: implicitHeight / 2
      color: Theme.frame
      border.width: 2
      border.color: parent.activeFocus ? Theme.accent : "transparent"
    }
  }

  component PowerButton: Button {
    id: powerButton
    required property string buttonText

    ToolTip.visible: ToolTip.text !== "" && hovered
    ToolTip.delay: 500

    leftPadding: 5
    rightPadding: 8
    topPadding: -5
    bottomPadding: -5
    focusPolicy: Qt.NoFocus

    contentItem: Text {
      text: powerButton.buttonText
      color: powerButton.hovered ? "#ffffff" : "#dddddd"
      font.pixelSize: 44
      font.family: "MesloLGS Nerd Font"
      horizontalAlignment: Text.AlignHCenter
      verticalAlignment: Text.AlignVCenter

      layer.enabled: true
      layer.effect: MultiEffect {
        shadowEnabled: true
        shadowBlur: 0.2
        shadowHorizontalOffset: 2
        shadowVerticalOffset: 2
      }
    }

    background: Rectangle {
      color: "transparent"
    }

    HoverHandler {
      cursorShape: Qt.PointingHandCursor
    }
  }

  function submit(): void {
    if (root.prompt !== "") {
      status.text = "checking"
      Greetd.respond(answer.text)
      root.prompt = ""
      answer.text = ""
      return
    }

    if (!Greetd.available) {
      status.text = "Greetd is not available"
      return
    }

    status.text = ""
    if (!username.text) {
      return
    }

    if (Greetd.state !== GreetdState.Inactive) {
      return
    }

    Greetd.createSession(username.text)
  }

  Connections {
    target: Greetd

    function onAuthMessage(message, error, responseRequired, echoResponse) {
      if (!responseRequired) {
        status.text = message
        return
      }

      if (!echoResponse && !root.passwordSent) {
        Greetd.respond(password.text)
        root.passwordSent = true
        return
      }

      root.prompt = message
      status.text = message
      root.echoResponse = echoResponse
      answer.forceActiveFocus()
    }

    function onReadyToLaunch() {
      lastUser.setText(username.text)
      Greetd.launch(["systemd-cat", "-t", "uwsm-launch", "uwsm", "start", "-e", "-D", "Hyprland", "/usr/local/share/hyprland-dotfiles/hyprland.desktop"])
    }

    function onAuthFailure(message) {
      status.text = message
      root.prompt = password.text = answer.text = ""
      root.passwordSent = false
      password.forceActiveFocus()
    }

    function onError(message) {
      status.text = message
      root.prompt = password.text = answer.text = ""
      root.passwordSent = false
      password.forceActiveFocus()

      if (Greetd.state !== GreetdState.Inactive)
        Greetd.cancelSession()
    }
  }

  FileView {
    id: lastUser
    path: Quickshell.cachePath("last-user")
    blockWrites: true

    onLoaded: {
      username.text = text().trim()
      if (username.text)
        password.forceActiveFocus()
    }
  }
}
