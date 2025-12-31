"""
Version management - get, set, and bump versions.
"""

import json
import os
import re

from . import common


def get_version(component):
    """Get current version of a component."""
    return common.get_current_version(component)


def set_crate_version(name, new_version):
    """Update version in a crate's Cargo.toml."""
    path = common.CRATES[name]
    full_path = os.path.join(common.ROOT_DIR, path)

    with open(full_path, 'r') as f:
        content = f.read()

    package_match = re.search(r'\[package\]', content)
    if not package_match:
        raise ValueError(f"Could not find [package] in {path}")

    pre = content[:package_match.end()]
    post = content[package_match.end():]

    new_post = re.sub(r'(version\s*=\s*)"[^"]+"', f'\\g<1>"{new_version}"', post, count=1)

    if post == new_post:
        raise ValueError(f"Could not find valid 'version =' string to replace in {path} under [package]")

    with open(full_path, 'w') as f:
        f.write(pre + new_post)
    print(f"Updated {name} to {new_version}")


def set_json_version(name, new_version):
    """Update version in a package.json file."""
    config = common.TOOLS[name]
    path = os.path.join(common.ROOT_DIR, config["version_file"])

    with open(path, 'r') as f:
        data = json.load(f)

    data["version"] = new_version

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(f"Updated {name} to {new_version}")


def set_lua_version(name, new_version):
    """Update version in a Lua file."""
    config = common.TOOLS[name]
    path = config["version_file"]

    pattern = r'(version\s*=\s*)"[^"]+"'
    replacement = f'\\g<1>"{new_version}"'

    if not common.replace_in_file(path, pattern, replacement):
        raise ValueError(f"Could not update version in {path}")
    print(f"Updated {name} to {new_version}")


def set_version(component, new_version):
    """Set version for any component."""
    if component in common.CRATES:
        set_crate_version(component, new_version)
    elif component in common.TOOLS:
        tool_type = common.TOOLS[component]["type"]
        if tool_type == "package.json":
            set_json_version(component, new_version)
        elif tool_type == "lua":
            set_lua_version(component, new_version)
    else:
        raise ValueError(f"Unknown component: {component}")


def bump_version(version, bump_type, preid=None):
    """Calculate next version using semver CLI."""
    common.check_semver_installed()

    cmd = f"semver -i {bump_type} {version}"
    if preid:
        cmd += f" --preid {preid}"

    new_version = common.run_command(cmd)
    if not new_version:
        raise ValueError("semver returned empty string")
    return new_version


def update_component_version(component, part):
    """Bump version of a component and update its manifest."""
    current = get_version(component)
    if not current:
        raise ValueError(f"Could not determine current version for {component}")

    next_ver = bump_version(current, part)
    print(f"{component}: {current} -> {next_ver}")

    set_version(component, next_ver)
    return next_ver
