# ═══ imports ═══════════════════════════════════════════════════════════════
# qtile core
from libqtile.config import Click, Drag, Key
from libqtile.lazy import lazy
from libqtile.widget.backlight import ChangeDirection

# ═══ misc ═══════════════════════════════════════════════════════════════
terminal = "alacritty"  # only terminal installed on this box
launcher = "rofi -show drun"

# ImageMagick's `import` plus xclip, because that is what is already on this
# box - no flameshot, maim or scrot - and between them they cover both shots
# without pulling in another package.
#
# Every shot lands in ~/Pictures/Screenshots, and the file is the part that is
# always there: the save happens before xclip is ever called, so the shot
# survives whatever the clipboard does. The capture goes to a temp file first
# rather than straight down a pipe, so a cancelled or empty grab leaves nothing
# behind - a drag that ends where it started is a 0-byte PNG, and that must not
# become a file. mktemp makes that file 0600, hence the chmod: a screenshot is
# an ordinary file and should not be readable only by its owner.
#
# The clipboard copy is best-effort, and deliberately not trusted. xclip cannot
# serve a selection much past 1MB - measured on this box, 774KB pastes and
# 1.1MB hangs the receiving app - and a full-screen PNG at 1920x1080 is around
# 1.2MB, so it is exactly the full-screen shots that fall off the end. Region
# shots are almost always well under. xclip forks and holds the selection
# itself, so nothing here has to stay alive for a paste that does work.
#
# No notify-send confirmation: there is no notification daemon on this box
# (org.freedesktop.Notifications is unclaimed), so the call would only ever
# fail silently. The shot appearing on the clipboard is the feedback.
#
# The capture flags come in as "$@" - see _screenshot() below - so the two
# bindings share one script: no args means the interactive crosshair,
# "-window root" means the whole screen.
_SCREENSHOT_SH = """\
dir="$HOME/Pictures/Screenshots"
tmp=$(mktemp --suffix=.png) || exit 1
if import "$@" png:"$tmp" && [ -s "$tmp" ]; then
    mkdir -p "$dir"
    out="$dir/Screenshot from $(date '+%Y-%m-%d %H-%M-%S').png"
    mv "$tmp" "$out"
    chmod 644 "$out"
    xclip -selection clipboard -target image/png -i "$out"
else
    rm -f "$tmp"
fi
"""


def _screenshot(*args):
    """Run _SCREENSHOT_SH with `args` as the flags handed to import."""
    # The "screenshot" between the script and the flags is $0: sh -c takes the
    # argument after the script as the shell's own name, and without it the
    # first real flag would be swallowed into $0 instead of "$@".
    return lazy.spawn(["sh", "-c", _SCREENSHOT_SH, "screenshot", *args])


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
    # Driven through the bar widget rather than by spawning brightnessctl, so
    # the meter and the keys cannot disagree: the widget owns the step, the
    # exponential curve and the floor, and still shells out to brightnessctl -
    # which writes /sys/class/backlight unprivileged thanks to the
    # brightness-udev rule plus video-group membership.
    #
    # -e puts the 5% steps on an exponential curve: the panel's response to raw
    # values is perceptually non-linear, so linear steps crawl at the top and
    # lurch at the bottom. The curve makes each press feel like the same change.
    # That curve has no floor of its own - "brightnessctl -e set 5%-" walks
    # happily down to a raw 0 and a black panel - so the widget's
    # min_brightness is what stops the last press going dark.
    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.widget["brightness"].change_backlight(ChangeDirection.UP),
        desc="Raise screen brightness",
    ),
    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.widget["brightness"].change_backlight(ChangeDirection.DOWN),
        desc="Lower screen brightness",
    ),
    # --- screenshots ---
    # Print alone takes the whole screen; shift+Print hands over the crosshair
    # to drag a region out, and a plain click there grabs the window under the
    # pointer instead.
    Key([], "Print", _screenshot("-window", "root"), desc="Screenshot the screen"),
    Key(["shift"], "Print", _screenshot(), desc="Screenshot a region or window"),
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
