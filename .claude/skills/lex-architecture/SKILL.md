---
name: lex-architecture
description: |
  Project architecture overview for the Lex plain text document format workspace. Use when:
  (1) Understanding the codebase structure and component relationships
  (2) Finding where specific features are implemented
  (3) Working across multiple Lex repositories (core, editors, tools, lexed, nvim, vscode)
  (4) Understanding the dependency flow between crates
  (5) Locating test fixtures and testing conventions
---

# Lex Project Architecture

## Directory Structure

```
lex/
├── core/       lex-parser (crates.io)
├── editors/    lex-lsp + lex-analysis (crates.io)
├── tools/      lex-babel + lex-config + lex-cli
├── lexed/      Electron desktop editor
├── nvim/       Neovim plugin (Lua)
├── vscode/     VSCode extension (TypeScript)
└── comms/      Specifications and test fixtures
```

## Dependency Flow

```
core (lex-parser)
       │
       ├───────────────────────┐
       ▼                       ▼
editors/lex-analysis     tools/lex-babel
       │                       │
       ▼                       ▼
editors/lex-lsp          tools/lex-cli
       │
       └──────────┬────────────┐
                  ▼            ▼
                lexed/nvim/vscode
```

## Quick Reference

| Task | Location |
|------|----------|
| AST definitions | `core/src/lex/ast.rs` |
| Parser | `core/src/lex/parsing.rs` |
| Syntax highlighting | `editors/lex-analysis/src/semantic_tokens.rs` |
| Document symbols | `editors/lex-analysis/src/document_symbols.rs` |
| Go to definition | `editors/lex-analysis/src/go_to_definition.rs` |
| Format conversion | `tools/lex-babel/src/formats/` |
| IR types | `tools/lex-babel/src/ir/` |
| LSP server | `editors/lex-lsp/src/server.rs` |
| CLI | `tools/lex-cli/src/main.rs` |
| Config | `tools/lex-config/src/lib.rs` |
| Test fixtures | `comms/specs/` |

## Crate Details

For detailed crate documentation, read the lib.rs files:
- `core/src/lib.rs` - Parser pipeline (5 stages: Lexing → Tree → Parsing → Building → Assembly)
- `editors/lex-analysis/src/lib.rs` - Stateless analysis modules
- `editors/lex-lsp/src/lib.rs` - LSP server architecture (tower-lsp)
- `tools/lex-babel/src/lib.rs` - Format conversion via IR
- `tools/lex-config/src/lib.rs` - Configuration loader

### core/ (lex-parser)

5-stage pipeline transforming Lex source to AST:
1. Lexing - Tokenization, semantic indentation
2. Tree Building - Hierarchical LineContainer
3. Parsing - Pattern-based IR production
4. Building - AST with location tracking
5. Assembly - Annotations and references

### editors/lex-analysis/

Stateless semantic analysis. Modules:
- `semantic_tokens` - Syntax highlighting
- `document_symbols` - Outline/structure
- `hover` - Tooltip previews
- `go_to_definition` / `references` - Navigation
- `folding_ranges` - Collapsible regions
- `completion` - Autocompletion
- `diagnostics` - Errors/warnings

### editors/lex-lsp/

LSP server using tower-lsp. Architecture:
- LSP Layer: JSON-RPC, protocol handling
- Server Layer: Thin LanguageServer implementation
- Feature Layer: Calls lex-analysis (dense tests here)

### tools/lex-babel/

Format conversion. Never parses/serializes directly—uses format libraries.
- `ir/` - Intermediate representation
- `common/` - flat↔nested algorithms
- `formats/` - Format adapters (markdown, html, xml, pdf)

### tools/lex-config/

Configuration loader. Embeds `defaults/lex.default.toml`, supports layered overrides via `Loader`.

## Testing

Use fixtures from `comms/specs/`:
- `kitchensink` - Comprehensive document
- `trifecta/` - Edge cases
- `elements/` - Isolated element tests

Load via testing module in lex-parser.

## Development

Cross-component changes: `./scripts/build-local.sh`

Release order: core → tools → editors → clients

## Editor Feature Matrix

| Feature | LSP | VSCode | Lexed | Neovim |
|---------|-----|--------|-------|--------|
| Syntax Errors | ✓ | ✓ | ✓ | ✓ |
| Go to Definition | ✓ | ✓ | ✓ | ✓ |
| Find References | ✓ | ✓ | ✓ | ✓ |
| Document Format | ✓ | ✓ | ✓ | ✓ |
| Spellcheck | ✓ | ✓ | ✓ | ✗ |
| Code Actions | ✓ | partial | partial | ✗ |
