pragma Singleton
import QtQuick
import Quickshell

Singleton {
    readonly property color surface: "{{colors.surface.default.hex}}"
    readonly property color surfaceContainer: "{{colors.surface_container.default.hex}}"
    readonly property color surfaceContainerHigh: "{{colors.surface_container_high.default.hex}}"
    readonly property color oonSurface: "{{colors.on_surface.default.hex}}"
    readonly property color oonSurfaceVariant: "{{colors.on_surface_variant.default.hex}}"
    readonly property color primary: "{{colors.primary.default.hex}}"
    readonly property color oonPrimary: "{{colors.on_primary.default.hex}}"
    readonly property color error: "{{colors.error.default.hex}}"
}
