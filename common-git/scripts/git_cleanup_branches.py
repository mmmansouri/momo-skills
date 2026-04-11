#!/usr/bin/env python3
"""Cleanup merged branches in Buy Nature repositories.

Deletes local branches that have been merged into develop.
Supports dry-run mode and auto mode (skip confirmation).

Usage: python3 git_cleanup_branches.py --repo /path [--dry-run] [--auto]
       python3 git_cleanup_branches.py --all-repos /workspace [--auto]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import run_git, get_current_branch, is_protected_branch, find_repos, output_json


def get_merged_branches(repo_path):
    """Get list of branches merged into develop (excluding protected)."""
    code, output = run_git("branch", "--merged", "develop", cwd=repo_path)
    if code != 0 or not output:
        return []

    branches = []
    for line in output.strip().split("\n"):
        branch = line.strip().lstrip("* ")
        if branch and not is_protected_branch(branch):
            branches.append(branch)
    return branches


def cleanup_repo(repo_path, dry_run=False, auto=False):
    """Clean up merged branches in a single repo."""
    name = os.path.basename(repo_path)
    current = get_current_branch(repo_path)

    # Ensure we're on develop
    if current != "develop":
        if not auto:
            print(f"  Switching to develop from {current}...")

        # Stash if dirty
        code, porcelain = run_git("status", "--porcelain", cwd=repo_path)
        stashed = False
        if porcelain.strip():
            run_git("stash", "push", "-m", "auto-stash for branch cleanup", cwd=repo_path)
            stashed = True

        run_git("checkout", "develop", cwd=repo_path)

    merged = get_merged_branches(repo_path)

    if not merged:
        return {"repo": name, "deleted": [], "dry_run": dry_run, "status": "clean"}

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

    # Restore previous branch and stash
    if current != "develop" and not is_protected_branch(current):
        code, _ = run_git("checkout", current, cwd=repo_path)
        if stashed:
            run_git("stash", "pop", cwd=repo_path)

    result = {
        "repo": name,
        "deleted": deleted,
        "dry_run": dry_run,
        "status": "success" if not failed else "partial",
    }
    if failed:
        result["failed"] = failed

    return result


def main():
    parser = argparse.ArgumentParser(description="Cleanup merged branches")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="Single repository path")
    group.add_argument("--all-repos", help="Workspace directory containing repos")
    parser.add_argument("--dry-run", action="store_true", help="List branches without deleting")
    parser.add_argument("--auto", action="store_true", help="Skip confirmations")
    args = parser.parse_args()

    if args.repo:
        result = cleanup_repo(args.repo, args.dry_run, args.auto)
        output_json(result)
    else:
        repos = find_repos(args.all_repos)
        results = [cleanup_repo(r, args.dry_run, args.auto) for r in repos]
        total_deleted = sum(len(r["deleted"]) for r in results)
        output_json({
            "repos": results,
            "total_deleted": total_deleted,
            "dry_run": args.dry_run,
        })


if __name__ == "__main__":
    main()
