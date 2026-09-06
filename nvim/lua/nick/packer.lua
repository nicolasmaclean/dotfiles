-- This file can be loaded by calling `lua require('plugins')` from your init.vim

-- Only required if you have packer configured as `opt`
vim.cmd [[packadd packer.nvim]]

return require('packer').startup(function(use)
  -- Packer can manage itself
  use 'wbthomason/packer.nvim'

  use {
	  'nvim-telescope/telescope.nvim', tag = 'v0.2.1',
	  requires = { 'nvim-lua/plenary.nvim' },
  }

  use {
    'saghen/blink.cmp',
    requires = { 'saghen/blink.lib', 'rafamadriz/friendly-snippets' },
    tag = 'v1.*',
    run = function() require('blink.cmp').build():pwait() end,
    config = function()
        require('blink.cmp').setup({
            keymap = { preset = 'default' },
            sources = {
                default = { 'lsp', 'path', 'buffer', 'snippets'},
            }
        })
    end
  }

  use({
	  'rose-pine/neovim',
	  as = 'rose-pine',
	  config = function()
		vim.cmd('colorscheme rose-pine')
	  end
  })

  use('nvim-treesitter/nvim-treesitter', {run = ':TSUpdate'})
  use('theprimeagen/harpoon')
  use('mbbill/undotree')
  use('tpope/vim-fugitive')
  use {'nvim-telescope/telescope-ui-select.nvim' }

  use('ThePrimeagen/vim-be-good')
end)
