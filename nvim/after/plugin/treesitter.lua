require('nvim-treesitter').setup {
	ensure_installed = { 'c', 'cpp', 'lua', 'python' },

	highlight = {
		enable = true,
	}
}

vim.api.nvim_set_keymap("n", "gd", "<cmd>lua vim.lsp.buf.definition()<CR>", { noremap = true, silent = true })
