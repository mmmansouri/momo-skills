#!/usr/bin/env python3
"""Cleanup merged local branches.

Deletes local branches already merged into the base branch (default: develop).
Supports dry-run, single repo, or workspace-wide cleanup.

Usage:
    python3 git_cleanup_branches.py --repo /path [--dry-run]
    python3 git_cleanup_branches.py --all-repos /workspace [--auto]
    python3 git_cleanup_branches.py --repo /path --base-branch main

Base branch resolution: --base-branch flag, then BASE_BRANCH env var,
then default "develop".
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    DEFAULT_BASE_BRANCH, run_git, get_current_branch,
    is_protected_branch, find_repos, output_json,
)


def get_merged_branches(repo_path, base_branch):
    """Get list of branches merged into base_branch (excluding protected)."""
    code, output = run_git("branch", "--merged", base_branch, cwd=repo_path)
    if code != 0 or not output:
        return []

    branches = []
    for line in output.strip().split("\n"):
        branch = line.strip().lstrip("* ")
        if branch and not is_protected_branch(branch, base_branch):
            branches.append(branch)
    return branches


def restore_original_branch(repo_path, current, base_branch, stashed):
    """Return to the branch we started on and re-apply any auto-stash.

    Checking out the original branch is always safe — even a protected one —
    since we only ever switched away from it to run the cleanup. The stash is
    popped only after a successful checkout so it can never land on the wrong
    branch. Returns a warning dict when restoration failed (stash kept), else None.
    """
    if not current or current == base_branch:
        return None
    code, output = run_git("checkout", current, cwd=repo_path)
    if code != 0:
        return {"restore_failed": current, "stash_kept": stashed, "error": output}
    if stashed:
        run_git("stash", "pop", cwd=repo_path)
    return None


def cleanup_repo(repo_path, base_branch, dry_run=False, auto=False):
    """Clean up merged branches in a single repo.

    Switches to base_branch first (auto-stashing if dirty), restores
    original branch and stash afterwards. The auto flag only suppresses
    stdout chatter; it never bypasses safety.
    """
    name = os.path.basename(repo_path)
    current = get_current_branch(repo_path)

    stashed = False
    if current != base_branch:
        if not auto:
            print(f"  Switching to {base_branch} from {current}...", file=sys.stderr)

        # Stash dirty working tree so checkout doesn't refuse / lose work.
        code, porcelain = run_git("status", "--porcelain", cwd=repo_path)
        if porcelain.strip():
            run_git("stash", "push", "-m", "auto-stash for branch cleanup", cwd=repo_path)
            stashed = True

        run_git("checkout", base_branch, cwd=repo_path)

    merged = get_merged_branches(repo_path, base_branch)

    if not merged:
        # Restore original branch even when nothing to delete.
        warning = restore_original_branch(repo_path, current, base_branch, stashed)
        result = {"repo": name, "deleted": [], "dry_run": dry_run, "status": "clean"}
        if warning:
            result["warning"] = warning
        return result

    deleted = []
    failed = []

    for branch in merged:
        if dry_run:
            deleted.append(branch)
            continue

        code, output = run_git("branch", "-d", branch, cwd=repo_path)
        if code == 0:
            deleted.append(branch)
        else:
            failed.append({"branch": branch, "error": output})

    warning = restore_original_branch(repo_path, current, base_branch, stashed)

    result = {
        "repo": name,
        "deleted": deleted,
        "dry_run": dry_run,
        "status": "success" if not failed else "partial",
    }
    if failed:
        result["failed"] = failed
    if warning:
        result["warning"] = warning

    return result


def main():
    parser = argparse.ArgumentParser(description="Cleanup merged branches")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="Single repository path")
    group.add_argument("--all-repos", help="Workspace directory containing repos")
    parser.add_argument(
        "--base-branch",
        default=DEFAULT_BASE_BRANCH,
        help=f"Base branch for merge detection (default from BASE_BRANCH env or '{DEFAULT_BASE_BRANCH}')",
    )
    parser.add_argument("--dry-run", action="store_true", help="List branches without deleting")
    parser.add_argument("--auto", action="store_true", help="Suppress informational output")
    args = parser.parse_args()

    if args.repo:
        result = cleanup_repo(args.repo, args.base_branch, args.dry_run, args.auto)
        output_json(result)
    else:
        repos = find_repos(args.all_repos)
        results = [cleanup_repo(r, args.base_branch, args.dry_run, args.auto) for r in repos]
        total_deleted = sum(len(r["deleted"]) for r in results)
        output_json({
            "repos": results,
            "total_deleted": total_deleted,
            "dry_run": args.dry_run,
            "base_branch": args.base_branch,
        })


if __name__ == "__main__":
    main()
