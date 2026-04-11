#!/usr/bin/env python3
"""Safe commit for Buy Nature projects.

Validates Jira references, scans for debug statements and secrets,
formats commit message with Co-Authored-By footer.

Usage: python3 git_safe_commit.py --epic BNAT-100 --tickets BNAT-123 --message "Add checkout"
       python3 git_safe_commit.py --epic BNAT-100 --tickets BNAT-123,BNAT-124 --message "Add order flow"
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from git_utils import (
    run_git, get_current_branch, is_protected_branch,
    scan_for_patterns, DEBUG_PATTERNS, SECRET_PATTERNS, output_json,
)

CO_AUTHOR = "Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"


def get_staged_files(cwd=None):
    """Get list of staged file paths."""
    code, output = run_git("diff", "--cached", "--name-only", cwd=cwd)
    if code != 0 or not output:
        return []
    return [f.strip() for f in output.split("\n") if f.strip()]


def get_staged_diff(cwd=None):
    """Get the full diff of staged changes."""
    code, output = run_git("diff", "--cached", cwd=cwd)
    return output if code == 0 else ""


def validate_jira_refs(epic, tickets):
    """Validate Jira references format."""
    errors = []
    pattern = r"^[A-Z]+-\d+$"

    if not re.match(pattern, epic):
        errors.append(f"Invalid epic format: {epic} (expected: BNAT-XXX)")

    for ticket in tickets:
        if not re.match(pattern, ticket):
            errors.append(f"Invalid ticket format: {ticket} (expected: BNAT-XXX)")

    return errors


def build_commit_message(epic, tickets, message):
    """Build formatted commit message with Jira references."""
    refs = f"[{epic}]"
    for ticket in tickets:
        refs += f"[{ticket}]"
    return f"{refs} {message}\n\n{CO_AUTHOR}"


def main():
    parser = argparse.ArgumentParser(description="Safe commit with Jira validation")
    parser.add_argument("--epic", required=True, help="Epic key (e.g., BNAT-100)")
    parser.add_argument("--tickets", required=True, help="Comma-separated ticket keys")
    parser.add_argument("--message", required=True, help="Commit message")
    parser.add_argument("--repo", default=os.getcwd(), help="Repository path")
    parser.add_argument("--skip-scan", action="store_true", help="Skip debug/secrets scan")
    args = parser.parse_args()

    repo = args.repo
    tickets = [t.strip() for t in args.tickets.split(",") if t.strip()]

    # Check not on protected branch
    branch = get_current_branch(repo)
    if is_protected_branch(branch):
        output_json({
            "status": "error",
            "message": f"Cannot commit directly to protected branch '{branch}'",
        })
        sys.exit(1)

    # Validate Jira references
    jira_errors = validate_jira_refs(args.epic, tickets)
    if jira_errors:
        output_json({"status": "error", "message": "Invalid Jira references", "errors": jira_errors})
        sys.exit(1)

    # Check staged files exist
    staged = get_staged_files(repo)
    if not staged:
        output_json({"status": "error", "message": "No staged files. Use 'git add' first."})
        sys.exit(1)

    # Scan staged diff for issues
    if not args.skip_scan:
        diff = get_staged_diff(repo)
        added_lines = "\n".join(
            line[1:] for line in diff.split("\n")
            if line.startswith("+") and not line.startswith("+++")
        )

        debug_hits = scan_for_patterns(added_lines, DEBUG_PATTERNS)
        secret_hits = scan_for_patterns(added_lines, SECRET_PATTERNS)

        if secret_hits:
            output_json({
                "status": "error",
                "message": "Potential secrets detected in staged changes",
                "secrets": [{"line": h[0], "content": h[1], "type": h[2]} for h in secret_hits],
            })
            sys.exit(1)

        if debug_hits:
            # Warnings only, don't block
            print(f"Warning: {len(debug_hits)} debug statement(s) found in staged changes",
                  file=sys.stderr)
            for h in debug_hits[:5]:
                print(f"  Line {h[0]}: {h[2]} — {h[1][:80]}", file=sys.stderr)

    # Build commit message
    commit_msg = build_commit_message(args.epic, tickets, args.message)

    # Execute commit
    code, output = run_git("commit", "-m", commit_msg, cwd=repo)
    if code != 0:
        output_json({"status": "error", "message": "Commit failed", "details": output})
        sys.exit(1)

    # Get commit hash
    code, commit_hash = run_git("rev-parse", "--short", "HEAD", cwd=repo)

    output_json({
        "status": "success",
        "commit": commit_hash,
        "branch": branch,
        "epic": args.epic,
        "tickets": tickets,
        "message": args.message,
        "files": staged,
        "file_count": len(staged),
    })


if __name__ == "__main__":
    main()
