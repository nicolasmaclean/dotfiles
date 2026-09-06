vim.opt.guicursor = "i:ver25"

vim.opt.nu = true
vim.opt.relativenumber = true

-- count display rows, not buffer lines, so the numbers match gj/gk on wrapped
-- text. "%s" keeps the sign column; falls back to normal behaviour when nowrap.
function _G.display_relnum()
  local sp = vim.fn.screenpos(0, vim.v.lnum, 1)
  if sp.row == 0 then return "" end
  local delta = (sp.row + vim.v.virtnum) - vim.fn.winline()
  local n = delta == 0 and vim.v.lnum or math.abs(delta)
  return "%s" .. string.format("%3d ", n)
end
vim.opt.statuscolumn = "%!v:lua.display_relnum()"

-- cursor movement only redraws the number column when the cursor's *buffer*
-- line changes, so moving between rows of one wrapped line left stale numbers.
-- re-setting the option marks the column dirty; guarded so it only fires when
-- the cursor actually changes display row.
vim.api.nvim_create_autocmd({ "CursorMoved", "CursorMovedI" }, {
  group = vim.api.nvim_create_augroup("display_relnum", { clear = true }),
  callback = function()
    if not vim.wo.wrap then return end
    local row = vim.fn.winline()
    if row ~= vim.w.display_relnum_row then
      vim.w.display_relnum_row = row
      vim.wo.statuscolumn = vim.wo.statuscolumn
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
