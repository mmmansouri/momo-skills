# Git on Windows / Unix / macOS

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Git is portable, but a handful of details bite the moment a repo is shared across operating systems.

## Contents

- [Line endings (CRLF vs LF)](#line-endings-crlf-vs-lf)
- [Case sensitivity](#case-sensitivity)
- [Executable bit on Windows](#executable-bit-on-windows)
- [Hooks across OSes](#hooks-across-oses)
- [Path length limits](#path-length-limits-windows)
- [Common .gitignore patterns](#common-gitignore-patterns)
- [Long-running scripts in git-bash vs PowerShell](#long-running-scripts-in-git-bash-vs-powershell)

---

## Line Endings (CRLF vs LF)

Windows tools default to `CRLF`, Unix tools to `LF`. Mixing them produces "phantom diffs" (whole-file changes when nothing visible changed) and breaks shell scripts checked in from Windows.

### 🔴 BLOCKING — Configure `core.autocrlf` per OS

**Why:** without this, every clone introduces or removes line-ending bytes, polluting every diff and silently breaking `#!/bin/bash` shebangs in shell scripts checked in from Windows.

```bash
# Windows: convert LF→CRLF on checkout, CRLF→LF on commit
git config --global core.autocrlf true

# Unix / macOS: leave LF alone, refuse CRLF on commit
git config --global core.autocrlf input
```

### 🟢 BEST PRACTICE — Pin via `.gitattributes`

A repo-level `.gitattributes` overrides per-user settings and removes ambiguity:

```gitattributes
# Auto-detect text files, normalize to LF in repo
* text=auto eol=lf

# Force LF on shell scripts (broken on Windows otherwise)
*.sh        text eol=lf
*.bash      text eol=lf

# Force CRLF on Windows-specific files
*.bat       text eol=crlf
*.cmd       text eol=crlf
*.ps1       text eol=crlf

# Treat as binary (no newline conversion, no diff)
*.png       binary
*.jpg       binary
*.pdf       binary
*.zip       binary
```

After committing `.gitattributes`, renormalize the repo once:

```bash
git add --renormalize .
git commit -m "Normalize line endings via .gitattributes"
```

---

## Case Sensitivity

| OS | Filesystem default |
|---|---|
| Linux | case-sensitive |
| macOS (APFS / HFS+) | case-insensitive (preserving) |
| Windows (NTFS) | case-insensitive (preserving) |

Result: `Foo.java` and `foo.java` collide on Windows/macOS but are distinct on Linux. CI on Linux fails with cryptic "file not found" while local builds work fine.

```bash
# Make git refuse to treat case-only renames as no-op
git config --global core.ignorecase false

# Rename properly (two steps to force git to track the change)
git mv Foo.java foo.tmp
git mv foo.tmp foo.java
git commit -m "Rename Foo.java → foo.java (case fix)"
```

---

## Executable Bit on Windows

NTFS doesn't carry the Unix executable bit. Without intervention, shell scripts checked in from Windows lose `+x` and fail in CI.

```bash
# Set the executable bit explicitly (works from Windows too)
git update-index --chmod=+x scripts/build.sh
git commit -m "Mark build.sh executable"

# Verify
git ls-files --stage scripts/build.sh
# 100755 abc1234... 0   scripts/build.sh    ← 100755 = executable
```

To prevent the bit from being silently flipped on Windows clones:

```bash
git config --global core.fileMode false
```

---

## Hooks Across OSes

Git hooks live in `.git/hooks/` and are shell scripts with a shebang.

### Bash hooks on Windows

Native PowerShell **cannot** run a `#!/bin/bash` script directly. Two options:

1. **Git for Windows** ships `bash.exe` (msys2). Hooks work out of the box if a `.sh` interpreter is on PATH and the file is committed with LF endings (see [Line Endings](#line-endings-crlf-vs-lf)).
2. **Use Python instead of bash** for portability. A `.git/hooks/pre-commit` with shebang `#!/usr/bin/env python3` runs identically on Windows, Linux, and macOS.

### 🔴 BLOCKING — Hooks must be executable

**Why:** git silently skips non-executable hooks on Unix; the developer thinks the hook ran when it didn't.

```bash
# After installing a hook
chmod +x .git/hooks/pre-commit
```

On Windows, `git update-index --chmod=+x` is the equivalent (the file is "executable" once committed).

### Sharing hooks across the team

`.git/hooks/` is **not** versioned. Use one of:

```bash
# 1. Committed hooks directory + git config
git config core.hooksPath .githooks

# 2. Husky (Node), pre-commit (Python), Lefthook — all wire .git/hooks/ to a versioned config
```

---

## Path Length Limits (Windows)

Default Windows API: 260 characters. Java/Node monorepos blow past this regularly.

```bash
# One-time fix (requires admin)
git config --system core.longpaths true

# Verify
git config --get core.longpaths
```

Also enable Windows itself:
- Group Policy → *Computer Configuration → Administrative Templates → System → Filesystem → Enable Win32 long paths*
- Or registry: `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`

---

## Common `.gitignore` Patterns

Per-language ignores. Combine with `git check-ignore -v <path>` to debug why a file is or isn't ignored.

### Java / Maven

```gitignore
target/
*.class
*.jar
*.war
.mvn/wrapper/maven-wrapper.jar
hs_err_pid*.log
```

### Java / Gradle

```gitignore
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar
```

### Node / TypeScript / Angular

```gitignore
node_modules/
dist/
build/
coverage/
.angular/
*.tsbuildinfo
.npm/
```

### Python

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

### IDE / OS

```gitignore
# IntelliJ / WebStorm / PyCharm
.idea/
*.iml

# VS Code (keep settings.json optional)
.vscode/*
!.vscode/settings.json
!.vscode/extensions.json

# macOS
.DS_Store

# Windows
Thumbs.db
desktop.ini

# Logs / env
*.log
.env
.env.local
```

### Secrets — always

```gitignore
# Never commit
*.pem
*.key
*.p12
*.pfx
.env
.env.*
!.env.example
secrets/
credentials.json
service-account*.json
```

---

## Long-Running Scripts in git-bash vs PowerShell

Some git operations (large clones, big rebases) print progress on stderr. Behavior differs:

- **PowerShell** : stderr appears in red. Many CI parsers misread red text as errors. Pipe with `2>&1` to merge streams.
- **git-bash** : behaves like Linux ; ANSI colors render if `git config --global color.ui auto`.
- **cmd.exe** : ANSI colors don't render natively before Windows 10 1909 — use `git -c color.ui=false`.

```powershell
# PowerShell — merge stderr so progress doesn't trigger CI's "found errors" heuristic
git fetch --all --tags 2>&1 | Out-String
```
