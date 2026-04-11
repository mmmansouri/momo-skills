#!/usr/bin/env python3
"""Git credential helper for Buy Nature GitHub App.

Generates a fresh installation token on every git auth request.
Configure with: git config --global credential.helper '!python3 /path/to/git_credential_buynature.py'

Git calls this script with "get" as argument when it needs credentials.
We return username + password (fresh GitHub App installation token).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # Only respond to "get" requests
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action != "get":
        return

    # Read input from git (protocol, host, etc.)
    host = ""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        if "=" in line:
            key, value = line.split("=", 1)
            if key == "host":
                host = value

    # Only handle github.com requests
    if host != "github.com":
        return

    # Generate fresh token
    try:
        from github_auth import get_token
        token = get_token()
    except (SystemExit, Exception) as e:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Failed to generate GitHub token", file=sys.stderr)
        print(f"Run: python3 {os.path.join(scripts_dir, 'github_setup.py')}", file=sys.stderr)
        sys.exit(1)

    # Return credentials to git
    print("protocol=https")
    print("host=github.com")
    print("username=x-access-token")
    print(f"password={token}")


if __name__ == "__main__":
    main()
