vim.g.mapleader = " "

vim.keymap.set("n", "<leader>pv", vim.cmd.Ex)

vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

-- disable arrow keys :skull:
vim.api.nvim_set_keymap('n', '<Up>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('n', '<Down>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('n', '<Left>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('n', '<Right>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('i', '<Up>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('i', '<Down>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('i', '<Left>', '<Nop>', { noremap = true })
vim.api.nvim_set_keymap('i', '<Right>', '<Nop>', { noremap = true })

