#!/usr/bin/env python3
"""Setup GitHub App authentication for Claude Code.

Creates ~/.claude/secrets/github-app.pem and configures git credential helper.

Usage: python3 github_setup.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    secrets_dir = os.path.join(os.path.expanduser("~"), ".claude", "secrets")
    pem_file = os.path.join(secrets_dir, "github-app.pem")
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    print("GitHub App Setup for Claude Code")
    print()

    # 1. Create secrets directory
    if not os.path.isdir(secrets_dir):
        print(f"Creating secrets directory: {secrets_dir}")
        os.makedirs(secrets_dir, exist_ok=True)

    # 2. Check if PEM already exists
    if os.path.isfile(pem_file):
        print(f"PEM file already exists: {pem_file}")
    else:
        print("Please copy your GitHub App private key (PEM file) to:")
        print(f"   {pem_file}")
        print()
        print("The PEM file should be the same as used on OpenClaw VPS.")
        print("You can find it at: ~/.openclaw/secrets/github-app.pem")
        print()
        input("Press Enter when you've copied the file...")

        if not os.path.isfile(pem_file):
            print("PEM file not found. Setup incomplete.", file=sys.stderr)
            sys.exit(1)

    # 3. Test token generation
    print()
    print("Testing token generation...")
    try:
        from github_auth import get_token
        token = get_token()
        print(f"Token generated successfully!")
        print(f"   Token: {token[:20]}...")
    except SystemExit:
        print("Token generation failed.", file=sys.stderr)
        sys.exit(1)

    # 4. Offer to configure git credential helper
    print()
    print("Git Credential Helper Configuration")
    print("To make git operations use GitHub App tokens automatically:")
    credential_helper = f"!python3 {os.path.join(scripts_dir, 'git_credential_buynature.py')}"
    print(f"   git config --global credential.helper '{credential_helper}'")
    print()
    reply = input("Configure git credential helper now? (y/n) ").strip().lower()

    if reply == "y":
        subprocess.run(
            ["git", "config", "--global", "credential.helper", credential_helper],
            check=True,
        )
        print("Git credential helper configured!")
    else:
        print("Skipped git credential helper configuration")
        print("   You can configure it later by running the command above")

    print()
    print("Setup complete!")
    print()
    print("Next steps:")
    print("1. Agents will now use GitHub App tokens automatically")
    print("2. PRs will be created as 'rahman-momo-bot[bot]'")
    print("3. Tokens are regenerated automatically (1 hour expiry)")


if __name__ == "__main__":
    main()
