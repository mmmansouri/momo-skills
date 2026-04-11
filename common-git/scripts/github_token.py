#!/usr/bin/env python3
"""Generate a GitHub App installation token.

Outputs just the token string (for use in scripts and credential helpers).

Usage: python3 github_token.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from github_auth import get_token


def main():
    token = get_token()
    print(token)


if __name__ == "__main__":
    main()
