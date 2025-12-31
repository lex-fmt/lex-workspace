#!/usr/bin/env python3
import sys
import os
import re
import json
import _common

def update_crate_version(name, new_version):
    path = _common.CRATES[name]
    # In Cargo.toml: version = "0.2.2" -> version = "0.2.3"
    # We rely on _common.read_crate_version logic to find the file and regex.
    # The regex needs to replace the first `version = "..."` AFTER `[package]`
    
    # We do custom replacement here because `replace_in_file` is simple find-replace
    # and we need context (post [package])
    
    full_path = os.path.join(_common.ROOT_DIR, path)
    with open(full_path, 'r') as f:
        content = f.read()
    
    package_match = re.search(r'\[package\]', content)
    if not package_match:
         raise ValueError(f"Could not find [package] in {path}")
    
    # Split content: Pre-[package], [package] tag, Post-[package]
    pre = content[:package_match.end()]
    post = content[package_match.end():]
    
    # Replace version in Post
    # Note: This naively assumes version is the first thing or early in [package]
    # It might replace a dependency version if referenced oddly?
    # Standard Cargo.toml has `version =` as a top key under [package].
    # But dependencies might have `version =`.
    # To be safer: `^version\s*=\s*".*"` multiline?
    
    # Using specific regex for key-value pair `version = "..."`
    new_post = re.sub(r'(version\s*=\s*)"[^"]+"', f'\\g<1>"{new_version}"', post, count=1)
    
    if post == new_post:
        raise ValueError(f"Could not find valid 'version =' string to replace in {path} under [package]")
    
    with open(full_path, 'w') as f:
        f.write(pre + new_post)
    print(f"Updated {name} to {new_version}")

def update_json_version(name, new_version):
    config = _common.TOOLS[name]
    path = os.path.join(_common.ROOT_DIR, config["version_file"])
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    data["version"] = new_version
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        # Add newline at end usually
        f.write('\n')
    print(f"Updated {name} to {new_version}")

def update_lua_version(name, new_version):
    config = _common.TOOLS[name]
    path = config["version_file"]
    # Lua init.lua: `M.version = "0.3.1"` or `version = "0.3.1"`
    # We use regex replacement.
    pattern = r'(version\s*=\s*)"[^"]+"'
    replacement = f'\\g<1>"{new_version}"'
    
    if not _common.replace_in_file(path, pattern, replacement):
         raise ValueError(f"Could not update version in {path}")
    print(f"Updated {name} to {new_version}")

def main():
    if len(sys.argv) != 3:
        print("Usage: _set_version.py <component> <new_version>")
        sys.exit(1)

    component = sys.argv[1]
    new_version = sys.argv[2]
    
    try:
        if component in _common.CRATES:
            update_crate_version(component, new_version)
        elif component in _common.TOOLS:
            tool_type = _common.TOOLS[component]["type"]
            if tool_type == "package.json":
                update_json_version(component, new_version)
            elif tool_type == "lua":
                update_lua_version(component, new_version)
        else:
            print(f"Error: Unknown component {component}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
