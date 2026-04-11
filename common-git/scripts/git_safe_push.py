#!/usr/bin/env python3
"""Safe push for Buy Nature projects.

Checks protected branches, handles first push, warns about divergence.

Usage: python3 git_safe_push.py [--repo /path] [--force-with-lease]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    run_git, get_current_branch, is_protected_branch,
    has_remote_tracking, get_divergence, output_json,
)


def main():
    parser = argparse.ArgumentParser(description="Safe push with protection checks")
    parser.add_argument("--repo", default=os.getcwd(), help="Repository path")
    parser.add_argument("--force-with-lease", action="store_true",
                        help="Use --force-with-lease (for post-rebase push)")
    args = parser.parse_args()

    repo = args.repo

    # Check branch
    branch = get_current_branch(repo)
    if not branch:
        output_json({"status": "error", "message": "Not in a git repository or detached HEAD"})
        sys.exit(1)

    # Protect develop/main
    if is_protected_branch(branch):
        output_json({
            "status": "error",
            "message": f"Cannot push directly to protected branch '{branch}'. Use a PR.",
        })
        sys.exit(1)

    # Check for unpushed commits
    tracking = has_remote_tracking(repo)

    if tracking:
        divergence = get_divergence(repo)
        if divergence and divergence["ahead"] == 0:
            output_json({"status": "skip", "message": "Nothing to push (up to date with remote)"})
            return

        if divergence and divergence["behind"] > 0 and not args.force_with_lease:
            output_json({
                "status": "warning",
                "message": (
                    f"Branch is {divergence['behind']} commit(s) behind remote. "
                    f"Consider pulling first or use --force-with-lease after rebase."
                ),
                "behind": divergence["behind"],
                "ahead": divergence["ahead"],
            })
            # Still attempt push — git will reject if needed

    # Build push command
    push_args = ["push"]
    if not tracking:
        push_args.extend(["-u", "origin", branch])
    elif args.force_with_lease:
        push_args.append("--force-with-lease")

    code, output = run_git(*push_args, cwd=repo)

    if code != 0:
        output_json({"status": "error", "message": "Push failed", "details": output})
        sys.exit(1)

    output_json({
        "status": "success",
        "branch": branch,
        "first_push": not tracking,
        "force_with_lease": args.force_with_lease,
    })


if __name__ == "__main__":
    main()
