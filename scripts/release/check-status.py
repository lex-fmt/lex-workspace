#!/usr/bin/env python3
import sys
import _common

def main():
    print("Release Status Report")
    print("=====================")
    
    # 1. Crates
    print("\n[Crates]")
    for crate in _common.CRATES:
        ver = _common.get_current_version(crate)
        print(f"{crate:<15} : {ver}")
        
    # 2. Tools
    print("\n[Clients]")
    for tool in _common.TOOLS:
        ver = _common.get_current_version(tool)
        print(f"{tool:<15} : {ver}")

    # TODO: Diff logic (check if changes exist since tag)
    # This requires git tag lookup and diff.
    # Ex: lex-babel (current: v0.3.2): Code Change(v0.3.3)
    
if __name__ == "__main__":
    main()
