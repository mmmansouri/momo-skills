---
name: common-builder
description: >-
  Build wrapper scripts (Python) for Maven and NPM. Captures logs to file, returns JSON summary.
  Cross-platform (Windows + Linux). Not auto-loaded by agents — build rules are in common-developer Section 7.
---

# Common Builder Scripts

Python scripts in `scripts/` directory. Referenced by `common-developer` skill Section 7.

**Prerequisite:** Python 3 must be installed.

## Scripts

| Script | Purpose |
|--------|---------|
| `build.py` | Entry point. Auto-detects Maven/NPM, runs build with timeout, returns JSON |
| `check_prereqs.py` | Verify python3, mvn, node, npm installed |
| `cleanup.py` | Delete log file after successful push |
| `safe_exec.py` | Block dangerous build commands (mvn/npm/ng/npx direct) |

## Usage

```bash
# Full build (default — install + build + test)
python3 build.py --path <dir> [--type maven|npm] [--timeout 600]

# Phase control — run only specific phases
python3 build.py --path <dir> --phases build              # compile-only
python3 build.py --path <dir> --phases test               # test-only
python3 build.py --path <dir> --phases build,test          # compile + test (skip install)

# Targeted tests
python3 build.py --path <dir> --phases test --test-include "src/app/pages/checkout/**"   # Angular
python3 build.py --path <dir> --phases test --test-class "OrderServiceTest"              # Maven

# Force reinstall (skip smart install check)
python3 build.py --path <dir> --force-install

# Cleanup
python3 cleanup.py <logFile>
python3 check_prereqs.py
```

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--path` | required | Project directory |
| `--type` | auto-detect | `maven` or `npm` |
| `--timeout` | 600 | Timeout in seconds |
| `--phases` | `install,build,test` | Comma-separated: `install`, `build`, `test`. `verify` = all. |
| `--test-include` | none | NPM only: glob for `ng test --include` |
| `--test-class` | none | Maven only: class name for `-Dtest=` |
| `--force-install` | off | Force `npm ci` even if `node_modules` is fresh |
| `--offline` | off | Maven only: skip remote repo checks (`-o` flag) |

### Maven Daemon (mvnd) Auto-Detection

If `mvnd` is on PATH, `build.py` uses it automatically instead of `mvn`. Maven Daemon keeps the JVM warm between builds for ~40-60% faster repeated builds. No flag needed — falls back to `mvn` if `mvnd` is not installed.

### Smart Install (NPM)

By default, `npm ci` is skipped when `node_modules/.package-lock.json` is newer than `package-lock.json`. Use `--force-install` to override.

## JSON Output Format

```json
{
  "status": "success|failure|error",
  "type": "maven|npm",
  "exitCode": 0,
  "phases": {
    "requested": ["install", "build", "test"],
    "executed": ["build", "test"],
    "skipped": ["install"],
    "timing": { "install": "skipped (fresh node_modules)", "build": "34s", "test": "18s" }
  },
  "tests": { "run": 142, "passed": 142, "failed": 0 },
  "duration": "52s",
  "logFile": "C:/Users/.../AppData/Local/Temp/build-npm-1738759440.log"
}
```
