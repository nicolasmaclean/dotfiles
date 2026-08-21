local lsps = {
    { "lua_ls" },
    {
        "clangd",
        {
            cmd = { 'clangd' },
            filetypes = { 'c', 'cpp', },
            root_markers = { '.clangd', 'compile_commands.json', '.git' },
        }
    },
}

for _, lsp in pairs(lsps) do
    local name, config = lsp[1], lsp[2]
    if config then
        vim.lsp.config(name, config)
    end
    vim.lsp.enable(name)
end


local grp = vim.api.nvim_create_augroup("UserLspBinds", { clear = true })

vim.api.nvim_create_autocmd("LspAttach", {
  group = grp,
  callback = function(args)
    vim.keymap.set({ "n", "x" }, "<leader><CR>", function()
      vim.lsp.buf.code_action({
        apply = true,
        context = { only = { "quickfix" } },
      })
    end, { buffer = args.buf, desc = "Apply fix-it" })
  end,
})
