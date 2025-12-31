
import os
import subprocess
import sys
import re

# Mapping of repo/folder name to metadata
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

# Mapping for Tools (Editors/Clients)
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

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

def run_command(cmd, cwd=None, capture_output=True, check=True):
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
    try:
        run_command("semver --help", check=False)
    except Exception:
        print("Error: 'semver' command not found. Please install it (e.g. npm install -g semver).")
        sys.exit(1)

def read_crate_version(crate_name):
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
    import json
    full_path = os.path.join(ROOT_DIR, file_path)
    with open(full_path, 'r') as f:
        data = json.load(f)
        return data.get("version")

def read_lua_version(file_path):
    full_path = os.path.join(ROOT_DIR, file_path)
    with open(full_path, 'r') as f:
        content = f.read()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return None

def get_current_version(component):
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
        # Tools are usually at root of their repo or handled specifically?
        # lexed -> lexed/ package.json
        # nvim -> nvim/
        # vscode -> vscode/
        # Check if the repo path IS the component path? 
        # TOOLS definitions: "vscode": { "path": "vscode" ... }
        # Repo root is likely ROOT_DIR/vscode. relative path is .?
        return repo_root, "."
    raise ValueError(f"Unknown component {component}")

def get_tag_name(component, version):
    """Standardized tag name: component-vVersion"""
    # Always prefix? Or only for multi-crate repos?
    # User requested standardized naming. Prefixing everything is safest.
    return f"{component}-v{version}"
