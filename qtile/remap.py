# ═══ imports ═══════════════════════════════════════════════════════════════
# qtile core
from libqtile.config import Click, Drag, Key
from libqtile.lazy import lazy

import brightness

# ═══ misc ═══════════════════════════════════════════════════════════════
terminal = "alacritty"  # only terminal installed on this box
launcher = "rofi -show drun"

# ═══ keybindings ═══════════════════════════════════════════════════════════════
mod = "mod1"  # Alt: keyboard modifier for every Key() binding
mod_mouse = "mod4"  # Windows key: blender and other 3d software uses alt+mouse, so leave mod+mouse to windows key

keys = [
    # --- window focus ---
    Key([mod], "h", lazy.layout.left(), desc="Move focus left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move focus to next window"),
    # --- move windows ---
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # --- resize ---
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset window sizes"),
    Key(
        [mod, "shift"],
        "s",
        lazy.layout.toggle_split(),
        desc="Stack/unstack the current column",
    ),
    # --- launching ---
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    Key([mod], "r", lazy.spawn(launcher), desc="Search and launch an app"),
    # --- layout / window management ---
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating"),
    # --- media keys ---
    # Volume rides the bar widget instead of calling wpctl directly: the widget
    # already owns the wpctl commands (config.py), and driving it from here
    # redraws the bar at once rather than waiting on its next poll.
    Key(
        [],
        "XF86AudioRaiseVolume",
        lazy.widget["volume"].increase_vol(),
        desc="Raise volume",
    ),
    Key(
        [],
        "XF86AudioLowerVolume",
        lazy.widget["volume"].decrease_vol(),
        desc="Lower volume",
    ),
    Key([], "XF86AudioMute", lazy.widget["volume"].mute(), desc="Toggle mute"),
    # Nothing in the bar tracks the mic, so this one talks to wpctl itself.
    Key(
        [],
        "XF86AudioMicMute",
        lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
        desc="Toggle mic mute",
    ),
    # Nothing in the bar tracks the backlight, so these call brightness.py,
    # which owns the step, the -e curve and the floor and posts the dunst
    # notification that replaced the meter.
    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.function(brightness.up),
        desc="Raise screen brightness",
    ),
    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.function(brightness.down),
        desc="Lower screen brightness",
    ),
    # --- screenshots ---
    # Flameshot, configured in ../flameshot/flameshot.ini: Print dims the
    # screen and waits for a region to be dragged, then offers the annotation
    # toolbar; shift+Print grabs the whole desktop with no interaction at all.
    #
    # Both need session/flameshot.service resident to be able to copy anything
    # - see the note in that unit - and both rely on the config for where the
    # file lands, so there is no --path here to drift out of step with it.
    #
    # --clipboard is what makes the capture the *clipboard's*; saveAfterCopy in
    # the config is what additionally puts it on disk. Neither key needs a
    # shell: flameshot is doing all the work.
    Key(
        [],
        "Print",
        lazy.spawn("flameshot gui --clipboard"),
        desc="Screenshot a region, with annotation",
    ),
    Key(
        ["shift"],
        "Print",
        lazy.spawn("flameshot full --clipboard"),
        desc="Screenshot the whole desktop",
    ),
    # --- input sources ---
    # Alt+Shift+space, not Alt+space: that one is taken by layout.next() above.
    # Goes through the bar widget rather than calling ibus directly, for the
    # same reason the volume keys do - the widget owns the engine list and the
    # cycle order, and driving it from here redraws the label immediately.
    Key(
        [mod, "shift"],
        "space",
        lazy.widget["keyboard"].next_layout(),
        desc="Cycle input source (US / pinyin)",
    ),
    # --- session ---
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shut down qtile"),
]

mouse = [
    Drag(
        [mod_mouse],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod_mouse],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
    Click([mod_mouse], "Button2", lazy.window.bring_to_front()),
]


# --- group switching ---
# A function, not a module-level loop: the groups are defined in config.py, and
# importing them back here would be a cycle. config.py calls this and extends
# `keys` with the result.
def group_keys(groups):
    """mod+N to focus group N, mod+shift+N to throw the focused window there."""
    bindings = []
    for i in groups:
        bindings.extend(
            [
                Key(
                    [mod],
                    i.name,
                    lazy.group[i.name].toscreen(),
                    desc=f"Switch to group {i.name}",
                ),
                Key(
                    [mod, "shift"],
                    i.name,
                    lazy.window.togroup(i.name, switch_group=True),
                    desc=f"Move focused window to group {i.name}",
                ),
            ]
        )
    return bindings
