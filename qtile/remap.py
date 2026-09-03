# ═══ imports ═══════════════════════════════════════════════════════════════
# qtile core
from libqtile.config import Click, Drag, Key
from libqtile.lazy import lazy

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
