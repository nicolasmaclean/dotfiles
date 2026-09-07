vim.opt_local.wrap = true
vim.opt_local.linebreak = true
vim.opt_local.breakindent = true

-- wrapped text: number the display rows, not the buffer lines (display_relnum
-- in lua/nick/set.lua). window-local, so other buffers keep the built-in column.
vim.b.display_relnum = true
vim.opt_local.statuscolumn = "%!v:lua.display_relnum()"
