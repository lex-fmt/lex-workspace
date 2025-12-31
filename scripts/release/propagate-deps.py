#!/usr/bin/env python3
import sys
import _common
import _set_dep_version

def main():
    print("Propagating latest library versions to dependent crates...")

    # Define strict ordering/dependency graph?
    # Core -> Tools (Babel, Config) -> Editors (Analysis, LSP)
    
    # 1. Get latest versions of Sources
    sources = {
        "lex-core": _common.get_current_version("lex-core"),
        "lex-babel": _common.get_current_version("lex-babel"),
    }
    
    print(f"Sources: {sources}")
    
    # 2. Iterate Targets
    # Which crates consume these? 
    # Almost everyone consumes lex-core.
    # lex-lsp consumes lex-babel.
    
    targets = [
        "lex-babel", # Depends on core
        "lex-cli",   # Depends on core, babel, config
        "lex-config", # Depends on core
        "lex-analysis", # Depends on core, babel 
        "lex-lsp",    # Depends on core, babel, analysis
    ]
    
    # Also lex-analysis is a source for lex-lsp
    sources["lex-analysis"] = _common.get_current_version("lex-analysis")
    
    # Dependency Map (Target -> [Sources])
    # This could be dynamic but static is safer for this scoped script
    deps = {
        "lex-babel": ["lex-core"],
        "lex-cli": ["lex-core", "lex-babel", "lex-config"],
        "lex-config": ["lex-core"],
        "lex-analysis": ["lex-core", "lex-babel"],
        "lex-lsp": ["lex-core", "lex-babel", "lex-analysis"],
    }
    
    updates = 0
    
    for target, required_sources in deps.items():
        if target not in _common.CRATES:
            continue
            
        for source in required_sources:
            if source not in sources:
                continue # Should be in sources map
                
            latest = sources[source]
            
            # Update the dependency
            # _set_dep_version logic handles "workspace=true" vs inline
            # AND it prints if updated or warning if not found.
            
            # We explicitly call the main logic or reuse function
            # Using subprocess to call script to reuse its reliable CLI interface? 
            # Or direct import. Direct import is better.
            
            print(f"Checking {target} depends on {source} ({latest})...")
            try:
                # We need to capture if it actually updated or not?
                # The function prints to stdout.
                _set_dep_version.update_cargo_dep(target, source, latest)
            except Exception as e:
                print(f"Failed to update {target} dep {source}: {e}")

if __name__ == "__main__":
    main()
