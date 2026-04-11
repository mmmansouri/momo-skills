#!/usr/bin/env python3
"""Shared Git utility functions for Buy Nature scripts.

Used by git_safe_commit.py, git_safe_push.py, git_safe_branch.py,
git_status_report.py, git_cleanup_branches.py, git_install_hooks.py.
"""
import json
import os
import re
import subprocess
import sys


PROTECTED_BRANCHES = {"develop", "main", "master"}


def run_git(*args, cwd=None):
    """Run a git command and return (exit_code, stdout_text).

    Args:
        *args: Git subcommand and arguments (e.g., "status", "--porcelain")
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (exit_code, stdout_string)
    """
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        print("git not found. Install Git or ensure it's in PATH.", file=sys.stderr)
        sys.exit(1)


def get_repo_root(path=None):
    """Get the git repository root directory."""
    code, root = run_git("rev-parse", "--show-toplevel", cwd=path)
    if code != 0:
        return None
    return root


def get_current_branch(cwd=None):
    """Get the current branch name."""
    code, branch = run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    if code != 0:
        return None
    return branch


def is_protected_branch(branch):
    """Check if a branch name is protected."""
    if branch in PROTECTED_BRANCHES:
        return True
    if branch.startswith("release/"):
        return True
    return False


def has_remote_tracking(cwd=None):
    """Check if current branch has a remote tracking branch."""
    code, _ = run_git("rev-parse", "--abbrev-ref", "@{u}", cwd=cwd)
    return code == 0


def get_divergence(cwd=None):
    """Get ahead/behind counts relative to upstream.

    Returns dict: {'ahead': N, 'behind': N} or None if no tracking.
    """
    if not has_remote_tracking(cwd):
        return None

    code, output = run_git("rev-list", "--left-right", "--count", "HEAD...@{u}", cwd=cwd)
    if code != 0:
        return None

    parts = output.split()
    if len(parts) == 2:
        return {"ahead": int(parts[0]), "behind": int(parts[1])}
    return None


def find_repos(base_dir):
    """Find all git repositories under base_dir (1 level deep)."""
    repos = []
    if not os.path.isdir(base_dir):
        return repos
    for entry in sorted(os.listdir(base_dir)):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(os.path.join(full_path, ".git")):
            repos.append(full_path)
    return repos


def validate_branch_name(name):
    """Validate branch naming convention: type/BNAT-XXX-description.

    Returns (is_valid, error_message).
    """
    pattern = r"^(feature|bugfix|hotfix|release)/[A-Z]+-\d+(-[a-z0-9-]+)?$"
    if re.match(pattern, name):
        return True, ""

    # Check for release branch
    if re.match(r"^release/v\d+\.\d+\.\d+$", name):
        return True, ""

    return False, (
        f"Invalid branch name: {name}. "
        f"Expected: feature/BNAT-XXX-description or release/vX.Y.Z"
    )


def scan_for_patterns(content, patterns):
    """Scan content for patterns (debug statements, secrets, etc.).

    Args:
        content: File content string
        patterns: List of (pattern_regex, description) tuples

    Returns:
        List of (line_number, line, description) tuples for matches
    """
    findings = []
    for i, line in enumerate(content.split("\n"), 1):
        for pattern, desc in patterns:
            if re.search(pattern, line):
                findings.append((i, line.strip(), desc))
    return findings


DEBUG_PATTERNS = [
    (r"\bconsole\.(log|debug|warn|error)\b", "console.log/debug/warn/error"),
    (r"\bSystem\.(out|err)\.print", "System.out/err.print"),
    (r"\bprint\s*\(", "print() statement"),
    (r"//\s*TODO\b", "TODO comment"),
    (r"//\s*FIXME\b", "FIXME comment"),
    (r"debugger\b", "debugger statement"),
]

SECRET_PATTERNS = [
    (r"(password|secret|token|api_key|apikey)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
    (r"-----BEGIN (RSA )?PRIVATE KEY-----", "Private key"),
    (r"(ghp_|ghs_|gho_|github_pat_)[A-Za-z0-9_]+", "GitHub token"),
    (r"sk-(live|test)_[A-Za-z0-9]+", "Stripe key"),
]


def output_json(data):
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=2))
