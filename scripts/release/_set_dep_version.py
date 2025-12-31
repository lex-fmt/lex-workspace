#!/usr/bin/env python3
import sys
import os
import re
import json
import _common

def update_cargo_dep(crate, dep_name, new_version):
    crate_toml = _common.CRATES[crate]
    # Check if dependency is 'workspace = true' in the crate manifest
    full_path = os.path.join(_common.ROOT_DIR, crate_toml)
    with open(full_path, 'r') as f:
        content = f.read()

    # Regex for `dep = { workspace = true }` or `dep.workspace = true`
    # or `dep = { ..., workspace = true, ... }`
    # Simple check for `dep_name.*workspace\s*=\s*true` ?
    # Be careful not to false positive. `lex-core = { workspace = true }`
    
    workspace_re = r'(' + re.escape(dep_name) + r'\s*=\s*\{[^}]*workspace\s*=\s*true)'
    is_workspace = re.search(workspace_re, content)
    
    target_toml = crate_toml
    if is_workspace:
        # It's a workspace dep, we must update the workspace root manifest
        pkg_workspace = _common.CRATE_TO_WORKSPACE.get(crate)
        if not pkg_workspace:
             print(f"Warning: {crate} uses workspace dep for {dep_name} but no workspace map found. Updating matching workspace definition if possible.")
             # Fallback or error? For now fallback to current file (which will fail regex)
        else:
             target_toml = pkg_workspace
             print(f"Dependency {dep_name} is workspace-managed. Updating {target_toml}")
    
    # Now update in target_toml
    # Workspace definition syntax:
    # [workspace.dependencies]
    # lex-core = "0.2.2"
    
    # Or Inline: `lex-core = "0.2.2"` anywhere?
    # We should look for `dep_name = "OLD"` or `dep_name = { ..., version = "OLD", ... }`
    
    return update_toml_dep(target_toml, dep_name, new_version)

def update_toml_dep(path, dep_name, new_version):
    full_path = os.path.join(_common.ROOT_DIR, path)
    with open(full_path, 'r') as f:
        content = f.read()

    # Logic similar to previous attempt, but applied to potentially workspace manifest
    # 1. Simple inline: `lex-core = "0.2.2"`
    pattern_simple = r'(' + re.escape(dep_name) + r'\s*=\s*)"[^"]+"'
    replacement_simple = f'\\g<1>"{new_version}"'
    
    # 2. Table inline: `lex-core = { version = "0.2.2", ... }`
    pattern_table = r'(' + re.escape(dep_name) + r'\s*=\s*\{[^}]*version\s*=\s*)"[^"]+"'
    replacement_table = f'\\g<1>"{new_version}"'

    count = 0
    # Check existence
    if re.search(pattern_simple, content) or re.search(pattern_table, content):
        exists = True
    else:
        exists = False
        
    new_content = re.sub(pattern_simple, replacement_simple, content)
    if new_content != content:
        count += 1
        content = new_content
    
    new_content = re.sub(pattern_table, replacement_table, content)
    if new_content != content:
        count += 1
        content = new_content
        
    if count == 0:
        if exists:
             # Found but identical
             print(f"Dependency {dep_name} in {path} already {new_version} (or no change needed)")
             return "CLEAN"
        else:
             print(f"Warning: No usage of {dep_name} found in {path} to update.")
             return "MISSING"
    else:
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"Updated dependency {dep_name} to {new_version} in {path}")
        return "UPDATED"


def update_json_dep(tool, dep_name, new_version):
    config = _common.TOOLS[tool]
    path = config.get("lsp_dep_file")
    if not path:
        print(f"No lsp_dep_file configured for {tool}")
        return

    full_path = os.path.join(_common.ROOT_DIR, path)
    
    if path.endswith(".json"):
        with open(full_path, 'r') as f:
            data = json.load(f)
        if "version" in data:
            data["version"] = new_version
        elif dep_name in data:
            data[dep_name] = new_version
        
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
            
    elif path.endswith(".sh"):
        with open(full_path, 'r') as f:
            content = f.read()
        pattern = r'(LEX_LSP_VERSION=")[^"]+"'
        replacement = f'\\g<1>{new_version}"'
        new_content = re.sub(pattern, replacement, content)
        with open(full_path, 'w') as f:
            f.write(new_content)
    
    elif path.endswith(".lua"):
        _common.replace_in_file(path, r'(lex_lsp_version\s*=\s*)"[^"]+"', f'\\g<1>"{new_version}"')

    print(f"Updated {dep_name} to {new_version} in {tool}")



def main():
    if len(sys.argv) != 4:
        print("Usage: _set_dep_version.py <component> <dep_name> <new_version>")
        sys.exit(1)

    component = sys.argv[1]
    dep_name = sys.argv[2]
    new_version = sys.argv[3]
    
    try:
        if component in _common.CRATES:
            update_cargo_dep(component, dep_name, new_version)
        elif component in _common.TOOLS:
            update_json_dep(component, dep_name, new_version)
        else:
            print(f"Error: Unknown component {component}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e} - Traceback: {sys.exc_info()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
