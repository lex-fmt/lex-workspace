"""
Common utilities and registry for release management.
"""

import json
import os
import re
import subprocess
import sys

# Mapping of crate name to its Cargo.toml path (relative to ROOT_DIR)
CRATES = {
    "lex-core": "core/Cargo.toml",
    "lex-babel": "tools/lex-babel/Cargo.toml",
    "lex-cli": "tools/lex-cli/Cargo.toml",
    "lex-config": "tools/lex-config/Cargo.toml",
    "lex-analysis": "editors/lex-analysis/Cargo.toml",
    "lex-lsp": "editors/lex-lsp/Cargo.toml",
}

# Mapping of crate to its workspace root manifest
CRATE_TO_WORKSPACE = {
    "lex-core": "core/Cargo.toml",
    "lex-babel": "tools/Cargo.toml",
    "lex-cli": "tools/Cargo.toml",
    "lex-config": "tools/Cargo.toml",
    "lex-analysis": "editors/Cargo.toml",
    "lex-lsp": "editors/Cargo.toml",
}

# Mapping for client tools (editors/GUIs)
TOOLS = {
    "lexed": {
        "path": "lexed",
        "version_file": "lexed/package.json",
        "type": "package.json",
        "lsp_dep_file": "lexed/shared/src/lex-version.json"
    },
    "vscode": {
        "path": "vscode",
        "version_file": "vscode/package.json",
        "type": "package.json",
        "lsp_dep_file": "vscode/scripts/download-lex-lsp.sh"
    },
    "nvim": {
        "path": "nvim",
        "version_file": "nvim/lua/lex/init.lua",
        "type": "lua",
        "lsp_dep_file": "nvim/lua/lex/init.lua"
    }
}

# ROOT_DIR is the lex-workspace root (parent of scripts/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


def run_command(cmd, cwd=None, capture_output=True, check=True):
    """Run a shell command and return output."""
    if cwd is None:
        cwd = ROOT_DIR
    try:
        if capture_output:
            result = subprocess.check_output(cmd, shell=True, cwd=cwd, stderr=subprocess.STDOUT)
            return result.decode('utf-8').strip()
        else:
            subprocess.check_call(cmd, shell=True, cwd=cwd)
            return None
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {cmd}")
            if e.output:
                print(e.output.decode('utf-8'))
            sys.exit(e.returncode)
        else:
            raise


def check_semver_installed():
    """Verify semver CLI is available."""
    try:
        run_command("semver --help", check=False)
    except Exception:
        print("Error: 'semver' command not found. Please install it (e.g. npm install -g semver).")
        sys.exit(1)


def read_crate_version(crate_name):
    """Read version from a crate's Cargo.toml."""
    if crate_name not in CRATES:
        raise ValueError(f"Unknown crate: {crate_name}")
    toml_path = os.path.join(ROOT_DIR, CRATES[crate_name])
    with open(toml_path, 'r') as f:
        content = f.read()
    package_match = re.search(r'\[package\]', content)
    if not package_match:
        raise ValueError(f"Could not find [package] section in {toml_path}")
    post_package = content[package_match.end():]
    version_match = re.search(r'version\s*=\s*"([^"]+)"', post_package)
    if version_match:
        return version_match.group(1)
    raise ValueError(f"Could not find version in {toml_path}")


def read_json_version(file_path):
    """Read version from a package.json file."""
    full_path = os.path.join(ROOT_DIR, file_path)
    with open(full_path, 'r') as f:
        data = json.load(f)
        return data.get("version")


def read_lua_version(file_path):
    """Read version from a Lua file."""
    full_path = os.path.join(ROOT_DIR, file_path)
    with open(full_path, 'r') as f:
        content = f.read()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def get_current_version(component):
    """Get current version for any component (crate or tool)."""
    check_semver_installed()
    if component in CRATES:
        return read_crate_version(component)
    elif component in TOOLS:
        tool_config = TOOLS[component]
        if tool_config["type"] == "package.json":
            return read_json_version(tool_config["version_file"])
        elif tool_config["type"] == "lua":
            return read_lua_version(tool_config["version_file"])
    else:
        raise ValueError(f"Unknown component: {component}")


def replace_in_file(file_path, pattern, replacement):
    """Replace text in a file using regex."""
    full_path = os.path.join(ROOT_DIR, file_path)
    with open(full_path, 'r') as f:
        content = f.read()
    new_content = re.sub(pattern, replacement, content, count=1)
    if content == new_content:
        return False
    with open(full_path, 'w') as f:
        f.write(new_content)
    return True


def get_repo_details(component):
    """Returns (repo_root_abs_path, relative_path_in_repo) for a component."""
    if component in CRATES:
        manifest_path = CRATES[component]
        parts = manifest_path.split("/")
        repo_dir = parts[0]
        repo_root = os.path.join(ROOT_DIR, repo_dir)
        if len(parts) > 2:
            relative_crate_path = os.path.dirname("/".join(parts[1:]))
        else:
            relative_crate_path = "."
        return repo_root, relative_crate_path
    elif component in TOOLS:
        config = TOOLS[component]
        repo_dir = config["path"].split("/")[0]
        repo_root = os.path.join(ROOT_DIR, repo_dir)
        return repo_root, "."
    raise ValueError(f"Unknown component {component}")


def _build_repo_map():
    """Build map of repo directory to components."""
    repo_map = {}

    # Process Crates
    for comp, path in CRATES.items():
        repo_dir = path.split("/")[0]
        if repo_dir not in repo_map:
            repo_map[repo_dir] = set()
        repo_map[repo_dir].add(comp)

    # Process Tools
    for comp, config in TOOLS.items():
        repo_dir = config["path"].split("/")[0]
        if repo_dir not in repo_map:
            repo_map[repo_dir] = set()
        repo_map[repo_dir].add(comp)

    return repo_map


_REPO_ENTRIES = _build_repo_map()


def is_monorepo(component):
    """Check if component is in a monorepo (multiple components in same repo)."""
    repo_root, _ = get_repo_details(component)
    repo_name = os.path.basename(repo_root)

    if repo_name in _REPO_ENTRIES:
        return len(_REPO_ENTRIES[repo_name]) > 1
    return False


def get_tag_name(component, version):
    """Get standardized tag name: component-vVersion or vVersion."""
    if is_monorepo(component):
        return f"{component}-v{version}"
    else:
        return f"v{version}"


def get_latest_tag(component):
    """Get the latest git tag for a component."""
    repo_root, _ = get_repo_details(component)

    # First try component-prefixed tags (for monorepos)
    prefix = f"{component}-v"
    try:
        result = run_command(f"git tag --list '{prefix}*' --sort=-v:refname | head -1", cwd=repo_root, check=False)
        if result:
            return result
    except Exception:
        pass

    # Fall back to v* tags for single-component repos
    try:
        result = run_command("git tag --list 'v*' --sort=-v:refname | head -1", cwd=repo_root, check=False)
        # Filter out test tags like v100.0.0
        if result and not result.startswith("v100"):
            return result
        # Try second tag
        result = run_command("git tag --list 'v*' --sort=-v:refname | head -2 | tail -1", cwd=repo_root, check=False)
        if result and not result.startswith("v100"):
            return result
    except Exception:
        pass
    return None


def read_crate_dependencies(crate_name):
    """Read lex-* dependencies from a crate's Cargo.toml or workspace manifest."""
    if crate_name not in CRATES:
        return {}

    workspace_path = CRATE_TO_WORKSPACE.get(crate_name)
    if not workspace_path:
        workspace_path = CRATES[crate_name]

    full_path = os.path.join(ROOT_DIR, workspace_path)
    with open(full_path, 'r') as f:
        content = f.read()

    deps = {}
    for dep in ["lex-core", "lex-babel", "lex-analysis", "lex-config"]:
        if dep == crate_name:
            continue
        # Match: dep = "version" or dep = { version = "version", ... }
        simple_match = re.search(rf'{re.escape(dep)}\s*=\s*"([^"]+)"', content)
        table_match = re.search(rf'{re.escape(dep)}\s*=\s*\{{[^}}]*version\s*=\s*"([^"]+)"', content)
        if simple_match:
            deps[dep] = simple_match.group(1)
        elif table_match:
            deps[dep] = table_match.group(1)

    return deps


def extract_version_from_tag(tag):
    """Extract version number from a tag like 'lex-lsp-v0.2.7' or 'v0.2.7'."""
    if not tag:
        return None
    # Handle component-prefixed tags like "lex-lsp-v0.2.7"
    if "-v" in tag:
        return tag.split("-v")[-1]
    # Handle simple v-prefixed tags like "v0.2.7"
    if tag.startswith("v"):
        return tag[1:]
    return tag


def read_tool_lsp_version(tool_name):
    """Read the lex-lsp version a tool depends on."""
    if tool_name not in TOOLS:
        return None

    config = TOOLS[tool_name]
    lsp_dep_file = config.get("lsp_dep_file")
    if not lsp_dep_file:
        return None

    full_path = os.path.join(ROOT_DIR, lsp_dep_file)
    if not os.path.exists(full_path):
        return None

    with open(full_path, 'r') as f:
        content = f.read()

    raw_version = None
    if lsp_dep_file.endswith(".json"):
        try:
            data = json.loads(content)
            raw_version = data.get("lexLspVersion", "")
        except Exception:
            return None
    elif lsp_dep_file.endswith(".sh"):
        match = re.search(r'LEX_LSP_VERSION="([^"]+)"', content)
        raw_version = match.group(1) if match else None
    elif lsp_dep_file.endswith(".lua"):
        match = re.search(r'lex_lsp_version\s*=\s*"([^"]+)"', content)
        raw_version = match.group(1) if match else None

    return extract_version_from_tag(raw_version)


def get_all_components():
    """Get list of all component names."""
    return list(CRATES.keys()) + list(TOOLS.keys())
