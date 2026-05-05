#!/usr/bin/env python3
"""Git status report (single repo or workspace).

Generates a JSON status report including: branch, divergence, uncommitted,
stash count, last commit, and merged-branch candidates for cleanup.

Usage:
    python3 git_status_report.py --repo /path/to/repo
    python3 git_status_report.py --all-repos /path/to/workspace
    python3 git_status_report.py --repo /path --base-branch main

Base branch resolution: --base-branch flag, then BASE_BRANCH env var,
then default "develop".
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    DEFAULT_BASE_BRANCH, run_git, get_current_branch,
    has_remote_tracking, get_divergence, find_repos, output_json,
)


def get_repo_status(repo_path, base_branch):
    """Generate a comprehensive status report for a single repo."""
    name = os.path.basename(repo_path)
    branch = get_current_branch(repo_path)

    if not branch:
        return {"name": name, "path": repo_path, "status": "error", "message": "Not a git repo"}

    # Uncommitted changes (porcelain format: XY <path>)
    code, porcelain = run_git("status", "--porcelain", cwd=repo_path)
    uncommitted = [line for line in porcelain.split("\n") if line.strip()] if porcelain else []

    staged = [f for f in uncommitted if f and f[0] in "MADRC"]
    unstaged = [f for f in uncommitted if f and len(f) > 1 and f[1] in "MDRC"]
    untracked = [f for f in uncommitted if f.startswith("??")]

    tracking = has_remote_tracking(repo_path)
    divergence = get_divergence(repo_path) if tracking else None

    code, last_commit = run_git("log", "-1", "--format=%h %s (%cr)", cwd=repo_path)
    last_commit_value = last_commit if code == 0 else None

    code, stash_output = run_git("stash", "list", cwd=repo_path)
    stash_count = len(stash_output.strip().split("\n")) if stash_output.strip() else 0

    # Merged branches (cleanup candidates) — only if base branch exists locally.
    merged_branches = []
    code, _ = run_git("rev-parse", "--verify", base_branch, cwd=repo_path)
    if code == 0:
        code, merged = run_git("branch", "--merged", base_branch, cwd=repo_path)
        if merged:
            for b in merged.strip().split("\n"):
                b = b.strip().lstrip("* ")
                if b and b not in (base_branch, "main", "master"):
                    merged_branches.append(b)

    report = {
        "name": name,
        "path": repo_path,
        "branch": branch,
        "base_branch": base_branch,
        "tracking": tracking,
        "last_commit": last_commit_value,
        "changes": {
            "staged": len(staged),
            "unstaged": len(unstaged),
            "untracked": len(untracked),
        },
        "stashes": stash_count,
        "merged_branches": merged_branches,
    }

    if divergence:
        report["divergence"] = divergence

    if any([staged, unstaged, untracked]):
        report["status"] = "dirty"
    elif divergence and divergence.get("ahead", 0) > 0:
        report["status"] = "ahead"
    else:
        report["status"] = "clean"

    return report


def main():
    parser = argparse.ArgumentParser(description="Git status report (JSON)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="Single repository path")
    group.add_argument("--all-repos", help="Workspace directory containing repos")
    parser.add_argument(
        "--base-branch",
        default=DEFAULT_BASE_BRANCH,
        help=f"Base branch for merge detection (default from BASE_BRANCH env or '{DEFAULT_BASE_BRANCH}')",
    )
    args = parser.parse_args()

    if args.repo:
        report = get_repo_status(args.repo, args.base_branch)
        output_json(report)
    else:
        repos = find_repos(args.all_repos)
        if not repos:
            output_json({"status": "error", "message": f"No repos found in {args.all_repos}"})
            sys.exit(1)

        reports = [get_repo_status(r, args.base_branch) for r in repos]
        output_json({
            "repos": reports,
            "total": len(reports),
            "dirty": sum(1 for r in reports if r.get("status") == "dirty"),
            "clean": sum(1 for r in reports if r.get("status") == "clean"),
        })


if __name__ == "__main__":
    main()
