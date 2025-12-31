"""
Command-line interface for release manager.
"""

import argparse
import sys

from . import common
from . import component
from . import dependencies
from . import orchestrate
from . import status
from . import version


def cmd_check_status(args):
    """Check release status."""
    status.check_status()


def cmd_get_version(args):
    """Get version of a component."""
    try:
        ver = version.get_version(args.component)
        if ver:
            print(ver)
        else:
            print(f"Error: Version not found for {args.component}")
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_set_version(args):
    """Set version of a component."""
    try:
        version.set_version(args.component, args.version)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_set_dep_version(args):
    """Set dependency version."""
    try:
        dependencies.set_dep_version(args.component, args.dep, args.version)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_bump_version(args):
    """Bump a version string."""
    try:
        new_ver = version.bump_version(args.version, args.part, args.preid)
        print(new_ver)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_update(args):
    """Update component version (bump + set)."""
    try:
        version.update_component_version(args.component, args.part)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_release(args):
    """Release a component (update + commit + tag)."""
    try:
        component.release_component(args.component, args.part)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_propagate_deps(args):
    """Propagate library versions to dependent crates."""
    dependencies.propagate_deps()


def cmd_propagate_lsp(args):
    """Propagate LSP version to client tools."""
    dependencies.propagate_lsp()


def cmd_release_all(args):
    """Full release orchestration."""
    orchestrate.release_all()


def cmd_release_all_crates(args):
    """Release all crates with changes."""
    orchestrate.release_all_crates()


def main(argv=None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="release-manager",
        description="Unified release automation for Lex workspace",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check-status
    p_status = subparsers.add_parser("check-status", help="Show release status report")
    p_status.set_defaults(func=cmd_check_status)

    # get-version
    p_get_ver = subparsers.add_parser("get-version", help="Get version of a component")
    p_get_ver.add_argument("component", choices=common.get_all_components(), help="Component name")
    p_get_ver.set_defaults(func=cmd_get_version)

    # set-version
    p_set_ver = subparsers.add_parser("set-version", help="Set version of a component")
    p_set_ver.add_argument("component", choices=common.get_all_components(), help="Component name")
    p_set_ver.add_argument("version", help="New version string")
    p_set_ver.set_defaults(func=cmd_set_version)

    # set-dep-version
    p_set_dep = subparsers.add_parser("set-dep-version", help="Set dependency version")
    p_set_dep.add_argument("component", choices=common.get_all_components(), help="Component name")
    p_set_dep.add_argument("dep", help="Dependency name")
    p_set_dep.add_argument("version", help="New version string")
    p_set_dep.set_defaults(func=cmd_set_dep_version)

    # bump-version
    p_bump = subparsers.add_parser("bump-version", help="Calculate next version")
    p_bump.add_argument("version", help="Current version")
    p_bump.add_argument("part", choices=["major", "minor", "patch", "premajor", "preminor", "prepatch"], help="Version part to bump")
    p_bump.add_argument("--preid", help="Prerelease identifier")
    p_bump.set_defaults(func=cmd_bump_version)

    # update
    p_update = subparsers.add_parser("update", help="Update component version")
    p_update.add_argument("component", choices=common.get_all_components(), help="Component name")
    p_update.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    p_update.set_defaults(func=cmd_update)

    # release
    p_release = subparsers.add_parser("release", help="Release a component (update + commit + tag)")
    p_release.add_argument("component", choices=common.get_all_components(), help="Component name")
    p_release.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    p_release.set_defaults(func=cmd_release)

    # propagate-deps
    p_prop_deps = subparsers.add_parser("propagate-deps", help="Propagate library versions to dependents")
    p_prop_deps.set_defaults(func=cmd_propagate_deps)

    # propagate-lsp
    p_prop_lsp = subparsers.add_parser("propagate-lsp", help="Propagate LSP version to clients")
    p_prop_lsp.set_defaults(func=cmd_propagate_lsp)

    # release-all
    p_release_all = subparsers.add_parser("release-all", help="Full release orchestration")
    p_release_all.set_defaults(func=cmd_release_all)

    # release-all-crates
    p_release_crates = subparsers.add_parser("release-all-crates", help="Release all crates with changes")
    p_release_crates.set_defaults(func=cmd_release_all_crates)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
