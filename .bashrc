# zsh is the login shell (.zshrc); this is for the bash that's still around.
source ~/dotfiles/.shellrc

command -v starship >/dev/null && eval "$(starship init bash)"
