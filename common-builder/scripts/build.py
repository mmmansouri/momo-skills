#!/usr/bin/env python3
"""Build wrapper for Maven and NPM projects.

Captures all build output to a log file and returns a small JSON summary.
Cross-platform: works on Windows, Linux, and macOS.

Usage:
    python3 build.py --path /project/path [--type maven|npm] [--timeout 600]
                     [--phases install,build,test] [--test-include pattern]
                     [--test-class ClassName] [--force-install] [--offline]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ALL_PHASES = ["install", "build", "test"]


def error_json(message):
    """Print error JSON and exit."""
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def detect_type(path):
    """Auto-detect project type from build files."""
    if os.path.exists(os.path.join(path, "pom.xml")):
        return "maven"
    if os.path.exists(os.path.join(path, "package.json")):
        return "npm"
    return None


def parse_phases(phases_str):
    """Parse --phases argument into a list of phases.

    Returns list of phases in execution order.
    Default (None) returns all phases.
    'verify' is an alias for all phases.
    """
    if phases_str is None or phases_str == "verify":
        return list(ALL_PHASES)
    phases = [p.strip() for p in phases_str.split(",")]
    valid = set(ALL_PHASES) | {"verify"}
    for p in phases:
        if p not in valid:
            error_json(f"Invalid phase: {p}. Valid: {', '.join(sorted(valid))}")
    return phases


def is_install_fresh(path):
    """Check if node_modules is current with package-lock.json.

    Compares mtime of node_modules/.package-lock.json (written by npm ci)
    against package-lock.json. If the installed manifest is newer or equal,
    dependencies are fresh and install can be skipped.
    """
    lock_file = os.path.join(path, "package-lock.json")
    modules_lock = os.path.join(path, "node_modules", ".package-lock.json")
    if not os.path.exists(modules_lock) or not os.path.exists(lock_file):
        return False
    return os.path.getmtime(modules_lock) >= os.path.getmtime(lock_file)


def detect_maven_cmd():
    """Detect whether to use mvnd (Maven Daemon) or mvn.

    Returns 'mvnd' if Maven Daemon is on PATH, otherwise 'mvn'.
    mvnd keeps the JVM warm between builds for ~40-60% faster repeated builds.
    """
    if shutil.which("mvnd"):
        return "mvnd"
    return "mvn"


def parse_maven_tests(log_content):
    """Parse Maven surefire test summary: 'Tests run: X, Failures: Y, Errors: Z, Skipped: W'."""
    tests = {"run": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    matches = re.findall(
        r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)",
        log_content,
    )
    if matches:
        last = matches[-1]
        tests["run"] = int(last[0])
        tests["failed"] = int(last[1])
        tests["errors"] = int(last[2])
        tests["skipped"] = int(last[3])
        tests["passed"] = max(0, tests["run"] - tests["failed"] - tests["errors"])
    return tests


def parse_npm_tests(log_content):
    """Parse Jest or Jasmine/Karma test output."""
    tests = {"run": 0, "passed": 0, "failed": 0}

    # Jest format: "Tests:  X passed, Y total" or "Tests:  X failed, Y passed, Z total"
    jest_match = re.search(r"Tests:\s+.*?(\d+)\s+total", log_content)
    if jest_match:
        tests["run"] = int(jest_match.group(1))
        passed_match = re.search(r"(\d+)\s+passed", log_content)
        failed_match = re.search(r"(\d+)\s+failed", log_content)
        tests["passed"] = int(passed_match.group(1)) if passed_match else 0
        tests["failed"] = int(failed_match.group(1)) if failed_match else 0
        return tests

    # Jasmine/Karma format: "X specs, Y failures"
    karma_match = re.search(r"(\d+)\s+specs?", log_content)
    if karma_match:
        tests["run"] = int(karma_match.group(1))
        failure_match = re.search(r"(\d+)\s+failures?", log_content)
        tests["failed"] = int(failure_match.group(1)) if failure_match else 0
        tests["passed"] = tests["run"] - tests["failed"]
        return tests

    return tests


def build_npm_commands(phases, path, force_install, test_include=None):
    """Build list of (phase_name, command_or_None) for NPM project.

    Returns list of tuples: (phase_name, cmd_list_or_None, skip_reason_or_None)
    """
    commands = []

    for phase in ALL_PHASES:
        if phase not in phases:
            continue

        if phase == "install":
            if not force_install and is_install_fresh(path):
                commands.append(("install", None, "fresh node_modules"))
            else:
                commands.append(("install", ["npm", "ci", "--legacy-peer-deps"], None))

        elif phase == "build":
            commands.append(("build", ["npx", "ng", "build"], None))

        elif phase == "test":
            cmd = ["npx", "ng", "test", "--no-watch", "--browsers=ChromeHeadless"]
            if test_include:
                cmd.extend(["--include", test_include])
            commands.append(("test", cmd, None))

    return commands


def build_maven_commands(phases, test_class=None, offline=False):
    """Build list of (phase_name, command_or_None) for Maven project.

    Maven lifecycle doesn't map 1:1 to our phases, so we approximate:
    - build (compile-only): mvn compile -B
    - test: mvn test -B [-Dtest=ClassName]
    - all (install+build+test): mvn clean verify -B (current behavior)

    Auto-detects mvnd (Maven Daemon) for faster builds.
    """
    commands = []
    mvn = detect_maven_cmd()
    has_install = "install" in phases
    has_build = "build" in phases
    has_test = "test" in phases

    def _append_flags(cmd):
        if offline:
            cmd.append("-o")
        return cmd

    # Full lifecycle (default)
    if has_install and has_build and has_test:
        cmd = [mvn, "clean", "verify", "-B"]
        if test_class:
            cmd.append(f"-Dtest={test_class}")
        commands.append(("verify", _append_flags(cmd), None))
        return commands

    # Build + test (no clean)
    if has_build and has_test:
        cmd = [mvn, "verify", "-B"]
        if test_class:
            cmd.append(f"-Dtest={test_class}")
        commands.append(("verify", _append_flags(cmd), None))
        return commands

    # Individual phases
    if has_build and not has_test:
        commands.append(("build", _append_flags([mvn, "compile", "-B"]), None))

    if has_test and not has_build:
        cmd = [mvn, "test", "-B"]
        if test_class:
            cmd.append(f"-Dtest={test_class}")
        commands.append(("test", _append_flags(cmd), None))

    return commands


def wrap_command_for_platform(cmd):
    """Wrap command for current platform.

    On Windows, npm/npx/mvn need cmd /c prefix for subprocess.run to find them.
    """
    if os.name == "nt" and cmd and cmd[0] in ("npm", "npx", "mvn", "mvnd"):
        return ["cmd", "/c"] + cmd
    return cmd


def run_build(path, build_type, timeout_secs, phases, force_install,
              test_include=None, test_class=None, offline=False):
    """Run the build phases and return a JSON-serializable result dict."""
    log_file = os.path.join(
        tempfile.gettempdir(), f"build-{build_type}-{int(time.time())}.log"
    )
    start_time = time.time()

    # Build command list
    if build_type == "npm":
        commands = build_npm_commands(phases, path, force_install, test_include)
    else:
        commands = build_maven_commands(phases, test_class, offline)

    if not commands:
        error_json("No phases to execute. Check --phases argument.")

    phase_timing = {}
    executed_phases = []
    skipped_phases = []
    exit_code = 0
    timed_out = False

    remaining_timeout = timeout_secs

    with open(log_file, "w", encoding="utf-8") as log:
        for phase_name, cmd, skip_reason in commands:
            if skip_reason:
                phase_timing[phase_name] = f"skipped ({skip_reason})"
                skipped_phases.append(phase_name)
                log.write(f"\n=== Phase: {phase_name} — SKIPPED ({skip_reason}) ===\n")
                continue

            phase_start = time.time()
            log.write(f"\n=== Phase: {phase_name} ===\n")
            log.write(f"Command: {' '.join(cmd)}\n\n")
            log.flush()

            platform_cmd = wrap_command_for_platform(cmd)

            try:
                result = subprocess.run(
                    platform_cmd,
                    cwd=path,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=remaining_timeout,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                exit_code = 124
                timed_out = True
            except FileNotFoundError as e:
                log.write(f"\nERROR: Command not found: {e.filename}\n")
                exit_code = 127

            phase_duration = int(time.time() - phase_start)
            phase_timing[phase_name] = f"{phase_duration}s"
            executed_phases.append(phase_name)

            # Update remaining timeout
            remaining_timeout = max(1, timeout_secs - int(time.time() - start_time))

            if timed_out:
                log.write(f"\n=== TIMEOUT after {phase_duration}s ===\n")
                break

            if exit_code != 0:
                log.write(f"\n=== Phase {phase_name} FAILED (exit code {exit_code}) ===\n")
                break

    duration = int(time.time() - start_time)

    if timed_out:
        return {
            "status": "error",
            "type": build_type,
            "exitCode": 124,
            "message": f"Build timed out during '{executed_phases[-1]}' phase",
            "timeout": timeout_secs,
            "phases": {
                "requested": phases,
                "executed": executed_phases,
                "skipped": skipped_phases,
                "timing": phase_timing,
            },
            "tests": {"run": 0, "passed": 0, "failed": 0},
            "duration": f"{duration}s",
            "logFile": log_file,
        }

    # Read log to parse test results
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
    except OSError:
        log_content = ""

    if "test" in phases and "test" in executed_phases:
        if build_type == "maven":
            tests = parse_maven_tests(log_content)
        else:
            tests = parse_npm_tests(log_content)
    else:
        tests = {"run": 0, "passed": 0, "failed": 0}

    status = "success" if exit_code == 0 else "failure"

    return {
        "status": status,
        "type": build_type,
        "exitCode": exit_code,
        "phases": {
            "requested": phases,
            "executed": executed_phases,
            "skipped": skipped_phases,
            "timing": phase_timing,
        },
        "tests": tests,
        "duration": f"{duration}s",
        "logFile": log_file,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build wrapper — captures logs to file, returns JSON summary."
    )
    parser.add_argument("--path", required=True, help="Project directory path")
    parser.add_argument(
        "--type", choices=["maven", "npm"], help="Build type (auto-detected if omitted)"
    )
    parser.add_argument(
        "--timeout", type=int, default=600, help="Timeout in seconds (default: 600)"
    )
    parser.add_argument(
        "--phases", type=str, default=None,
        help="Comma-separated phases: install,build,test (default: all). 'verify' = all."
    )
    parser.add_argument(
        "--test-include", type=str, default=None,
        help="NPM only: glob pattern for ng test --include (e.g. 'src/app/pages/checkout/**')"
    )
    parser.add_argument(
        "--test-class", type=str, default=None,
        help="Maven only: test class name for -Dtest= (e.g. 'OrderServiceTest')"
    )
    parser.add_argument(
        "--force-install", action="store_true",
        help="Force npm ci even if node_modules appears fresh"
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Maven only: skip remote repo checks (-o flag)"
    )
    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        error_json(f"Directory not found: {args.path}")

    # Detect type
    build_type = args.type or detect_type(args.path)
    if not build_type:
        error_json("Cannot detect project type. Use --type maven|npm")

    # Parse phases
    phases = parse_phases(args.phases)

    # Validate flag combinations
    if args.test_include and build_type != "npm":
        error_json("--test-include is only supported for NPM projects")
    if args.test_class and build_type != "maven":
        error_json("--test-class is only supported for Maven projects")
    if args.test_include and "test" not in phases:
        error_json("--test-include requires 'test' in --phases")
    if args.test_class and "test" not in phases:
        error_json("--test-class requires 'test' in --phases")
    if args.offline and build_type != "maven":
        error_json("--offline is only supported for Maven projects")

    result = run_build(
        args.path, build_type, args.timeout, phases, args.force_install,
        args.test_include, args.test_class, args.offline,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
