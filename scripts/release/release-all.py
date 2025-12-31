#!/usr/bin/env python3
import sys
import _common
import subprocess
import os
import _set_dep_version


def release_if_changed(component, force=False):
    """Checks for git diff (tag..HEAD), bumps patch if needed."""
    repo_root, rel_path = _common.get_repo_details(component)
    current_ver = _common.get_current_version(component)
    tag_name = _common.get_tag_name(component, current_ver)
    
    release_script = os.path.join(os.path.dirname(__file__), "release-component.py")
    
    # Check if tag exists
    run_args = {"cwd": repo_root, "check": False, "capture_output": True}
    try:
        _common.run_command(f"git rev-parse {tag_name}", **run_args)
        tag_exists = True
    except Exception:
        tag_exists = False
    
    should_release = force
    
    if not tag_exists:
        print(f"[{component}] Tag {tag_name} missing. Assuming initial or forced release needed.")
        should_release = True
    elif not should_release:
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
    try:
        return _set_dep_version.update_cargo_dep(target, source, source_ver)
    except Exception as e:
        print(f"[{target}] Propagate failed: {e}")
        return "MISSING"

def check_json_dep_update(target, dep_key, new_ver):
    # Always force update attempted, return True
    try:
         _set_dep_version.update_json_dep(target, dep_key, new_ver)
         return True
    except Exception as e:
         print(f"Failed to update {target}: {e}")
         return False

def main():
    print("Starting One-Click Release Orchestration...")
    
    # 1. Lex Core
    core_ver = release_if_changed("lex-core")
    
    # 2. Propagate Core -> Tools
    tools_crates = ["lex-babel", "lex-cli", "lex-config"]
    forced_tools = set()
    manifest_updated = False
    
    for tool in tools_crates:
        res = propagate(tool, "lex-core", core_ver)
        if res == "UPDATED":
            manifest_updated = True
            forced_tools.add(tool)
        elif res == "CLEAN" and manifest_updated:
            forced_tools.add(tool)
            
    # 3. Release Tools
    for tool in tools_crates:
        release_if_changed(tool, force=(tool in forced_tools))
        
    # 4. Propagate Core/Babel -> Editors
    # Get potentially new babel version
    babel_ver = _common.get_current_version("lex-babel")
    
    editors_crates = ["lex-analysis", "lex-lsp"]
    forced_editors = set()
    manifest_updated = False 
    
    # Propagate Core
    for ed in editors_crates:
        res = propagate(ed, "lex-core", core_ver)
        if res == "UPDATED":
            manifest_updated = True
            forced_editors.add(ed)
        elif res == "CLEAN" and manifest_updated:
            forced_editors.add(ed)

    # Propagate Babel 
    # (Babel likely UPDATES manifest too if core didn't, or same manifest if core did)
    # If core updated manifest, manifest_updated is True.
    # If babel updates manifest, manifest_updated stays True.
    for ed in editors_crates:
        res = propagate(ed, "lex-babel", babel_ver)
        if res == "UPDATED":
            manifest_updated = True # Even if it wasn't before
            forced_editors.add(ed)
        elif res == "CLEAN" and manifest_updated:
            forced_editors.add(ed)
        
    # lex-lsp also depends on analysis
    analysis_ver = release_if_changed("lex-analysis", force=("lex-analysis" in forced_editors))
    
    res = propagate("lex-lsp", "lex-analysis", analysis_ver)
    if res == "UPDATED":
        forced_editors.add("lex-lsp")
    # Note: separate tracking for internal dep vs shared manifest external dep logic?
    # Analysis dep is usually "path=..." in monorepo, so version might not be used?
    # But we update it anyway.
    
    # 5. Release LSP
    lsp_ver = release_if_changed("lex-lsp", force=("lex-lsp" in forced_editors))
    
    # 6. Propagate LSP -> Clients
    clients = ["lexed", "vscode", "nvim"]
    
    client_dep_keys = {
        "lexed": "version", 
        "vscode": "LEX_LSP_VERSION",
        "nvim": "lex_lsp_version",
    }
    
    for client in clients:
        print(f"[{client}] Updating LSP to {lsp_ver}...")
        check_json_dep_update(client, client_dep_keys[client], lsp_ver)
        release_if_changed(client, force=True) # Always force release if we updated dep

    print("\nRelease Cycle Complete!")
    status_script = os.path.join(os.path.dirname(__file__), "check-status.py")
    subprocess.call([sys.executable, status_script])

if __name__ == "__main__":
    main()
