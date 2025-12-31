"""
Release orchestration - coordinate full release cycles across all components.
"""

import os
import sys

from . import common
from . import component
from . import dependencies
from . import status
from . import version

# Global list to collect push commands
PUSH_COMMANDS = []


def record_push_command(comp):
    """Record push command for a component's repo."""
    repo_root, _ = common.get_repo_details(comp)
    try:
        rel_path = os.path.relpath(repo_root, os.getcwd())
    except Exception:
        rel_path = repo_root

    cmd = f"pushd {rel_path} && git push && git push --tags && popd"
    if cmd not in PUSH_COMMANDS:
        PUSH_COMMANDS.append(cmd)


def release_if_changed(comp, force=False):
    """Check for changes and release if needed."""
    repo_root, rel_path = common.get_repo_details(comp)
    current_ver = common.get_current_version(comp)
    tag_name = common.get_tag_name(comp, current_ver)

    # Check if tag exists
    try:
        common.run_command(f"git rev-parse {tag_name}", cwd=repo_root, check=False)
        tag_exists = True
    except Exception:
        tag_exists = False

    should_release = force

    if not tag_exists:
        print(f"[{comp}] Tag {tag_name} missing. Assuming initial or forced release needed.")
        should_release = True
    elif not should_release:
        cmd = f"git diff --name-only {tag_name}..HEAD -- {rel_path}"
        try:
            diff = common.run_command(cmd, cwd=repo_root, check=False)
            if diff and diff.strip():
                print(f"[{comp}] Changes detected!")
                should_release = True
            else:
                print(f"[{comp}] No changes.")
        except Exception:
            print(f"[{comp}] Diff failed. Forcing check.")
            should_release = True

    if should_release:
        print(f"[{comp}] Releasing patch...")
        try:
            component.release_component(comp, "patch")
            record_push_command(comp)
            return common.get_current_version(comp)
        except Exception as e:
            print(f"[{comp}] Release failed: {e}")
            sys.exit(1)

    return current_ver


def propagate(target, source, source_ver):
    """Propagate a dependency version."""
    print(f"[{target}] Checking dependency on {source} ({source_ver})...")
    try:
        return dependencies.update_cargo_dep(target, source, source_ver)
    except Exception as e:
        print(f"[{target}] Propagate failed: {e}")
        return "MISSING"


def release_all():
    """One-click release orchestration following dependency order."""
    global PUSH_COMMANDS
    PUSH_COMMANDS = []

    print("Starting One-Click Release Orchestration...")

    # 1. Lex Core
    core_ver = release_if_changed("lex-core")

    # 2. Propagate Core -> Tools
    tools_crates = ["lex-babel", "lex-cli", "lex-config"]
    forced_tools = set()
    manifest_updated = False

    for tool in tools_crates:
        res = propagate(tool, "lex-core", core_ver)
        if res == "UPDATED":
            manifest_updated = True
            forced_tools.add(tool)
        elif res == "CLEAN" and manifest_updated:
            forced_tools.add(tool)

    # 3. Release Tools
    for tool in tools_crates:
        release_if_changed(tool, force=(tool in forced_tools))

    # 4. Propagate Core/Babel -> Editors
    babel_ver = common.get_current_version("lex-babel")

    editors_crates = ["lex-analysis", "lex-lsp"]
    forced_editors = set()
    manifest_updated = False

    # Propagate Core
    for ed in editors_crates:
        res = propagate(ed, "lex-core", core_ver)
        if res == "UPDATED":
            manifest_updated = True
            forced_editors.add(ed)
        elif res == "CLEAN" and manifest_updated:
            forced_editors.add(ed)

    # Propagate Babel
    for ed in editors_crates:
        res = propagate(ed, "lex-babel", babel_ver)
        if res == "UPDATED":
            manifest_updated = True
            forced_editors.add(ed)
        elif res == "CLEAN" and manifest_updated:
            forced_editors.add(ed)

    # lex-lsp also depends on analysis
    analysis_ver = release_if_changed("lex-analysis", force=("lex-analysis" in forced_editors))

    res = propagate("lex-lsp", "lex-analysis", analysis_ver)
    if res == "UPDATED":
        forced_editors.add("lex-lsp")

    # 5. Release LSP
    lsp_ver = release_if_changed("lex-lsp", force=("lex-lsp" in forced_editors))

    # 6. Propagate LSP -> Clients
    clients = ["lexed", "vscode", "nvim"]

    for client in clients:
        print(f"[{client}] Updating LSP to {lsp_ver}...")
        try:
            dependencies.update_tool_dep(client, dependencies.CLIENT_LSP_KEYS[client], lsp_ver)
        except Exception as e:
            print(f"Failed to update {client}: {e}")
        release_if_changed(client, force=True)

    print("\nRelease Cycle Complete!")
    status.check_status()

    if PUSH_COMMANDS:
        print("\n" + "=" * 40)
        print("SYNC REQUIRED! Run these commands to push:")
        print("=" * 40)
        for cmd in PUSH_COMMANDS:
            print(cmd)
        print("=" * 40 + "\n")
    else:
        print("\nAll synced (or no releases needed).")


def release_all_crates():
    """Simpler alternative - check all crates for changes and release if found."""
    global PUSH_COMMANDS
    PUSH_COMMANDS = []

    print("Checking for changes in all crates...")

    order = [
        "lex-core",
        "lex-babel", "lex-cli", "lex-config",
        "lex-analysis", "lex-lsp"
    ]

    for crate in order:
        repo_root, rel_path = common.get_repo_details(crate)
        current_ver = common.get_current_version(crate)
        tag_name = f"v{current_ver}"

        print(f"Checking {crate} ({current_ver}) in {rel_path}...")

        # Check if tag exists
        try:
            common.run_command(f"git rev-parse {tag_name}", cwd=repo_root, check=False)
        except Exception:
            print(f"  Tag {tag_name} not found. Assuming generic 'main' or fresh release?")
            pass

        # Diff
        cmd = f"git diff --name-only {tag_name}..HEAD -- {rel_path}"
        try:
            diff = common.run_command(cmd, cwd=repo_root, check=False)
        except Exception:
            diff = "FORCE_UPDATE"

        if diff and diff.strip():
            print(f"  Changes detected in {crate}!")
            print(f"  Releasing {crate} (patch bump)...")
            try:
                component.release_component(crate, "patch")
                record_push_command(crate)
            except Exception as e:
                print(f"  Failed to release {crate}: {e}")
        else:
            print(f"  No changes in {crate}.")

    if PUSH_COMMANDS:
        print("\n" + "=" * 40)
        print("SYNC REQUIRED! Run these commands to push:")
        print("=" * 40)
        for cmd in PUSH_COMMANDS:
            print(cmd)
        print("=" * 40 + "\n")
