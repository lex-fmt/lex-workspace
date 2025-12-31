#!/usr/bin/env python3
"""
Release status checker - shows versions, tags, and dependency status.
"""
import sys
import _common


def format_tag_status(version, tag):
    """Format version with tag comparison."""
    if not tag:
        return f"{version} (no tag)"

    # Extract version from tag (strip v prefix or component- prefix)
    tag_ver = tag
    if tag.startswith("v"):
        tag_ver = tag[1:]
    elif "-v" in tag:
        tag_ver = tag.split("-v")[1]

    if tag_ver == version:
        return f"{version} ({tag})"
    else:
        return f"{version} (tag: {tag})"


def format_deps(deps, indent="    "):
    """Format dependencies as indented lines."""
    if not deps:
        return ""
    lines = []
    for dep, ver in sorted(deps.items()):
        lines.append(f"{indent}{dep}: {ver}")
    return "\n".join(lines)


def main():
    print("Release Status Report")
    print("=====================")

    # Define dependency chain for display order
    crate_order = ["lex-core", "lex-babel", "lex-config", "lex-cli", "lex-analysis", "lex-lsp"]

    # 1. Crates
    print("\n[Crates]")
    for crate in crate_order:
        if crate not in _common.CRATES:
            continue
        ver = _common.get_current_version(crate)
        tag = _common.get_latest_tag(crate)
        deps = _common.read_crate_dependencies(crate)

        status = format_tag_status(ver, tag)
        print(f"{crate:<15} : {status}")

        if deps:
            dep_str = format_deps(deps)
            print(dep_str)

    # 2. Clients
    print("\n[Clients]")
    for tool in _common.TOOLS:
        ver = _common.get_current_version(tool)
        tag = _common.get_latest_tag(tool)
        lsp_ver = _common.read_tool_lsp_version(tool)

        status = format_tag_status(ver, tag)
        print(f"{tool:<15} : {status}")

        if lsp_ver:
            print(f"    lex-lsp: {lsp_ver}")

    # 3. Summary of issues
    print("\n[Issues]")
    issues = []

    # Check for stale LSP versions in clients
    lsp_ver = _common.get_current_version("lex-lsp")
    for tool in _common.TOOLS:
        tool_lsp = _common.read_tool_lsp_version(tool)
        if tool_lsp and tool_lsp != lsp_ver:
            issues.append(f"{tool}: lex-lsp {tool_lsp} -> {lsp_ver}")

    # Check for stale crate dependencies
    for crate in crate_order:
        if crate not in _common.CRATES:
            continue
        deps = _common.read_crate_dependencies(crate)
        for dep, dep_ver in deps.items():
            current_dep_ver = _common.get_current_version(dep)
            if dep_ver != current_dep_ver:
                issues.append(f"{crate}: {dep} {dep_ver} -> {current_dep_ver}")

    # Check for version/tag mismatches
    for crate in crate_order:
        if crate not in _common.CRATES:
            continue
        ver = _common.get_current_version(crate)
        tag = _common.get_latest_tag(crate)
        expected_tag = _common.get_tag_name(crate, ver)
        if tag != expected_tag:
            issues.append(f"{crate}: missing tag {expected_tag} (latest: {tag})")

    for tool in _common.TOOLS:
        ver = _common.get_current_version(tool)
        tag = _common.get_latest_tag(tool)
        expected_tag = _common.get_tag_name(tool, ver)
        if tag != expected_tag:
            issues.append(f"{tool}: missing tag {expected_tag} (latest: {tag})")

    if issues:
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  None - all versions aligned!")


if __name__ == "__main__":
    main()
