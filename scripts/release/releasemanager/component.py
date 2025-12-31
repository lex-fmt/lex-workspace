"""
Component release management - update and release individual components.
"""

import os
import sys

from . import common
from . import version


def release_component(component, part):
    """Full release cycle for a component: bump version, commit, and tag."""

    # 1. Update version
    try:
        version.update_component_version(component, part)
        new_version = common.get_current_version(component)
    except Exception as e:
        print(f"Failed to update version: {e}")
        sys.exit(1)

    # 2. Get repo path
    repo_path = None
    if component in common.CRATES:
        manifest_path = common.CRATES[component]
        repo_dir = manifest_path.split("/")[0]
        repo_path = os.path.join(common.ROOT_DIR, repo_dir)
    elif component in common.TOOLS:
        repo_path = os.path.join(common.ROOT_DIR, common.TOOLS[component]["path"])

    if not repo_path:
        print(f"Could not determine repo path for {component}")
        sys.exit(1)

    tag_name = common.get_tag_name(component, new_version)
    commit_msg = f"chore: release {tag_name}"

    print(f"Committing and tagging in {repo_path}...")

    # 3. Check if anything to commit
    status = common.run_command("git status --porcelain", cwd=repo_path)
    if not status:
        print("No changes to commit (version might be already bumped?)")
    else:
        common.run_command("git add .", cwd=repo_path, check=True)
        common.run_command(f'git commit -m "{commit_msg}"', cwd=repo_path, check=True)

    # 4. Tag
    try:
        # Check if tag already exists
        try:
            common.run_command(f"git rev-parse {tag_name}", cwd=repo_path, check=False)
            print(f"Tag {tag_name} already exists, skipping tag creation")
        except Exception:
            common.run_command(f"git tag {tag_name}", cwd=repo_path, check=True)
            print(f"Tagged {tag_name}")
    except Exception as e:
        print(f"Failed to create tag {tag_name}: {e}")
        sys.exit(1)

    # 5. Push (skipped by default for safety)
    print("Pushing...")
    # common.run_command("git push && git push --tags", cwd=repo_path, check=True)
    print("(Push skipped for safety - run manually)")

    return new_version


def has_changes_since_tag(component):
    """Check if component has changes since its latest tag."""
    repo_root, rel_path = common.get_repo_details(component)
    current_ver = common.get_current_version(component)
    tag_name = common.get_tag_name(component, current_ver)

    # Check if tag exists
    try:
        common.run_command(f"git rev-parse {tag_name}", cwd=repo_root, check=False)
        tag_exists = True
    except Exception:
        tag_exists = False

    if not tag_exists:
        return True  # No tag means needs release

    # Check diff
    cmd = f"git diff --name-only {tag_name}..HEAD -- {rel_path}"
    try:
        diff = common.run_command(cmd, cwd=repo_root, check=False)
        return bool(diff and diff.strip())
    except Exception:
        return True  # Assume changes if diff fails
