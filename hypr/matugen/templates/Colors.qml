pragma Singleton
import QtQuick
import Quickshell

Singleton {
    // Primary
    readonly property color oonPrimary: "{{colors.on_primary.default.hex}}"
    readonly property color oonPrimaryContainer: "{{colors.on_primary_container.default.hex}}"
    readonly property color oonPrimaryFixed: "{{colors.on_primary_fixed.default.hex}}"
    readonly property color oonPrimaryFixedVariant: "{{colors.on_primary_fixed_variant.default.hex}}"
    readonly property color primary: "{{colors.primary.default.hex}}"
    readonly property color primaryContainer: "{{colors.primary_container.default.hex}}"
    readonly property color primaryFixed: "{{colors.primary_fixed.default.hex}}"
    readonly property color primaryFixedDim: "{{colors.primary_fixed_dim.default.hex}}"

    // Secondary
    readonly property color oonSecondary: "{{colors.on_secondary.default.hex}}"
    readonly property color oonSecondaryContainer: "{{colors.on_secondary_container.default.hex}}"
    readonly property color oonSecondaryFixed: "{{colors.on_secondary_fixed.default.hex}}"
    readonly property color oonSecondaryFixedVariant: "{{colors.on_secondary_fixed_variant.default.hex}}"
    readonly property color secondary: "{{colors.secondary.default.hex}}"
    readonly property color secondaryContainer: "{{colors.secondary_container.default.hex}}"
    readonly property color secondaryFixed: "{{colors.secondary_fixed.default.hex}}"
    readonly property color secondaryFixedDim: "{{colors.secondary_fixed_dim.default.hex}}"

    // Tertiary
    readonly property color oonTertiary: "{{colors.on_tertiary.default.hex}}"
    readonly property color oonTertiaryContainer: "{{colors.on_tertiary_container.default.hex}}"
    readonly property color oonTertiaryFixed: "{{colors.on_tertiary_fixed.default.hex}}"
    readonly property color oonTertiaryFixedVariant: "{{colors.on_tertiary_fixed_variant.default.hex}}"
    readonly property color tertiary: "{{colors.tertiary.default.hex}}"
    readonly property color tertiaryContainer: "{{colors.tertiary_container.default.hex}}"
    readonly property color tertiaryFixed: "{{colors.tertiary_fixed.default.hex}}"
    readonly property color tertiaryFixedDim: "{{colors.tertiary_fixed_dim.default.hex}}"

    // Error
    readonly property color error: "{{colors.error.default.hex}}"
    readonly property color errorContainer: "{{colors.error_container.default.hex}}"
    readonly property color oonError: "{{colors.on_error.default.hex}}"
    readonly property color oonErrorContainer: "{{colors.on_error_container.default.hex}}"

    // Surface / background
    readonly property color background: "{{colors.background.default.hex}}"
    readonly property color oonBackground: "{{colors.on_background.default.hex}}"
    readonly property color oonSurface: "{{colors.on_surface.default.hex}}"
    readonly property color oonSurfaceVariant: "{{colors.on_surface_variant.default.hex}}"
    readonly property color surface: "{{colors.surface.default.hex}}"
    readonly property color surfaceBright: "{{colors.surface_bright.default.hex}}"
    readonly property color surfaceContainer: "{{colors.surface_container.default.hex}}"
    readonly property color surfaceContainerHigh: "{{colors.surface_container_high.default.hex}}"
    readonly property color surfaceContainerHighest: "{{colors.surface_container_highest.default.hex}}"
    readonly property color surfaceContainerLow: "{{colors.surface_container_low.default.hex}}"
    readonly property color surfaceContainerLowest: "{{colors.surface_container_lowest.default.hex}}"
    readonly property color surfaceDim: "{{colors.surface_dim.default.hex}}"
    readonly property color surfaceTint: "{{colors.surface_tint.default.hex}}"
    readonly property color surfaceVariant: "{{colors.surface_variant.default.hex}}"

    // Inverse
    readonly property color inverseOnSurface: "{{colors.inverse_on_surface.default.hex}}"
    readonly property color inversePrimary: "{{colors.inverse_primary.default.hex}}"
    readonly property color inverseSurface: "{{colors.inverse_surface.default.hex}}"

    // Misc
    readonly property color outline: "{{colors.outline.default.hex}}"
    readonly property color outlineVariant: "{{colors.outline_variant.default.hex}}"
    readonly property color scrim: "{{colors.scrim.default.hex}}"
    readonly property color shadow: "{{colors.shadow.default.hex}}"
    readonly property color sourceColor: "{{colors.source_color.default.hex}}"
}
