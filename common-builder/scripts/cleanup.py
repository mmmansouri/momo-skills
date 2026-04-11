#!/usr/bin/env python3
"""Cleanup build log files after successful build.

Usage:
    python3 cleanup.py <logFile>
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"cleaned": False, "error": "No log file specified"}))
        sys.exit(1)

    log_file = sys.argv[1]

    if not os.path.isfile(log_file):
        print(json.dumps({"cleaned": False, "error": f"File not found: {log_file}"}))
        sys.exit(1)

    try:
        os.remove(log_file)
    except OSError as e:
        print(json.dumps({"cleaned": False, "error": f"Failed to delete: {e}"}))
        sys.exit(1)

    print(json.dumps({"cleaned": True, "file": log_file}))


if __name__ == "__main__":
    main()
