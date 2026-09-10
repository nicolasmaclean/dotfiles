#!/usr/bin/env bash
#
# The single entry point on a fresh CachyOS install (minimal profile, no
# desktop). Run as the normal user — it calls sudo itself for the steps that
# need it:
#
#     curl -fsSL https://raw.githubusercontent.com/nicolasmaclean/dotfiles/main/ansible/bootstrap.sh | bash
#
# or, from an existing checkout, just `ansible/bootstrap.sh`. Extra arguments
# are passed through to ansible-playbook, so a first run on a machine that
# already has a desktop should be:
#
#     ansible/bootstrap.sh --check --diff
#
# The clone is HTTPS and stays HTTPS: a fresh box has no SSH key, and nothing
# here needs one. The `identity` role generates a per-host key and prints it;
# registering it anywhere is yours to do, whenever.
set -euo pipefail

REPO_HTTPS="https://github.com/nicolasmaclean/dotfiles.git"
DOTFILES="${DOTFILES:-$HOME/dotfiles}"

# `ansible`, not `ansible-core`: the full package is what ships
# community.general and community.crypto, which is where pacman:, ini_file:,
# npm: and openssh_keypair: come from. requirements.yml pins them anyway, and
# is genuinely load-bearing for kewlfft.aur, which is bundled with nothing.
#
# base-devel and paru are named here as well as in the roles, and the
# duplication is deliberate: roles/base installs base-devel and roles/aur
# installs paru, so this line is what makes the *first* run identical to a run
# that reaches those roles some other way. Neither is preinstalled on the
# minimal CachyOS profile — the ISO does not ship paru, verified on the VM,
# whatever its package list implies. --needed is the --noconfirm-safe
# idempotent form; without it pacman reinstalls on every run.
sudo pacman -Sy --needed --noconfirm ansible git base-devel paru

if [ -d "$DOTFILES/.git" ]; then
    echo "==> $DOTFILES exists, updating"
    git -C "$DOTFILES" pull --ff-only
else
    echo "==> cloning into $DOTFILES"
    git clone "$REPO_HTTPS" "$DOTFILES"
fi

# ansible.cfg is only read from the current directory, so this cd is what makes
# the inventory path and transport=local take effect.
cd "$DOTFILES/ansible"

ansible-galaxy collection install -r requirements.yml

# Every host in the inventory is local, so a run that is not limited to this
# machine would apply the other machine's host_vars to it. Fail before the
# playbook rather than provision the wrong box.
HOST="$(hostname)"
if ! ansible-inventory --host "$HOST" >/dev/null 2>&1; then
    echo "hostname '$HOST' is not in inventory/hosts.yml." >&2
    echo "Add it there and write inventory/host_vars/$HOST.yml first." >&2
    exit 1
fi

ansible-playbook site.yml --limit "$HOST" --ask-become-pass "$@"

cat <<NEXT

==> done. One manual step remains, once per host:
      Spotify: register the app, write
      ~/.config/qtile-spotify/credentials.json (0600), and run
        python3 ~/.config/qtile/spotify_auth.py
NEXT
