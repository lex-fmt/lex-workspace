"""
Dependency management - update dependency versions in manifests.
"""

import json
import os
import re

from . import common

# Dependency graph: target -> [sources]
CRATE_DEPS = {
    "lex-babel": ["lex-core"],
    "lex-cli": ["lex-core", "lex-babel", "lex-config"],
    "lex-config": ["lex-core"],
    "lex-analysis": ["lex-core", "lex-babel"],
    "lex-lsp": ["lex-core", "lex-babel", "lex-analysis"],
}

# Client -> LSP dependency key (for display/logging)
CLIENT_LSP_KEYS = {
    "lexed": "lexLspVersion",  # lex-version.json key
    "vscode": "LEX_LSP_VERSION",  # download-lex-lsp.sh env var
    "nvim": "lex_lsp_version",  # init.lua var
}


def update_toml_dep(path, dep_name, new_version):
    """Update a dependency version in a TOML file."""
    full_path = os.path.join(common.ROOT_DIR, path)
    with open(full_path, 'r') as f:
        content = f.read()

    # 1. Simple inline: `lex-core = "0.2.2"`
    pattern_simple = r'(' + re.escape(dep_name) + r'\s*=\s*)"[^"]+"'
    replacement_simple = f'\\g<1>"{new_version}"'

    # 2. Table inline: `lex-core = { version = "0.2.2", ... }`
    pattern_table = r'(' + re.escape(dep_name) + r'\s*=\s*\{[^}]*version\s*=\s*)"[^"]+"'
    replacement_table = f'\\g<1>"{new_version}"'

    count = 0
    exists = bool(re.search(pattern_simple, content) or re.search(pattern_table, content))

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


def update_cargo_dep(crate, dep_name, new_version):
    """Update a crate dependency, handling workspace dependencies."""
    crate_toml = common.CRATES[crate]
    full_path = os.path.join(common.ROOT_DIR, crate_toml)

    with open(full_path, 'r') as f:
        content = f.read()

    # Check for workspace = true
    workspace_re = r'(' + re.escape(dep_name) + r'\s*=\s*\{[^}]*workspace\s*=\s*true)'
    is_workspace = re.search(workspace_re, content)

    target_toml = crate_toml
    if is_workspace:
        pkg_workspace = common.CRATE_TO_WORKSPACE.get(crate)
        if pkg_workspace:
            target_toml = pkg_workspace
            print(f"Dependency {dep_name} is workspace-managed. Updating {target_toml}")

    return update_toml_dep(target_toml, dep_name, new_version)


def update_tool_dep(tool, dep_key, new_version):
    """Update LSP version dependency in a client tool.

    Note: Tools store the full tag name (e.g., "lex-lsp-v0.2.7") not just the version.
    This is used for GitHub release downloads.
    """
    config = common.TOOLS[tool]
    path = config.get("lsp_dep_file")
    if not path:
        print(f"No lsp_dep_file configured for {tool}")
        return

    full_path = os.path.join(common.ROOT_DIR, path)

    # Tools store the full tag name for GitHub release downloads
    tag_name = f"lex-lsp-v{new_version}"

    if path.endswith(".json"):
        with open(full_path, 'r') as f:
            data = json.load(f)
        # lexed uses "lexLspVersion" key
        if "lexLspVersion" in data:
            data["lexLspVersion"] = tag_name
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')

    elif path.endswith(".sh"):
        with open(full_path, 'r') as f:
            content = f.read()
        pattern = r'(LEX_LSP_VERSION=")[^"]+"'
        replacement = f'\\g<1>{tag_name}"'
        new_content = re.sub(pattern, replacement, content)
        with open(full_path, 'w') as f:
            f.write(new_content)

    elif path.endswith(".lua"):
        common.replace_in_file(path, r'(lex_lsp_version\s*=\s*)"[^"]+"', f'\\g<1>"{tag_name}"')

    print(f"Updated {dep_key} to {tag_name} in {tool}")


def set_dep_version(component, dep_name, new_version):
    """Set dependency version for any component."""
    if component in common.CRATES:
        return update_cargo_dep(component, dep_name, new_version)
    elif component in common.TOOLS:
        update_tool_dep(component, dep_name, new_version)
        return "UPDATED"
    else:
        raise ValueError(f"Unknown component: {component}")


def propagate_deps():
    """Propagate latest library versions to dependent crates."""
    print("Propagating latest library versions to dependent crates...")

    sources = {
        "lex-core": common.get_current_version("lex-core"),
        "lex-babel": common.get_current_version("lex-babel"),
        "lex-analysis": common.get_current_version("lex-analysis"),
    }

    print(f"Sources: {sources}")

    for target, required_sources in CRATE_DEPS.items():
        if target not in common.CRATES:
            continue

        for source in required_sources:
            if source not in sources:
                continue

            latest = sources[source]
            print(f"Checking {target} depends on {source} ({latest})...")
            try:
                update_cargo_dep(target, source, latest)
            except Exception as e:
                print(f"Failed to update {target} dep {source}: {e}")


def propagate_lsp():
    """Propagate latest LSP version to client tools."""
    print("Propagating latest LSP version to client tools...")

    lsp_version = common.get_current_version("lex-lsp")
    print(f"Latest lex-lsp: {lsp_version}")

    for client, dep_key in CLIENT_LSP_KEYS.items():
        print(f"Updating {client} to use lex-lsp {lsp_version}...")
        try:
            update_tool_dep(client, dep_key, lsp_version)
        except Exception as e:
            print(f"Failed to update {client}: {e}")
