#!/usr/bin/env python3
"""Check prerequisites for common-builder scripts."""
import json
import shutil
import sys


def check_command(name, install_hint=None):
    """Check if a command is available on PATH."""
    if shutil.which(name):
        return True
    hint = install_hint or f"Install {name} via your package manager"
    print(json.dumps({"ok": False, "missing": name, "install": hint}))
    sys.exit(1)


def main():
    check_command("python3", "Install Python 3 from https://python.org")
    check_command("mvn", "Install Maven via SDKMAN: sdk install maven")
    check_command("node", "Install Node.js from https://nodejs.org")
    check_command("npm", "Comes with Node.js installation")

    print(json.dumps({"ok": True, "message": "All prerequisites satisfied"}))


if __name__ == "__main__":
    main()
