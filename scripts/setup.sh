#!/usr/bin/env bash
set -euo pipefail

# Lex Workspace Setup
# Clones all Lex project repositories into the workspace directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# GitHub organization
GITHUB_ORG="lex-fmt"

# Repositories to clone
REPOS=(
  core      # lex-parser: Core parser and AST
  editors   # lex-lsp, lex-analysis: Editor support
  tools     # lex-cli, lex-babel: CLI and format conversion
  lexed     # Standalone Electron editor
  nvim      # Neovim plugin
  vscode    # VSCode extension
  comms     # Specs and documentation
)

# Parse arguments
USE_SSH=false
VERBOSE=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Clones all Lex project repositories into the workspace.

Options:
  --ssh       Use SSH URLs (git@github.com:...) instead of HTTPS
  --verbose   Show detailed output
  --help      Show this help message

Environment:
  GITHUB_TOKEN  Used for authenticated HTTPS clones (optional)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh)
      USE_SSH=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

# Build clone URL for a repo
clone_url() {
  local repo="$1"
  if [[ "$USE_SSH" == true ]]; then
    echo "git@github.com:$GITHUB_ORG/$repo.git"
  else
    echo "https://github.com/$GITHUB_ORG/$repo.git"
  fi
}

log() {
  if [[ "$VERBOSE" == true ]]; then
    echo "$@"
  fi
}

echo "Setting up Lex workspace in $WORKSPACE_DIR"
echo ""

cd "$WORKSPACE_DIR"

cloned=0
skipped=0
failed=0

for repo in "${REPOS[@]}"; do
  if [[ -d "$repo/.git" ]]; then
    log "Skipping $repo (already exists)"
    skipped=$((skipped + 1))
  else
    url="$(clone_url "$repo")"
    echo "Cloning $repo..."
    if git clone "$url" "$repo"; then
      cloned=$((cloned + 1))
    else
      echo "Failed to clone $repo" >&2
      failed=$((failed + 1))
    fi
  fi
done

echo ""
echo "Setup complete: $cloned cloned, $skipped skipped, $failed failed"

if [[ $failed -gt 0 ]]; then
  exit 1
fi

# Check for Rust toolchain
if ! command -v cargo >/dev/null 2>&1; then
  echo ""
  echo "Note: Rust toolchain not found. Install from https://rustup.rs"
fi

# Check for Node.js
if ! command -v node >/dev/null 2>&1; then
  echo ""
  echo "Note: Node.js not found. Required for lexed and vscode extension."
fi

echo ""
echo "Next steps:"
echo "  - Run 'scripts/build-local.sh' to build lex-lsp with local dependencies"
echo "  - See README.md for development workflow"
