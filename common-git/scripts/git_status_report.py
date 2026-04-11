#!/usr/bin/env python3
"""Git status report for Buy Nature projects.

Generates JSON status report for a single repo or all repos.

Usage: python3 git_status_report.py --repo /path/to/repo
       python3 git_status_report.py --all-repos /path/to/workspace
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    run_git, get_current_branch, get_repo_root,
    has_remote_tracking, get_divergence, find_repos, output_json,
)


def get_repo_status(repo_path):
    """Generate a comprehensive status report for a single repo."""
    name = os.path.basename(repo_path)
    branch = get_current_branch(repo_path)

    if not branch:
        return {"name": name, "path": repo_path, "status": "error", "message": "Not a git repo"}

    # Uncommitted changes
    code, porcelain = run_git("status", "--porcelain", cwd=repo_path)
    uncommitted = [line.strip() for line in porcelain.split("\n") if line.strip()] if porcelain else []

    staged = [f for f in uncommitted if f and f[0] in "MADRC"]
    unstaged = [f for f in uncommitted if f and f[1] in "MDRC"]
    untracked = [f for f in uncommitted if f.startswith("??")]

    # Remote tracking
    tracking = has_remote_tracking(repo_path)
    divergence = get_divergence(repo_path) if tracking else None

    # Last commit
    code, last_commit = run_git("log", "-1", "--format=%h %s (%cr)", cwd=repo_path)

    # Stash count
    code, stash_output = run_git("stash", "list", cwd=repo_path)
    stash_count = len(stash_output.strip().split("\n")) if stash_output.strip() else 0

    # Merged branches (candidates for cleanup)
    code, merged = run_git("branch", "--merged", "develop", cwd=repo_path)
    merged_branches = []
    if merged:
        for b in merged.strip().split("\n"):
            b = b.strip().lstrip("* ")
            if b and b not in ("develop", "main", "master"):
                merged_branches.append(b)

    report = {
        "name": name,
        "path": repo_path,
        "branch": branch,
        "tracking": tracking,
        "last_commit": last_commit if code == 0 else None,
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

    # Overall status
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
    args = parser.parse_args()

    if args.repo:
        report = get_repo_status(args.repo)
        output_json(report)
    else:
        repos = find_repos(args.all_repos)
        if not repos:
            output_json({"status": "error", "message": f"No repos found in {args.all_repos}"})
            sys.exit(1)

        reports = [get_repo_status(r) for r in repos]
        output_json({
            "repos": reports,
            "total": len(reports),
            "dirty": sum(1 for r in reports if r.get("status") == "dirty"),
            "clean": sum(1 for r in reports if r.get("status") == "clean"),
        })


if __name__ == "__main__":
    main()
