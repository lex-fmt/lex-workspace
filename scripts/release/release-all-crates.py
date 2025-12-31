#!/usr/bin/env python3
import sys
import _common
import subprocess
import os

def main():
    print("Checking for changes in all crates...")
    
    # Order matters? 
    # Core -> Tools -> Editors
    order = [
        "lex-core",
        "lex-babel", "lex-cli", "lex-config",
        "lex-analysis", "lex-lsp"
    ]
    
    release_script = os.path.join(os.path.dirname(__file__), "release-component.py")

    for crate in order:
        repo_root, rel_path = _common.get_repo_details(crate)
        current_ver = _common.get_current_version(crate)
        tag_name = f"v{current_ver}"
        
        print(f"Checking {crate} ({current_ver}) in {rel_path}...")
        
        # Check if tag exists
        try:
            _common.run_command(f"git rev-parse {tag_name}", cwd=repo_root, check=False)
        except Exception:
            print(f"  Tag {tag_name} not found. Assuming generic 'main' or fresh release?")
            # If tag missing, do we assume changes? Or nothing?
            # User said "diff main against latest tag".
            # If no tag, maybe we should release?
            # Assume no changes if tag missing? Or assume ALL changes?
            pass

        # Diff
        # git diff --name-only v0.2.2..HEAD path/to/crate
        cmd = f"git diff --name-only {tag_name}..HEAD -- {rel_path}"
        try:
            diff = _common.run_command(cmd, cwd=repo_root, check=False)
        except Exception:
            # If tag incorrect, command fails.
            diff = "FORCE_UPDATE" # Fallback?

        if diff and diff.strip():
            print(f"  Changes detected in {crate}!")
            # Should we ask or auto-release?
            # User said "mark that create for updating, then use the previous script to release".
            # We will auto-release patch version?
            
            # Using subprocess to call release-component.py
            # "scripts/release/release-component.py <component> patch"
            print(f"  Releasing {crate} (patch bump)...")
            try:
                _common.run_command(f"{sys.executable} {release_script} {crate} patch")
            except Exception as e:
                print(f"  Failed to release {crate}: {e}")
        else:
            print(f"  No changes in {crate}.")

if __name__ == "__main__":
    main()
