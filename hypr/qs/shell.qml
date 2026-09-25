import QtQuick
//patch in default fonts (as opposed to symlink from .config to here)
//@ pragma Env FONTCONFIG_FILE=~/dotfiles/hypr/qs/fonts.conf
import Quickshell
import qs.widgets

Scope {
    NotificationArea {
    }

    Variants {
        model: Quickshell.screens

        // draw taskbar
        Scope {
            id: screenScope

            required property var modelData

            Frame {
                screen: screenScope.modelData
            }

            Taskbar {
                screen: screenScope.modelData
            }

        }

    }

}
