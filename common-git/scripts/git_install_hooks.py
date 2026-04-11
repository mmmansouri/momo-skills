#!/usr/bin/env python3
"""Install git hooks for Buy Nature repositories.

Installs a pre-commit hook that checks for:
- Direct commits to develop/main (blocked)
- Debug statements in staged code (warning)
- Secret patterns in staged code (blocked)
- Large files > 500KB (warning)

Usage: python3 git_install_hooks.py --repo /path
       python3 git_install_hooks.py --all-repos /workspace
"""
import argparse
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import find_repos, output_json

HOOK_MARKER = "# BUY-NATURE-HOOKS-V2"

PRE_COMMIT_HOOK = f"""#!/bin/bash
{HOOK_MARKER}
# Auto-installed by Buy Nature git_install_hooks.py
# Checks: protected branch, debug code, secrets, large files

set -e

branch=$(git rev-parse --abbrev-ref HEAD)

# Block commits to protected branches
if [[ "$branch" == "develop" || "$branch" == "main" || "$branch" == "master" ]]; then
  echo "BLOCKED: Direct commits to '$branch' are not allowed."
  echo "Create a feature branch: git checkout -b feature/BNAT-XXX-description"
  exit 1
fi

# Scan staged files for debug/secret patterns
staged_files=$(git diff --cached --name-only --diff-filter=ACM)
has_warning=0
has_block=0

for file in $staged_files; do
  # Skip binary files
  if ! git diff --cached --name-only --diff-filter=ACM -- "$file" | grep -qE '\\.(java|ts|js|py|json|yml|yaml|xml|properties|env)$'; then
    continue
  fi

  content=$(git show ":$file" 2>/dev/null || true)

  # Check for secrets (blocking)
  if echo "$content" | grep -qE '(password|secret|token|api_key)\\s*=\\s*["\\''][^"\\'\\']+["\\'']'; then
    echo "BLOCKED: Potential secret in $file"
    has_block=1
  fi
  if echo "$content" | grep -qE '-----BEGIN (RSA )?PRIVATE KEY-----'; then
    echo "BLOCKED: Private key detected in $file"
    has_block=1
  fi

  # Check for debug statements (warning)
  if echo "$content" | grep -qE 'console\\.(log|debug)\\b|System\\.(out|err)\\.print|debugger\\b'; then
    echo "WARNING: Debug statement in $file"
    has_warning=1
  fi
done

# Check large files
for file in $staged_files; do
  if [ -f "$file" ]; then
    size=$(wc -c < "$file" 2>/dev/null || echo 0)
    if [ "$size" -gt 512000 ]; then
      echo "WARNING: Large file ($size bytes): $file"
      has_warning=1
    fi
  fi
done

if [ $has_block -eq 1 ]; then
  exit 1
fi

if [ $has_warning -eq 1 ]; then
  echo "(Warnings above are non-blocking — commit will proceed)"
fi

exit 0
"""


def install_hook(repo_path):
    """Install or update pre-commit hook in a repository."""
    name = os.path.basename(repo_path)
    hooks_dir = os.path.join(repo_path, ".git", "hooks")

    if not os.path.isdir(hooks_dir):
        return {"repo": name, "status": "error", "message": "Not a git repo"}

    hook_path = os.path.join(hooks_dir, "pre-commit")

    # Check if our hook is already installed
    if os.path.isfile(hook_path):
        with open(hook_path, "r", encoding="utf-8") as f:
            content = f.read()
        if HOOK_MARKER in content:
            return {"repo": name, "status": "skip", "message": "Hook already installed"}

        # Backup existing hook
        backup_path = hook_path + ".backup"
        os.rename(hook_path, backup_path)

    # Write the hook
    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(PRE_COMMIT_HOOK)

    # Make executable (Unix)
    if os.name != "nt":
        os.chmod(hook_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

    return {"repo": name, "status": "installed", "path": hook_path}


def main():
    parser = argparse.ArgumentParser(description="Install git hooks")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="Single repository path")
    group.add_argument("--all-repos", help="Workspace directory containing repos")
    args = parser.parse_args()

    if args.repo:
        result = install_hook(args.repo)
        output_json(result)
    else:
        repos = find_repos(args.all_repos)
        results = [install_hook(r) for r in repos]
        installed = sum(1 for r in results if r["status"] == "installed")
        output_json({
            "repos": results,
            "total": len(results),
            "installed": installed,
        })


if __name__ == "__main__":
    main()
