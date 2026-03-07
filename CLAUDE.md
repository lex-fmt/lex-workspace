# Lex Project

Lex is a plain text format for structured documents — more expressive than Markdown, human-readable in raw form. Structure comes from indentation (4-space tabs), not markup.

**This is a multi-repo workspace.** Each subdirectory is an independent repo with its own git history, CI, and crates.io/npm publishing. See `README.txt` for setup and release workflow.

## Repos & Dependency Flow

```
core (lex-parser)         — Parser crate (crates.io)
  ├─► editors/lex-analysis  — Stateless semantic analysis (crates.io)
  │     └─► editors/lex-lsp   — LSP server, tower-lsp (crates.io)
  │           ├─► lexed/         — Electron desktop editor
  │           ├─► nvim/          — Neovim plugin (Lua)
  │           └─► vscode/        — VSCode extension (TS)
  └─► tools/lex-babel       — Format conversion via IR (crates.io)
        └─► tools/lex-cli     — CLI (uses local path deps)
comms/                     — Specs, fixtures, docs
tools/lex-config/          — Config loader (embeds defaults)
```

## Key Files

| What | Where |
|------|-------|
| AST nodes | `core/src/lex/ast.rs` |
| Parser | `core/src/lex/parsing.rs` |
| Lexer | `core/src/lex/lexing.rs` |
| Grammar specs | `comms/specs/grammar-{core,line,inline}.lex` |
| Test fixtures | `comms/specs/elements/`, `comms/specs/trifecta/`, `comms/specs/benchmark/` |
| LSP server | `editors/lex-lsp/src/server.rs` |
| Analysis modules | `editors/lex-analysis/src/{semantic_tokens,document_symbols,hover,go_to_definition,completion,diagnostics}.rs` |
| Format adapters | `tools/lex-babel/src/formats/` |
| CLI entry | `tools/lex-cli/src/main.rs` |

## Development

- Cross-component dev: `./scripts/build-local.sh` patches editors/ to use local core/tools crates
- Release order: core → tools → editors → clients (each repo tagged independently)
- Test fixtures live in `comms/specs/` — load via the testing module in lex-parser

## CLI Quick Reference

```sh
lex inspect file.lex                    # AST tree visualization (default)
lex inspect file.lex ast-tag            # XML-like AST
lex inspect file.lex ast-json           # JSON AST
lex inspect file.lex --extra-ast-full   # Full AST with all properties
lex inspect file.lex token-line-simple  # Token stream (line-classified)
lex inspect file.lex ir-json            # Intermediate representation
lex file.lex --to markdown              # Convert formats
lex format file.lex                     # Auto-format
```
