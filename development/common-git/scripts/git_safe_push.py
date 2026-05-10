#!/usr/bin/env python3
"""Safe push with protection checks.

Blocks pushes to protected branches (base/main/master/release/*), warns when
the local branch is behind remote, and handles the first-push (-u) case.

Usage:
    python3 git_safe_push.py [--repo /path] [--force-with-lease]
    python3 git_safe_push.py --base-branch main
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    DEFAULT_BASE_BRANCH, run_git, get_current_branch,
    is_protected_branch, has_remote_tracking, get_divergence, output_json,
)


def main():
    parser = argparse.ArgumentParser(description="Safe push with protection checks")
    parser.add_argument("--repo", default=os.getcwd(), help="Repository path")
    parser.add_argument(
        "--base-branch",
        default=DEFAULT_BASE_BRANCH,
        help=f"Base branch (default from BASE_BRANCH env or '{DEFAULT_BASE_BRANCH}')",
    )
    parser.add_argument(
        "--force-with-lease",
        action="store_true",
        help="Use --force-with-lease (post-rebase push on YOUR feature branch only)",
    )
    args = parser.parse_args()

    repo = args.repo
    branch = get_current_branch(repo)
    if not branch:
        output_json({"status": "error", "message": "Not in a git repository or detached HEAD"})
        sys.exit(1)

    if is_protected_branch(branch, args.base_branch):
        output_json({
            "status": "error",
            "message": f"Cannot push directly to protected branch '{branch}'. Use a PR.",
        })
        sys.exit(1)

    tracking = has_remote_tracking(repo)

    if tracking:
        divergence = get_divergence(repo)
        if divergence and divergence["ahead"] == 0 and divergence["behind"] == 0:
            output_json({"status": "skip", "message": "Nothing to push (up to date with remote)"})
            return

        # Behind without explicit force-with-lease: warn but still attempt push;
        # git itself will reject a non-fast-forward push.
        if divergence and divergence["behind"] > 0 and not args.force_with_lease:
            output_json({
                "status": "warning",
                "message": (
                    f"Branch is {divergence['behind']} commit(s) behind remote. "
                    f"Pull/rebase first, or use --force-with-lease after a local rebase."
                ),
                "behind": divergence["behind"],
                "ahead": divergence["ahead"],
            })

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
