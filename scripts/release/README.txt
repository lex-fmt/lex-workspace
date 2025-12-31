Release Automation Plan
=======================

Philosophy & Constraints
------------------------
*   **Language**: Python (stdlib only) + `semver` CLI (must be in PATH).
*   **Naming**:
    *   `_` prefix = Internal primitive (not for direct human use).
    *   `update-*` = Modifies files locally (e.g., bumps version, updates cargo.toml).
    *   `release-*` = Performs full release cycle (Update -> Commit -> Tag -> Push).
*   **Version Source of Truth**: `Cargo.toml` (Crates), `package.json` (JS), `init.lua` (Nvim).
*   **Tagging Strategy**:
    *   **Single-Component Repos** (e.g., `lex-core`): Uses standard `vX.Y.Z` (e.g., `v0.2.2`).
    *   **Monorepos** (e.g., `editors` containing `lex-lsp`, `lex-analysis`): Uses prefixed `Component-vX.Y.Z` (e.g., `lex-lsp-v0.2.3`) to avoid global namespace collisions.

File Structure (`scripts/release/`)
-----------------------------------

### A. Primitives (Internal Helpers)
*   **`_common.py`**:
    *   Registry of all repos/components (Paths, Types, Dependency maps).
    *   `run_git(cmd)`: Git wrapper.
    *   `run_semver(version, bump_type)`: Wrapper for `semver` CLI.
    *   `replace_in_file(path, pattern, replacement)`: Robust regex-based file editor.
    *   `read_toml_version(path)`: Naive TOML version reader.
*   **`_get_version.py <component>`**:
    *   Returns current version string for any crate or tool.
*   **`_set_version.py <component> <new_version>`**:
    *   Updates the specific version file (`Cargo.toml`/`package.json`/`init.lua`).
*   **`_set_dep_version.py <component> <dependency_name> <new_version>`**:
    *   Updates dependency definitions (e.g., `lex-core = "x.y"` in `tools/Cargo.toml` or `lexLspVersion` in `package.json`).

### B. Single Component Actions
*   **`bump-version.py <version_string> <part>`**:
    *   Public utility to calc the next version (e.g., `0.2.2 patch` -> `0.2.3`).
*   **`update-crate.py <crate> <part>`**:
    *   Calculates next version.
    *   Calls `_set_version.py`.
    *   Does **NOT** commit/tag.
*   **`release-component.py <component> <part>`**:
    *   Logic:
        1. `bump-version` (if diff exists or forced).
        2. `_set_version`.
        3. `git commit -m "chore: release vX.Y.Z"`.
        4. `git tag vX.Y.Z`.
        5. `git push && git push --tags`.

### C. Orchestration (The "Smart" Layer)
*   **`propagate-deps.py`**:
    *   Checks which crates depend on `lex-core` or `lex-babel`.
    *   If the required version in `Cargo.toml` < latest released version, runs `_set_dep_version`.
*   **`propagate-lsp.py`**:
    *   Checks `lexed`, `vscode`, `nvim`.
    *   Updates their LSP binary requirement to the latest `lex-lsp` version.
*   **`check-status.py`**:
    *   The "Dry Run" visualizer.
    *   Outputs the "Crate Name: <Code Change v0.x -> v0.y>, <Dep Change>" table.
*   **`release-all.py` (The Master Script)**:
    *   **Phase 1 (Core)**: Check `lex-core` changes -> Release if needed.
    *   **Phase 2 (Tools)**: Check `tools` changes OR `core` update -> Update `core` dep -> Release `tools`.
    *   **Phase 3 (Editors)**: Check `editors` changes OR `tools` update -> Update `tools` dep -> Release `editors`.
    *   **Phase 4 (Clients)**: Check Clients OR `editors` update -> Update `lex-lsp` dep -> Release Clients.

Setup
-----
Ensure `semver` is installed:
`npm install -g semver`
