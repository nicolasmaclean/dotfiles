-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)


-- Make sure to setup `mapleader` and `maplocalleader` before
-- loading lazy.nvim so that mappings are correct.
-- This is also a good place to setup other settings (vim.opt)
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"


-- EDITOR --

vim.o.relativenumber = true

vim.o.wrap = false
vim.o.expandtab = true
vim.o.tabstop = 4
vim.o.shiftwidth = 2

vim.o.signcolumn = 'yes'
vim.cmd("syntax on")
vim.o.ignorecase = true

--- PLUGINS ---

local lsp = {
  "lua_ls",
  "pyright",
  "clangd",
}

vim.opt.secure = true
require("lazy").setup({
  spec = {
    -- add your plugins here
    { 'mason-org/mason.nvim', opts = {}, },

    { "mason-org/mason-lspconfig.nvim",
      opts = {
        ensure_installed = lsp,
      },
    },

    { "neovim/nvim-lspconfig",
      config = function()
        vim.lsp.enable(lsp)
      end
    },
  },

  -- Configure any other settings here. See the documentation for more details.
  -- colorscheme that will be used when installing plugins.
  install = { colorscheme = { "habamax" } },
  
  -- automatically check for plugin updates
  checker = { enabled = true, notify = false, },
})
