#!/usr/bin/env python3
"""Wrapper for 'gh' CLI that automatically uses GitHub App token.

Ensures all 'gh' commands (gh pr create, gh api, etc.) use the GitHub App
instead of personal credentials.

Usage: python3 gh_with_app_token.py <gh-command> [args...]
Example: python3 gh_with_app_token.py pr create --title "My PR" --body "..."
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gh_with_app_token.py <gh-command> [args...]", file=sys.stderr)
        print("Example: python3 gh_with_app_token.py pr create --title 'My PR'", file=sys.stderr)
        sys.exit(1)

    # Generate GitHub App token
    try:
        from github_auth import get_token
        token = get_token()
    except SystemExit:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        print("Failed to generate GitHub App token", file=sys.stderr)
        print(f"Run: python3 {os.path.join(scripts_dir, 'github_setup.py')}", file=sys.stderr)
        sys.exit(1)

    # Execute gh with GitHub App token
    env = os.environ.copy()
    env["GH_TOKEN"] = token

    result = subprocess.run(["gh"] + sys.argv[1:], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
