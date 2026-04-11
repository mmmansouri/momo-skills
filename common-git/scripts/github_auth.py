#!/usr/bin/env python3
"""GitHub App authentication for Buy Nature.

Shared module used by GitHub/git scripts. Replaces github-detect-env.sh + github-jwt.sh.
Handles environment detection, JWT generation (RS256), and installation token management.

Usage as module:
    from github_auth import get_token, detect_env, generate_jwt

Usage as CLI (test auth):
    python3 github_auth.py
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

APP_ID = "2790539"
INSTALLATION_ID = "107832514"


def detect_env():
    """Detect assistant environment and locate GitHub App PEM file.

    Checks OpenClaw first, then Claude Code. Returns dict with:
      - pem_path: absolute path to github-app.pem
      - env: 'openclaw' or 'claude-code'
    """
    home = os.path.expanduser("~")

    candidates = [
        (os.path.join(home, ".openclaw", "secrets", "github-app.pem"), "openclaw"),
        (os.path.join(home, ".claude", "secrets", "github-app.pem"), "claude-code"),
    ]

    for path, env_name in candidates:
        if os.path.isfile(path):
            return {"pem_path": path, "env": env_name}

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    print("No GitHub App PEM file found.", file=sys.stderr)
    for path, _ in candidates:
        print(f"  {path} (not found)", file=sys.stderr)
    print(f"  Run: python3 {os.path.join(scripts_dir, 'github_setup.py')}", file=sys.stderr)
    sys.exit(1)


def _base64url_encode(data):
    """Base64 URL-safe encode without padding."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_jwt(pem_path=None, app_id=APP_ID):
    """Generate a JWT for GitHub App authentication using RS256.

    Uses openssl for RSA signing (same dependency as the original bash scripts).
    Python handles base64 URL-safe encoding and JSON natively.
    """
    if pem_path is None:
        env = detect_env()
        pem_path = env["pem_path"]

    now = int(time.time())
    header = _base64url_encode(json.dumps({"alg": "RS256", "typ": "JWT"}))
    payload = _base64url_encode(json.dumps({
        "iat": now - 60,
        "exp": now + 600,
        "iss": app_id,
    }))

    # Sign with openssl (cross-platform, same dependency as bash version)
    signing_input = f"{header}.{payload}"
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", pem_path],
            input=signing_input.encode("ascii"),
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        print("openssl not found. Install OpenSSL or ensure it's in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"JWT signing failed: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

    signature = _base64url_encode(result.stdout)
    return f"{header}.{payload}.{signature}"


def get_installation_token(jwt=None, installation_id=INSTALLATION_ID):
    """Exchange a JWT for a GitHub App installation access token.

    Returns the token string (valid for 1 hour).
    """
    if jwt is None:
        jwt = generate_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    req = urllib.request.Request(
        url,
        data=b"",
        headers={
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Failed to get installation token (HTTP {e.code}): {body}", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print(f"No 'token' in GitHub API response: {data}", file=sys.stderr)
        sys.exit(1)


def get_token():
    """High-level: detect env, generate JWT, get installation token."""
    env = detect_env()
    jwt = generate_jwt(env["pem_path"])
    return get_installation_token(jwt)


def main():
    """CLI: test GitHub App authentication."""
    env = detect_env()
    print(f"Environment: {env['env']}")
    print(f"PEM: {env['pem_path']}")

    jwt = generate_jwt(env["pem_path"])
    print(f"JWT: {jwt[:50]}...")

    token = get_installation_token(jwt)
    print(f"Token: {token[:20]}...")


if __name__ == "__main__":
    main()
