---
name: lex-parsing-tooling
description: |
  Guide for inspecting Lex parse trees and debugging the parser using the CLI. Use when:
  (1) Debugging parser output or verifying correctness
  (2) Comparing actual parse trees against expected structure
  (3) Understanding how a .lex file is tokenized, classified, and parsed
  (4) Investigating parser bugs or regressions
---

# Lex Parsing Tooling

The `lex` CLI (in `tools/lex-cli/`) is the primary tool for inspecting parser output at every stage. Build it with:

```sh
cargo build --manifest-path tools/lex-cli/Cargo.toml
# or from the tools/ workspace:
cd tools && cargo build -p lex-cli
```

## Inspect Commands

### AST Visualization (default)

```sh
lex inspect file.lex
# or explicitly:
lex inspect file.lex ast-treeviz
```

Output uses Unicode symbols for element types:
- `⧉` Document
- `§` Session
- `≔` Definition
- `☰` List (shows item count)
- `¶` Paragraph (shows line count)
- `⎯` Blank line group
- `⌸` Verbatim block
- `⊜` Annotation

Line numbers appear on the left. Indentation shows nesting.

Example output:
```
⧉ Document (0 annotations, 3 items)
03 ├─ § Introduction
05 │ ├─ ¶ 1 line(s)
06 │ └─ ⎯ 1 blank line
07 ├─ § Details
09 │ ├─ ≔ Key concept
10 │ │ └─ ¶ 2 line(s)
12 │ └─ ☰ 3 items
```

### Full AST (with all properties)

```sh
lex inspect file.lex --extra-ast-full
```

Shows session titles, definition subjects, annotation labels/parameters, list markers. Adds a second line per node with the label/subject text.

### AST as XML Tags

```sh
lex inspect file.lex ast-tag
```

Produces XML-like output showing the full tree with opening/closing tags. Useful for precise structural comparison.

### AST as JSON

```sh
lex inspect file.lex ast-json
```

Full AST in JSON. Best for programmatic analysis or diff-testing.

### Line-level AST

```sh
lex inspect file.lex ast-linetreeviz
```

Tree visualization that expands to show individual lines within elements.

## Token Inspection

### Token Stream (line-classified)

```sh
lex inspect file.lex token-line-simple
```

Shows each token with its line type classification (BlankLine, SubjectLine, ListLine, ParagraphLine, AnnotationStartLine, etc.). This is what the parser sees.

### Token Stream (core, pre-classification)

```sh
lex inspect file.lex token-core-simple
```

Raw tokens before line classification. Shows the fundamental tokenization: Text, Indent, Dedent, Newline, LexMarker, etc.

### Token JSON

```sh
lex inspect file.lex token-line-json   # classified tokens as JSON
lex inspect file.lex token-core-json   # core tokens as JSON
```

Includes byte ranges for every token — useful for verifying span correctness.

### Pretty-printed tokens

```sh
lex inspect file.lex token-line-pprint  # classified, formatted
lex inspect file.lex token-core-pprint  # core, formatted
```

## Intermediate Representation

```sh
lex inspect file.lex ir-json
```

The IR sits between tokens and AST. Shows the parse tree before final AST assembly.

## AST Node Map

```sh
lex inspect file.lex ast-nodemap
```

Character-level color map showing which AST node owns each character position. Useful for verifying element boundaries.

## Debugging Workflow

### 1. Verify tokenization
Start at the lowest level to ensure the input is tokenized correctly:
```sh
lex inspect problem.lex token-core-simple   # raw tokens
lex inspect problem.lex token-line-simple   # classified lines
```

Check that:
- Indentation produces correct Indent/Dedent tokens
- Lines are classified correctly (SubjectLine vs ParagraphLine, ListLine vs SubjectOrListItemLine)
- Blank lines are detected

### 2. Check parse tree structure
```sh
lex inspect problem.lex ast-treeviz         # overview
lex inspect problem.lex --extra-ast-full    # with labels/subjects
lex inspect problem.lex ast-tag             # precise structure
```

Compare against what the grammar specs say should happen. Key questions:
- Is a definition being parsed as a session (or vice versa)?
- Are list items being absorbed into paragraphs?
- Are verbatim blocks capturing the right content?
- Are annotations properly opened and closed?

### 3. Compare expected vs actual
For regression testing, use JSON output and diff:
```sh
lex inspect file.lex ast-json > actual.json
diff expected.json actual.json
```

### 4. Test fixtures
The spec fixtures in `comms/specs/` are the source of truth:
- `comms/specs/elements/*.lex` — isolated tests per element type
- `comms/specs/elements/*.docs` — documentation for what each fixture tests
- `comms/specs/trifecta/` — edge case combinations
- `comms/specs/benchmark/*.lex` — real-world documents

## Parser Pipeline Reference

```
Source text
  → Lexing (tokenization + semantic indentation)
    → Tree Building (hierarchical LineContainer)
      → Parsing (pattern matching → IR nodes)
        → Building (AST construction + locations)
          → Assembly (annotations + reference resolution)
```

Key source files:
- `core/src/lex/lexing.rs` — Tokenizer and line classification
- `core/src/lex/parsing.rs` — Pattern-based parser (precedence order: verbatim → annotation → list → definition → session → paragraph)
- `core/src/lex/ast.rs` — AST node definitions
- `core/src/lex/building.rs` — AST builder
- `core/src/lex/testing.rs` — Test helpers and fixture loading
