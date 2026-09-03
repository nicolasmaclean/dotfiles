local lsps = {
    { "lua_ls" },
    {
      "clangd",
      {
          cmd = {
              'clangd',
              '--background-index',
              '--clang-tidy',
              '--header-insertion=iwyu',
              '--completion-style=detailed',
              '--pch-storage=memory',
              '-j=4',
          },
          filetypes = { 'c', 'cpp' },
          root_markers = { '.clangd', 'compile_commands.json', '.git' },
      }
    },
    {
      -- types, completion, go-to-definition
      "pyright",
      {
          cmd = { 'pyright-langserver', '--stdio' },
          filetypes = { 'python' },
          root_markers = {
              'pyproject.toml',
              'pyrightconfig.json',
              'setup.py',
              'setup.cfg',
              'requirements.txt',
              '.git',
          },
          settings = {
              python = {
                  analysis = {
                      autoSearchPaths = true,
                      useLibraryCodeForTypes = true,
                      diagnosticMode = 'openFilesOnly',
                      typeCheckingMode = 'standard',
                  },
              },
          },
          handlers = {
              -- ruff already flags unused imports/vars, drop pyright's hint-level
              -- duplicates so they don't show up twice inline
              ['textDocument/publishDiagnostics'] = function(err, result, ctx)
                  if result and result.diagnostics then
                      result.diagnostics = vim.tbl_filter(function(d)
                          return d.severity ~= vim.lsp.protocol.DiagnosticSeverity.Hint
                      end, result.diagnostics)
                  end
                  return vim.lsp.handlers['textDocument/publishDiagnostics'](err, result, ctx)
              end,
          },
          -- point pyright at the project venv so third-party imports resolve
          before_init = function(_, config)
              local venv = vim.env.VIRTUAL_ENV
              if not venv then
                  local root = config.root_dir or vim.fn.getcwd()
                  for _, dir in ipairs({ '.venv', 'venv' }) do
                      if vim.fn.isdirectory(root .. '/' .. dir) == 1 then
                          venv = root .. '/' .. dir
                          break
                      end
                  end
              end
              if venv then
                  config.settings.python.pythonPath = venv .. '/bin/python'
              end
          end,
      }
    },
    {
      -- lint + format (the clang-tidy of python)
      "ruff",
      {
          cmd = { 'ruff', 'server' },
          filetypes = { 'python' },
          root_markers = { 'pyproject.toml', 'ruff.toml', '.ruff.toml', '.git' },
          on_attach = function(client, _)
              -- let pyright own hover, ruff's is much thinner
              client.server_capabilities.hoverProvider = false
          end,
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


vim.keymap.set({ "n" }, "gr", vim.lsp.buf.references)
vim.keymap.set("n", "<leader>dd", vim.diagnostic.open_float)
vim.keymap.set("n", "<leader>dq", vim.diagnostic.setqflist)
vim.keymap.set("n", "[d", function() vim.diagnostic.jump({ count = -1 }) end)
vim.keymap.set("n", "]d", function() vim.diagnostic.jump({ count = 1 }) end)

local grp = vim.api.nvim_create_augroup("UserLspBinds", { clear = true })
vim.api.nvim_create_autocmd("LspAttach", {
  group = grp,
  callback = function(args)
    -- add quickfix cmd when we have lsp
    vim.keymap.set({ "n", "x" }, "<leader><CR>", function()
      vim.lsp.buf.code_action({
        apply = true,
        context = { only = { "quickfix" } },
      })
    end, { buffer = args.buf, desc = "Apply fix-it" })

    -- format on save, delegated to whichever client actually formats well
    local formatters = { c = "clangd", cpp = "clangd", python = "ruff" }
    local formatter = formatters[vim.bo[args.buf].filetype]
    -- python attaches two clients, so only wire the autocmd up once per buffer
    if formatter and not vim.b[args.buf].user_format_on_save then
        vim.b[args.buf].user_format_on_save = true
        vim.api.nvim_create_autocmd("BufWritePre", {
          group = grp,
          buffer = args.buf,
          callback = function()
              vim.lsp.buf.format({
                  bufnr = args.buf,
                  timeout_ms = 2000,
                  filter = function(c) return c.name == formatter end,
              })
          end,
        })
    end
  end,
})
