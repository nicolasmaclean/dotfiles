alias vim="nvim"

# prettier git log
alias gitl="git log --graph --abbrev-commit --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(auto)%d%C(reset)' --all"
# prettier git log with per-commit file summary
gitll() {
  local color=always grn='\033[32m' ylw='\033[33m' red='\033[31m' cyn='\033[36m' dim='\033[2m' rst='\033[0m'
  if [ ! -t 1 ]; then
    color=never; grn=; ylw=; red=; cyn=; dim=; rst=
  fi
  git log --all --abbrev-commit --decorate --color=$color \
    --format=format:$'\x01%C(bold blue)%h%C(reset) - %C(bold cyan)%aD%C(reset) %C(bold green)(%ar)%C(reset)%C(auto)%d%C(reset)\x02%C(white)%s%C(reset) %C(dim white)- %an%C(reset)' \
    --name-status "$@" |
  awk -v max=10 -v grn="$grn" -v ylw="$ylw" -v red="$red" -v cyn="$cyn" -v dim="$dim" -v rst="$rst" '
    function flush(   i, out) {
      if (!have) return
      print header
      out = ""
      if (n["A"]) out = out sep(out) grn n["A"] " created" rst
      if (n["M"]) out = out sep(out) ylw n["M"] " modified" rst
      if (n["D"]) out = out sep(out) red n["D"] " deleted" rst
      if (n["R"]) out = out sep(out) cyn n["R"] " renamed" rst
      if (out == "") out = dim "no file changes" rst
      print pad out
      for (i = 1; i <= nf && i <= max; i++) print pad files[i]
      if (nf > max) printf "%s%s... and %d more%s\n", pad, dim, nf - max, rst
      print ""
      have = 0; nf = 0; split("", n); split("", files)
    }
    function sep(s) { return s == "" ? "" : dim ", " rst }
    function label(c) {
      return c == "A" ? grn "added   " rst : \
             c == "M" ? ylw "modified" rst : \
             c == "D" ? red "deleted " rst : \
             c == "R" ? cyn "renamed " rst : \
             c == "C" ? cyn "copied  " rst : sprintf("%-8s", c)
    }
    BEGIN { pad = "          " }
    /^\x01/ {
      flush()
      header = substr($0, 2)
      sub(/\x02/, "\n" pad, header)
      have = 1
      next
    }
    /^[ACDMRTUX][0-9]*\t/ {
      c = substr($0, 1, 1)
      n[c]++
      nf++
      path = $0
      sub(/^[^\t]*\t/, "", path)
      gsub(/\t/, " " dim "->" rst " ", path)
      files[nf] = label(c) "  " path
    }
    END { flush() }
  ' |
  { if [ -t 1 ]; then LESS="${LESS:-FRX}" $(git var GIT_PAGER 2>/dev/null || echo less); else cat; fi; }
}
