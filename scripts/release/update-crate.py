#!/usr/bin/env python3
import sys
import _common
import _set_version

def main():
    if len(sys.argv) < 3:
        print("Usage: update-crate.py <component> <part>")
        print("Part: major, minor, patch")
        sys.exit(1)

    component = sys.argv[1]
    part = sys.argv[2]
    
    current = _common.get_current_version(component)
    if not current:
        print(f"Error: Could not determine current version for {component}")
        sys.exit(1)
        
    cmd = f"semver -i {part} {current}"
    next_ver = _common.run_command(cmd)
    
    print(f"{component}: {current} -> {next_ver}")
    
    # Use the _set_version logic (imported or called via script?)
    # Importing usage is cleaner.
    
    if component in _common.CRATES:
        _set_version.update_crate_version(component, next_ver)
    elif component in _common.TOOLS:
        tool_type = _common.TOOLS[component]["type"]
        if tool_type == "package.json":
            _set_version.update_json_version(component, next_ver)
        elif tool_type == "lua":
            _set_version.update_lua_version(component, next_ver)
    else:
        print(f"Error: Unknown component {component}")
        sys.exit(1)

if __name__ == "__main__":
    main()
