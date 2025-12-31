#!/usr/bin/env bash
#
# Install pre-commit hooks for all Lex repositories
# Run from the lex-workspace root directory
#
# Usage:
#   ./scripts/install-hooks.sh         # Install all hooks
#   ./scripts/install-hooks.sh rust    # Install only Rust hooks
#   ./scripts/install-hooks.sh ts      # Install only TypeScript hooks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Repositories
RUST_REPOS=(core editors tools)
TS_REPOS=(lexed vscode)

install_rust_hook() {
    local repo="$1"
    local repo_path="$WORKSPACE_DIR/$repo"
    local hook_path="$repo_path/.git/hooks/pre-commit"
    local source_script="$SCRIPT_DIR/rust-pre-commit"

    if [ ! -d "$repo_path/.git" ]; then
        echo "  Skipping $repo (not a git repo or not cloned)"
        return
    fi

    # Create hooks directory if needed
    mkdir -p "$repo_path/.git/hooks"

    # Create a wrapper script that calls our central script
    cat > "$hook_path" << 'HOOK'
#!/bin/bash
# Pre-commit hook - calls central workspace script
# Installed by lex-workspace/scripts/install-hooks.sh

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

exec "$WORKSPACE_ROOT/scripts/rust-pre-commit"
HOOK

    chmod +x "$hook_path"
    echo "  Installed: $repo"
}

install_ts_hook() {
    local repo="$1"
    local repo_path="$WORKSPACE_DIR/$repo"
    local husky_path="$repo_path/.husky/pre-commit"

    if [ ! -d "$repo_path/.git" ]; then
        echo "  Skipping $repo (not a git repo or not cloned)"
        return
    fi

    if [ ! -d "$repo_path/.husky" ]; then
        echo "  Skipping $repo (no .husky directory - run 'npm install' first)"
        return
    fi

    # Update .husky/pre-commit to call our central script
    cat > "$husky_path" << 'HOOK'
#!/bin/bash
# Pre-commit hook - calls central workspace script
# Installed by lex-workspace/scripts/install-hooks.sh

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

exec "$WORKSPACE_ROOT/scripts/typescript-pre-commit"
HOOK

    chmod +x "$husky_path"
    echo "  Installed: $repo"
}

echo "Installing pre-commit hooks for Lex workspace"
echo ""

case "${1:-all}" in
    rust)
        echo "Installing Rust pre-commit hooks..."
        for repo in "${RUST_REPOS[@]}"; do
            install_rust_hook "$repo"
        done
        ;;
    ts|typescript)
        echo "Installing TypeScript pre-commit hooks..."
        for repo in "${TS_REPOS[@]}"; do
            install_ts_hook "$repo"
        done
        ;;
    all|"")
        echo "Installing Rust pre-commit hooks..."
        for repo in "${RUST_REPOS[@]}"; do
            install_rust_hook "$repo"
        done

        echo ""
        echo "Installing TypeScript pre-commit hooks..."
        for repo in "${TS_REPOS[@]}"; do
            install_ts_hook "$repo"
        done
        ;;
    *)
        echo "Usage: $0 [rust|ts|all]"
        exit 1
        ;;
esac

echo ""
echo "Done! Hooks will run the same checks as CI."
echo ""
echo "Note: Hooks call central scripts in lex-workspace/scripts/"
echo "      Updates to those scripts apply to all repos automatically."
