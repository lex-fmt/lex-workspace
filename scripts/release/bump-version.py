#!/usr/bin/env python3
import sys
import _common

def main():
    if len(sys.argv) < 3:
        print("Usage: bump-version.py <version> <type> [preid]")
        print("Type: major, minor, patch, premajor, etc.")
        sys.exit(1)

    version = sys.argv[1]
    bump_type = sys.argv[2]
    preid = sys.argv[3] if len(sys.argv) > 3 else None
    
    cmd = f"semver -i {bump_type} {version}"
    if preid:
        cmd += f" --preid {preid}"
        
    try:
        new_version = _common.run_command(cmd)
        if not new_version:
             raise ValueError("semver returned empty string")
        print(new_version)
    except Exception as e:
        print(f"Error running semver: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
