#!/usr/bin/env python3
"""Safe branch creation for Buy Nature projects.

Syncs develop, validates naming convention, creates feature branch.

Usage: python3 git_safe_branch.py --ticket BNAT-123 --description add-checkout-flow [--repo /path]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import run_git, get_current_branch, is_protected_branch, validate_branch_name, output_json


def main():
    parser = argparse.ArgumentParser(description="Safe branch creation")
    parser.add_argument("--ticket", required=True, help="Jira ticket (e.g., BNAT-123)")
    parser.add_argument("--description", required=True, help="Short description (kebab-case)")
    parser.add_argument("--type", default="feature", choices=["feature", "bugfix", "hotfix"],
                        help="Branch type (default: feature)")
    parser.add_argument("--repo", default=os.getcwd(), help="Repository path")
    args = parser.parse_args()

    repo = args.repo
    branch_name = f"{args.type}/{args.ticket}-{args.description}"

    # Validate branch name
    valid, error = validate_branch_name(branch_name)
    if not valid:
        output_json({"status": "error", "message": error})
        sys.exit(1)

    # Check for uncommitted changes
    code, status = run_git("status", "--porcelain", cwd=repo)
    if status:
        output_json({
            "status": "error",
            "message": "Uncommitted changes detected. Commit or stash before branching.",
            "uncommitted_files": len(status.strip().split("\n")),
        })
        sys.exit(1)

    # Switch to develop
    code, _ = run_git("checkout", "develop", cwd=repo)
    if code != 0:
        output_json({"status": "error", "message": "Failed to checkout develop branch"})
        sys.exit(1)

    # Pull latest develop
    code, output = run_git("pull", "origin", "develop", cwd=repo)
    if code != 0:
        output_json({
            "status": "error",
            "message": "Failed to pull origin develop",
            "details": output,
        })
        sys.exit(1)

    # Check if branch already exists
    code, existing = run_git("branch", "--list", branch_name, cwd=repo)
    if existing.strip():
        output_json({
            "status": "error",
            "message": f"Branch '{branch_name}' already exists locally",
        })
        sys.exit(1)

    # Create and switch to new branch
    code, _ = run_git("checkout", "-b", branch_name, cwd=repo)
    if code != 0:
        output_json({"status": "error", "message": f"Failed to create branch '{branch_name}'"})
        sys.exit(1)

    # Verify
    current = get_current_branch(repo)
    output_json({
        "status": "success",
        "branch": branch_name,
        "current_branch": current,
        "base": "develop",
        "ticket": args.ticket,
    })


if __name__ == "__main__":
    main()
