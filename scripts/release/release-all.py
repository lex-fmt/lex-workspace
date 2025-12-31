#!/usr/bin/env python3
import sys
import _common
import subprocess
import os
import _set_dep_version

def release_if_changed(component):
    """Checks for git diff (tag..HEAD), bumps patch if needed."""
    repo_root, rel_path = _common.get_repo_details(component)
    current_ver = _common.get_current_version(component)
    tag_name = f"v{current_ver}"
    
    release_script = os.path.join(os.path.dirname(__file__), "release-component.py")
    
    # Check if tag exists
    run_args = {"cwd": repo_root, "check": False, "capture_output": True}
    try:
        _common.run_command(f"git rev-parse {tag_name}", **run_args)
        tag_exists = True
    except Exception:
        tag_exists = False
    
    should_release = False
    
    if not tag_exists:
        print(f"[{component}] Tag {tag_name} missing. Assuming initial or forced release needed.")
        should_release = True
    else:
        # Diff
        cmd = f"git diff --name-only {tag_name}..HEAD -- {rel_path}"
        try:
            diff = _common.run_command(cmd, **run_args)
            if diff and diff.strip():
                print(f"[{component}] Changes detected!")
                should_release = True
            else:
                 print(f"[{component}] No changes.")
        except Exception:
            print(f"[{component}] Diff failed. Forcing check.")
            should_release = True
            
    if should_release:
        print(f"[{component}] Releasing patch...")
        try:
            _common.run_command(f"{sys.executable} {release_script} {component} patch")
            return _common.get_current_version(component) # Return new version
        except Exception as e:
            print(f"[{component}] Release failed: {e}")
            sys.exit(1)
            
    return current_ver

def propagate(target, source, source_ver):
    print(f"[{target}] Checking dependency on {source} ({source_ver})...")
    # This calls _set_dep_version logic
    try:
        _set_dep_version.update_cargo_dep(target, source, source_ver)
    except Exception as e:
        print(f"[{target}] Propagate failed: {e}")
        # Non-fatal? If dep not used, it warns.
    

def main():
    print("Starting One-Click Release Orchestration...")
    
    # 1. Lex Core
    core_ver = release_if_changed("lex-core")
    
    # 2. Propagate Core -> Tools
    tools_crates = ["lex-babel", "lex-cli", "lex-config"]
    for tool in tools_crates:
        propagate(tool, "lex-core", core_ver)
        
    # 3. Release Tools
    for tool in tools_crates:
        release_if_changed(tool)
        
    # 4. Propagate Core/Babel -> Editors
    # Get potentially new babel version
    babel_ver = _common.get_current_version("lex-babel")
    
    editors_crates = ["lex-analysis", "lex-lsp"]
    for ed in editors_crates:
        propagate(ed, "lex-core", core_ver)
        propagate(ed, "lex-babel", babel_ver)
        
    # lex-lsp also depends on analysis
    analysis_ver = release_if_changed("lex-analysis")
    propagate("lex-lsp", "lex-analysis", analysis_ver)
    
    # 5. Release LSP
    lsp_ver = release_if_changed("lex-lsp")
    
    # 6. Propagate LSP -> Clients
    clients = ["lexed", "vscode", "nvim"]
    
    client_dep_keys = {
        "lexed": "version", 
        "vscode": "LEX_LSP_VERSION",
        "nvim": "lex_lsp_version",
    }
    
    for client in clients:
        print(f"[{client}] Updating LSP to {lsp_ver}...")
        try:
             _set_dep_version.update_json_dep(client, client_dep_keys[client], lsp_ver)
        except Exception as e:
             print(f"Failed to update {client}: {e}")
             
        # Release Client
        release_if_changed(client)

    print("\nRelease Cycle Complete!")
    # Call check-status
    status_script = os.path.join(os.path.dirname(__file__), "check-status.py")
    subprocess.call([sys.executable, status_script])

if __name__ == "__main__":
    main()
