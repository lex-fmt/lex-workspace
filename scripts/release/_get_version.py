#!/usr/bin/env python3
import sys
import _common

def main():
    if len(sys.argv) != 2:
        print("Usage: _get_version.py <component>")
        print("Components:", ", ".join(list(_common.CRATES.keys()) + list(_common.TOOLS.keys())))
        sys.exit(1)

    component = sys.argv[1]
    try:
        version = _common.get_current_version(component)
        if version:
            print(version)
        else:
            print(f"Error: Version not found for {component}")
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
