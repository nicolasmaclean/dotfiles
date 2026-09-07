vim.opt.guicursor = "i:ver25"

vim.opt.nu = true
vim.opt.relativenumber = true

-- count display rows, not buffer lines, so the numbers match gj/gk on wrapped
-- text. "%s" keeps the sign column. opted into per-window (see
-- after/ftplugin/markdown.lua) rather than globally: as a global 'statuscolumn'
-- this also ran in telescope's one-line prompt, where v:lnum outruns the buffer
-- and screenpos() throws E966.
function _G.display_relnum()
  local lnum = vim.v.lnum
  if lnum < 1 or lnum > vim.api.nvim_buf_line_count(0) then return "" end
  local sp = vim.fn.screenpos(0, lnum, 1)
  if sp.row == 0 then return "" end
  local delta = (sp.row + vim.v.virtnum) - vim.fn.winline()
  local n = delta == 0 and lnum or math.abs(delta)
  return "%s" .. string.format("%3d ", n)
end

-- ftplugins run on FileType, which does not fire again when an already-loaded
-- buffer is opened in a second window; reapply there.
vim.api.nvim_create_autocmd("BufWinEnter", {
  group = vim.api.nvim_create_augroup("display_relnum_apply", { clear = true }),
  callback = function()
    if vim.b.display_relnum then
      vim.opt_local.statuscolumn = "%!v:lua.display_relnum()"
    end
  end,
})

-- cursor movement only redraws the number column when the cursor's *buffer*
-- line changes, so moving between rows of one wrapped line left stale numbers.
-- re-setting the option marks the column dirty; guarded so it only fires when
-- the cursor actually changes display row.
vim.api.nvim_create_autocmd({ "CursorMoved", "CursorMovedI" }, {
  group = vim.api.nvim_create_augroup("display_relnum", { clear = true }),
  callback = function()
    if not vim.wo.wrap or not vim.b.display_relnum then return end
    local row = vim.fn.winline()
    if row ~= vim.w.display_relnum_row then
      vim.w.display_relnum_row = row
      -- opt_local, not vim.wo: the latter writes the global value too, so every
      -- window opened afterwards (telescope's prompt included) would inherit it
      vim.opt_local.statuscolumn = vim.wo.statuscolumn
    end
  end,
})

vim.opt.tabstop = 2
vim.opt.softtabstop = 2  
vim.opt.shiftwidth = 2 
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.wrap = false

vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undodir = vim.fn.stdpath("state") .. "/undodir"

vim.opt.hlsearch = false
vim.opt.incsearch = true

vim.opt.termguicolors = true

vim.opt.scrolloff = 8
vim.opt.signcolumn = "yes"
vim.opt.isfname:append("@-@")

vim.opt.colorcolumn = "80"

vim.g.mapleader = " "

-- vim.diagnostic.config({virtual_text = true })
vim.diagnostic.config({
  virtual_text = { spacing = 2, prefix = "●" },
  underline = true,
  update_in_insert = true,   -- lint while typing, not just on InsertLeave
  severity_sort = true,
  signs = false,
})
