#!/usr/bin/env python3
"""Block dangerous build commands that cause context overflow.

Usage:
    python3 safe_exec.py <command...>

If the command matches a dangerous pattern (mvn, npm build, gradle),
it is blocked with an error message directing to build.py.
Otherwise, the command is executed normally.
"""
import json
import os
import subprocess
import sys

DANGEROUS_PATTERNS = [
    "mvn clean", "mvn compile", "mvn test", "mvn verify",
    "mvn package", "mvn install", "./mvnw",
    "mvnd clean", "mvnd compile", "mvnd test", "mvnd verify",
    "mvnd package", "mvnd install",
    "npm run build", "npm run test", "npm test",
    "ng build", "ng test", "npx ng",
    "gradle build", "gradle test", "./gradlew",
]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No command provided"}))
        sys.exit(1)

    command = " ".join(sys.argv[1:])

    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            print(
                f"BLOCKED: Dangerous build command detected\n"
                f"\n"
                f"Command: {command}\n"
                f"Reason: Streaming build logs causes context overflow (200K+ tokens)\n"
                f"\n"
                f"Use build.py instead:\n"
                f"  python3 {script_dir}/build.py --path /path/to/repo --timeout 300\n"
                f"\n"
                f"This returns a small JSON summary. Logs go to a file, not your context.",
                file=sys.stderr,
            )
            print(json.dumps({
                "status": "blocked",
                "reason": "Use build.py instead of direct build commands",
                "command": command,
            }))
            sys.exit(1)

    # Safe command — execute it
    result = subprocess.run(command, shell=True)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
