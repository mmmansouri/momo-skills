#!/usr/bin/env python3
"""Shared Git utility functions for common-git scripts.

Used by git_status_report.py, git_safe_push.py, git_cleanup_branches.py.

Configuration via environment variables (with safe defaults):
  - BASE_BRANCH   : integration branch (default: "develop")
  - JIRA_PREFIX   : ticket prefix used in branch names (default: "TICKET")
                    Multiple prefixes may be passed as a comma-separated list,
                    e.g. JIRA_PREFIX="PROJ,TICKET".

Branch naming regex is built from JIRA_PREFIX, so projects with a custom
prefix only need to export the env var (no code change required).
"""
import json
import os
import re
import subprocess
import sys


# Integration branch protection: configurable + always-protected names.
DEFAULT_BASE_BRANCH = os.environ.get("BASE_BRANCH", "develop")
ALWAYS_PROTECTED = {"main", "master"}


def _jira_prefix_pattern():
    """Build an alternation regex group from JIRA_PREFIX env var.

    Default: TICKET. Comma-separated list supported (e.g. "PROJ,TICKET").
    """
    raw = os.environ.get("JIRA_PREFIX", "TICKET")
    prefixes = [p.strip() for p in raw.split(",") if p.strip()]
    if not prefixes:
        prefixes = ["TICKET"]
    # Escape each prefix to be safe against accidental regex metachars.
    return "(?:" + "|".join(re.escape(p) for p in prefixes) + ")"


def run_git(*args, cwd=None):
    """Run a git command and return (exit_code, stdout_text).

    Returns:
        (exit_code, stdout_string). stderr is dropped on purpose; callers
        that need it should re-run with capture or use subprocess directly.
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
        # Hard fail: every script in this skill assumes git is on PATH.
        print("git not found. Install Git or ensure it's in PATH.", file=sys.stderr)
        sys.exit(1)


def get_repo_root(path=None):
    """Get the git repository root directory, or None if not in a repo."""
    code, root = run_git("rev-parse", "--show-toplevel", cwd=path)
    return root if code == 0 else None


def get_current_branch(cwd=None):
    """Get the current branch name, or None if detached / not in a repo."""
    code, branch = run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    return branch if code == 0 else None


def is_protected_branch(branch, base_branch=None):
    """Check if a branch name is protected (no direct commits, no rebase).

    A branch is protected if it is:
      - the configured base branch (default: develop)
      - main / master
      - any release/* branch
    """
    base = base_branch or DEFAULT_BASE_BRANCH
    if branch == base or branch in ALWAYS_PROTECTED:
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

    Returns dict {'ahead': N, 'behind': N} or None if no tracking branch.
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
    """Validate branch naming convention: type/PREFIX-NNN-description.

    Prefix is read from JIRA_PREFIX env var (default: TICKET, comma-separated
    list supported). Release branches (release/vX.Y.Z) are also accepted.

    Returns (is_valid, error_message).
    """
    prefix_group = _jira_prefix_pattern()
    pattern = rf"^(feature|bugfix|hotfix|release)/{prefix_group}-\d+(-[a-z0-9-]+)?$"
    if re.match(pattern, name):
        return True, ""

    if re.match(r"^release/v\d+\.\d+\.\d+$", name):
        return True, ""

    expected = f"{prefix_group.replace('(?:', '').replace(')', '')}-NNN-description"
    return False, (
        f"Invalid branch name: {name}. "
        f"Expected: feature/{expected} or release/vX.Y.Z"
    )


def scan_for_patterns(content, patterns):
    """Scan content for regex patterns; return (line_no, line, description) tuples."""
    findings = []
    for i, line in enumerate(content.split("\n"), 1):
        for pattern, desc in patterns:
            if re.search(pattern, line):
                findings.append((i, line.strip(), desc))
    return findings


# Common debug-statement signatures across languages used in typical projects.
DEBUG_PATTERNS = [
    (r"\bconsole\.(log|debug|warn|error)\b", "console.log/debug/warn/error"),
    (r"\bSystem\.(out|err)\.print", "System.out/err.print"),
    (r"\bprint\s*\(", "print() statement"),
    (r"//\s*TODO\b", "TODO comment"),
    (r"//\s*FIXME\b", "FIXME comment"),
    (r"debugger\b", "debugger statement"),
]

# High-signal secret signatures. Conservative on purpose: false negatives are
# preferred over false positives for a generic checker.
SECRET_PATTERNS = [
    (r"(password|secret|token|api_key|apikey)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
    (r"-----BEGIN (RSA )?PRIVATE KEY-----", "Private key"),
    (r"(ghp_|ghs_|gho_|github_pat_)[A-Za-z0-9_]+", "GitHub token"),
    (r"sk-(live|test)_[A-Za-z0-9]+", "Stripe key"),
]


def output_json(data):
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=2))
