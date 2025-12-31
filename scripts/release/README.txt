Release Manager
===============

Unified release automation for the Lex workspace.

Usage
-----
    scripts/release/release-manager <command> [options]

Commands
--------
    check-status          Show release status report
    get-version           Get version of a component
    set-version           Set version of a component
    set-dep-version       Set dependency version
    bump-version          Calculate next version
    update                Update component version (bump + set)
    release               Release a component (update + commit + tag)
    propagate-deps        Propagate library versions to dependents
    propagate-lsp         Propagate LSP version to clients
    release-all           Full release orchestration
    release-all-crates    Release all crates with changes

Examples
--------
    # Check current release status
    ./scripts/release/release-manager check-status

    # Get version of a component
    ./scripts/release/release-manager get-version lex-core

    # Release a single component with patch bump
    ./scripts/release/release-manager release lex-core patch

    # Run full release orchestration
    ./scripts/release/release-manager release-all

Philosophy & Constraints
------------------------
*   **Language**: Python (stdlib only) + `semver` CLI (must be in PATH).
*   **Version Source of Truth**: `Cargo.toml` (Crates), `package.json` (JS), `init.lua` (Nvim).
*   **Tagging Strategy**:
    *   **Single-Component Repos** (e.g., `lex-core`): Uses standard `vX.Y.Z` (e.g., `v0.2.2`).
    *   **Monorepos** (e.g., `editors` containing `lex-lsp`, `lex-analysis`): Uses prefixed
        `Component-vX.Y.Z` (e.g., `lex-lsp-v0.2.3`) to avoid global namespace collisions.

File Structure (`scripts/release/`)
-----------------------------------
    release-manager          # Entry point script (executable)
    releasemanager/          # Python package
        __init__.py          # Package initialization
        common.py            # Registry and shared utilities
        version.py           # Version get/set/bump operations
        dependencies.py      # Dependency management and propagation
        component.py         # Single component release operations
        status.py            # Release status reporting
        orchestrate.py       # Full release orchestration (release-all)
        cli.py               # Command-line interface

Release Flow
------------
1. **Core**: Check `lex-core` changes -> Release if needed
2. **Tools**: Propagate `core` version -> Release `lex-babel`, `lex-cli`, `lex-config`
3. **Editors**: Propagate `core`/`babel` -> Release `lex-analysis`, `lex-lsp`
4. **Clients**: Propagate `lsp` version -> Release `lexed`, `vscode`, `nvim`

Setup
-----
Ensure `semver` CLI is installed:
    npm install -g semver
