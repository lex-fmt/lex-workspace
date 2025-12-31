#!/usr/bin/env python3
import sys
import _common
import _set_dep_version

def main():
    print("Propagating latest LSP version to client tools...")

    # Get latest lex-lsp version
    # Note: lex-lsp might be "workspace = true" inside editors repo?
    # But _get_version reads editors/lex-lsp/Cargo.toml which has the REAL version.
    lsp_version = _common.get_current_version("lex-lsp")
    print(f"Latest lex-lsp: {lsp_version}")
    
    clients = ["lexed", "vscode", "nvim"]
    
    # Map of client -> dep_name for LSP
    # vscode/package.json -> "lexLspVersion" or shell script?
    # _set_dep_version logic handles specific file key logic for tools.
    
    client_deps = {
        "lexed": "version", # lex-version.json key
        "vscode": "LEX_LSP_VERSION", # download-lex-lsp.sh env var
        "nvim": "lex_lsp_version", # init.lua var
    }

    for client, dep_key in client_deps.items():
        print(f"Updating {client} to use lex-lsp {lsp_version}...")
        try:
            _set_dep_version.update_json_dep(client, dep_key, lsp_version)
        except Exception as e:
             print(f"Failed to update {client}: {e}")

if __name__ == "__main__":
    main()
