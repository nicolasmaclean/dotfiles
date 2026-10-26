# The parts of CachyOS's zsh config (/usr/share/cachyos-zsh-config) worth
# keeping, minus powerlevel10k: starship draws the prompt instead, and running
# both means two sets of prompt hooks fighting over PROMPT.

export ZSH=/usr/share/oh-my-zsh
export FZF_BASE=/usr/share/fzf
ZSH_THEME=""                    # starship, below
DISABLE_MAGIC_FUNCTIONS=true    # keeps pasted URLs from getting mangled
ENABLE_CORRECTION=true
COMPLETION_WAITING_DOTS=true
CASE_SENSITIVE=true             # path completion matches case exactly
plugins=(git fzf extract)
source $ZSH/oh-my-zsh.sh

source ~/dotfiles/.shellrc

command -v starship >/dev/null && eval "$(starship init zsh)"

# Fish-like autosuggestions and highlighting. syntax-highlighting has to come
# after everything else that defines widgets, and history-substring-search
# after it.
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh

# up/down search history for whatever is already typed
bindkey "${terminfo[kcuu1]}" history-substring-search-up
bindkey "${terminfo[kcud1]}" history-substring-search-down
