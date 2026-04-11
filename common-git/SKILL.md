---
name: common-git
description: >-
  Git version control workflow and conventions. Use when: starting work on a
  ticket (branch creation), committing code, pushing changes, creating PRs,
  keeping branches up-to-date, or handling multi-project changes. Contains
  mandatory branching rules, commit format, and Buy Nature-specific conventions.
  Required for all development agents.
---

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

📚 **References:** [git-advanced.md](references/git-advanced.md) for rebase, stash, undo, cherry-pick, tags

---

## 1. When Starting Work on a Ticket

### 🔴 BLOCKING - Sync Before Branching

**ALWAYS** sync with remote `develop` before creating a feature branch. Never branch from a stale local `develop`.

```bash
# 1. Switch to develop
git checkout develop

# 2. Pull latest changes from remote
git pull origin develop

# 3. Create feature branch from up-to-date develop
git checkout -b feature/BNAT-XXX-short-description

# 4. Verify branch point (should show latest develop commits)
git log --oneline -3
```

```bash
# ❌ WRONG: Branch without syncing
git checkout -b feature/BNAT-123-my-feature  # from wherever you are

# ❌ WRONG: Branch from stale develop
git checkout develop
# (skip git pull)
git checkout -b feature/BNAT-123-my-feature

# ✅ CORRECT: Always sync first
git checkout develop
git pull origin develop
git checkout -b feature/BNAT-123-my-feature
```

### 🔴 BLOCKING - Branch Naming

**Pattern:** `<type>/<ticket>-<short-description>`

| Type | Usage | Example |
|------|-------|---------|
| `feature/` | New features | `feature/BNAT-123-add-checkout-flow` |
| `bugfix/` | Bug fixes | `bugfix/BNAT-789-fix-cart-total` |
| `hotfix/` | Production fixes | `hotfix/BNAT-202-critical-payment-error` |
| `release/` | Release branches | `release/v1.2.0` |

### Main Branches

```
main (or master)
  ├── Production-ready code
  ├── Protected branch (no direct commits)
  └── Tagged releases (v1.0.0, v1.1.0)

develop
  ├── Integration branch
  ├── Latest features merged here
  └── Base for ALL feature branches
```

---

## 2. When Committing

### 🔴 BLOCKING - Buy Nature Commit Format

```
[BNAT-{Epic}][BNAT-{US1}][BNAT-{US2}]... Commit message

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Examples:**
```bash
git commit -m "[BNAT-100][BNAT-123] Add checkout service and controller

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

git commit -m "[BNAT-100][BNAT-124][BNAT-125] Implement order confirmation and email notifications

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 🔴 BLOCKING - Stage Specific Files

Never use `git add .` or `git add -A`. Always stage specific files.

```bash
# ❌ WRONG: Stages everything (risks secrets, debug files, unrelated changes)
git add .
git add -A

# ✅ CORRECT: Stage specific files
git add src/main/java/com/buynature/checkout/CheckoutService.java
git add src/test/java/com/buynature/checkout/CheckoutServiceTest.java
```

### 🟡 WARNING - Commit Message Quality

- Summarize the WHY, not the WHAT
- Keep first line under 72 characters
- Use imperative mood: "Add feature" not "Added feature"
- Body (optional) for complex changes

### 🔴 BLOCKING - Pre-Commit Checklist

Before every commit, verify:

- [ ] All tests pass (`mvn test` / `npm test`)
- [ ] Build succeeds (`mvn clean verify` / `npm run build`)
- [ ] No secrets or credentials in staged files
- [ ] No debug statements (`console.log`, `System.out.println`)
- [ ] No commented-out code (use git history instead)
- [ ] Changes are staged file-by-file (not `git add .`)
- [ ] Commit message includes Jira ticket references

---

## 3. When Pushing

### 🔴 BLOCKING - Build Must Pass Before Push

Build validation is mandatory. Use the `common-builder` skill's `build.py` script.

```bash
# First push (sets upstream tracking)
git push -u origin feature/BNAT-123-add-checkout-flow

# Subsequent pushes
git push
```

### 🟡 WARNING - Never Push to Protected Branches

```bash
# ❌ WRONG: Push directly to develop or main
git push origin develop
git push origin main

# ✅ CORRECT: Push to feature branch, then create PR
git push -u origin feature/BNAT-123-add-checkout-flow
```

---

## 4. When Keeping Branch Up-to-Date

### 🟢 BEST PRACTICE - Rebase on Develop

Regularly sync your feature branch with `develop` to avoid large merge conflicts.

```bash
# Fetch latest develop
git fetch origin develop

# Rebase your branch on top of develop
git rebase origin/develop

# If conflicts: resolve, then continue
git add <resolved-files>
git rebase --continue

# Force push safely after rebase (only on YOUR feature branch)
git push --force-with-lease origin feature/BNAT-123-add-checkout-flow
```

### 🔴 BLOCKING - Never Rebase Public Branches

```bash
# ❌ WRONG: Rebasing develop or main (rewrites shared history)
git checkout develop
git rebase feature/my-feature

# ✅ CORRECT: Merge into public branches
git checkout develop
git merge feature/my-feature
```

📚 **References:** [git-advanced.md](references/git-advanced.md) for interactive rebase and history cleanup

---

## 5. When Creating a PR

### 🔴 BLOCKING - Branch Must Be Up-to-Date

Before creating a PR, ensure your branch includes the latest `develop` changes:

```bash
git fetch origin develop
git rebase origin/develop
# Resolve conflicts if any
git push --force-with-lease
```

### 🔴 BLOCKING - PR Format

For agents: Always use the GitHub App token wrapper to create PRs as `rahman-momo-bot[bot]`:

```bash
# Resolve scripts directory (auto-detect, works in any environment)
GIT_SCRIPTS=$(find ~ -path "*/common-git/scripts/git_utils.py" -type f 2>/dev/null | head -1 | xargs dirname)

# Create PR using GitHub App token
python3 $GIT_SCRIPTS/gh_with_app_token.py pr create \
  --title "[BNAT-{Epic}][BNAT-{US}] Short description" \
  --body "$(cat <<'EOF'
## Summary
- What changed and why

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual verification done

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" \
  --base develop \
  --head feature/BNAT-123-add-checkout-flow
```

**Alternative**: Export GH_TOKEN directly (for scripts/automation):
```bash
export GH_TOKEN=$(python3 ~/path/to/github_token.py)
gh pr create --title "..." --body "..." --base develop --head feature/...
```

**For agents**: The skill auto-resolves paths. Just use `python3 gh_with_app_token.py` directly, or import `github_auth.get_token()` for programmatic access.

### 🟢 BEST PRACTICE - After PR Approval

```bash
# Squash merge (recommended for clean history)
gh pr merge <PR-number> --squash

# Delete local branch
git branch -d feature/BNAT-123-add-checkout-flow

# Delete remote branch (if not auto-deleted)
git push origin --delete feature/BNAT-123-add-checkout-flow
```

---

## 6. Multi-Project Changes

### 🟢 BEST PRACTICE - Matching Branches Across Repos

When a feature spans multiple projects (backend + frontend), create matching branches:

```bash
# Backend
cd buy-nature-back
git checkout develop && git pull origin develop
git checkout -b feature/BNAT-123-add-checkout

# Frontend
cd ../buy-nature-front
git checkout develop && git pull origin develop
git checkout -b feature/BNAT-123-add-checkout
```

- Use the **same Jira references** in commits across all repos
- **Link PRs** in their descriptions (mention the related PR URL)
- Create PRs in **all affected repos**

---

## 7. Quick Reference Checklists

### Before Commit

- [ ] Tests pass
- [ ] Build succeeds
- [ ] Specific files staged (no `git add .`)
- [ ] Commit message has Jira ticket `[BNAT-XXX]`
- [ ] Co-Authored-By footer included
- [ ] No secrets, no debug code

### Before PR

- [ ] Branch rebased on latest `develop`
- [ ] All commits have meaningful messages
- [ ] PR title follows format `[BNAT-{Epic}][BNAT-{US}] Description`
- [ ] PR description explains changes + test plan
- [ ] Build passes on feature branch

### Before Starting Work

- [ ] `git checkout develop`
- [ ] `git pull origin develop`
- [ ] `git checkout -b feature/BNAT-XXX-description`
- [ ] Verify with `git log --oneline -3` (latest develop commits visible)

---

## 8. Git Safety Scripts

> The `common-git` skill includes wrapper scripts that enforce safety checks
> and return JSON output (following the `common-builder` pattern).
> Agents **MUST** use these scripts instead of raw git commands for critical operations.

### Resolving Script Paths

All scripts are in the `scripts/` subdirectory relative to this SKILL.md file.

**To find the scripts, run:**
```bash
# Auto-detect: works on both OpenClaw VPS and Claude Code local
GIT_SCRIPTS=$(find ~ -path "*/common-git/scripts/git_utils.py" -type f 2>/dev/null | head -1 | xargs dirname)
echo "Scripts directory: $GIT_SCRIPTS"
```

### 🔴 BLOCKING - Recommended Agent Workflow

#### Starting work on a ticket:
```bash
# 1. Assess current state
python3 $GIT_SCRIPTS/git_status_report.py --repo $(pwd)

# 2. Clean up merged branches (optional)
python3 $GIT_SCRIPTS/git_cleanup_branches.py --auto --repo $(pwd)

# 3. Create branch safely (syncs develop automatically)
python3 $GIT_SCRIPTS/git_safe_branch.py --ticket BNAT-XXX --description short-desc
```

#### During development:
```bash
# Stage files individually (NEVER git add .)
git add path/to/specific/file.java

# Commit with validation
python3 $GIT_SCRIPTS/git_safe_commit.py \
  --epic BNAT-100 \
  --tickets BNAT-123 \
  --message "Add checkout service and controller"
```

#### Before pushing:
```bash
# 1. Validate build (common-builder -- separate skill)
python3 $BUILDER/build.py --path $(pwd)

# 2. Push with safety checks
python3 $GIT_SCRIPTS/git_safe_push.py
```

### Script Reference

| Script | Purpose | Key Checks |
|--------|---------|------------|
| `git_utils.py` | Shared helpers | `run_git()`, `is_protected_branch()`, `validate_branch_name()` |
| `git_status_report.py` | Situational awareness | Branch, divergence, uncommitted, stale |
| `git_safe_branch.py` | Safe branch creation | Syncs develop, validates naming |
| `git_safe_commit.py` | Safe commit | Jira refs, debug code, secrets |
| `git_safe_push.py` | Safe push | Protected branches, divergence |
| `git_cleanup_branches.py` | Remove merged branches | `--dry-run`, `--auto` modes |
| `git_install_hooks.py` | Install git hooks | Pre-commit checks across repos |

All scripts return JSON on stdout. Parse with Python `json` module.

### Installing Hooks (One-Time Setup)

```bash
python3 $GIT_SCRIPTS/git_install_hooks.py --all-repos ~/repos
```

Installs a lightweight `pre-commit` hook in all repos that checks for:
- Direct commits to `develop`/`main` (blocked)
- Debug statements in staged code (warning)
- Secret patterns in staged code (blocked)
- Large files > 500KB (warning)

### Automation Note

For periodic cleanup on the VPS, `python3 git_cleanup_branches.py --auto --all-repos ~/repos`
can be added to a crontab. This is an infrastructure setup concern outside the scope
of this skill.

---

## 9. GitHub App Authentication Setup

### Environment Detection

GitHub authentication scripts automatically detect the assistant environment:

| Environment | PEM File Location | Scripts Location |
|-------------|-------------------|------------------|
| OpenClaw VPS | `~/.openclaw/secrets/github-app.pem` | Auto-detected via `find ~` |
| Claude Code | `~/.claude/secrets/github-app.pem` | Auto-detected via `find ~` |

### Setup for Claude Code (One-Time)

1. **Run setup script**:
   ```bash
   cd buy-nature-ai/skills/common-git/scripts
   python3 github_setup.py
   ```

2. **Copy PEM file** when prompted:
   - From OpenClaw: `~/.openclaw/secrets/github-app.pem`
   - To Claude Code: `~/.claude/secrets/github-app.pem`

3. **Configure git credential helper** (when prompted by setup script)

4. **Verify token generation**:
   ```bash
   python3 github_token.py
   # Should output: ghs_... (installation token)
   ```

### How It Works

1. **Token Generation**:
   - `github_auth.py` shared module: generates JWT + exchanges for installation access token
   - `github_token.py` CLI wrapper: prints just the token string
   - `git_credential_buynature.py` provides fresh tokens to git on each auth request

2. **Agent Usage**:
   - **Git operations**: `git push`, `git pull` → credential helper generates fresh token automatically
   - **gh CLI commands**: Use `python3 gh_with_app_token.py` wrapper for any `gh` command
     - Example: `python3 gh_with_app_token.py pr create ...` (creates PR as `rahman-momo-bot[bot]`)
     - Or: `export GH_TOKEN=$(python3 github_token.py) && gh pr create ...`
   - **Code reviewer agents**: Use MCP GitHub tools (automatically use GitHub App token)
   - All PRs/comments created as `rahman-momo-bot[bot]`

3. **Available Wrappers**:
   - `gh_with_app_token.py`: Wraps `gh` commands with automatic GitHub App token injection
   - `git_credential_buynature.py`: Provides tokens to git automatically (credential helper)

4. **Token Lifecycle**:
   - Tokens expire after 1 hour
   - Automatically regenerated on next auth request
   - No manual token management needed

### Troubleshooting

**Problem**: `gh pr create` uses personal account instead of GitHub App

**Solution**:
```bash
# Check current gh auth
gh auth status

# If using personal token, set GH_TOKEN env var
export GH_TOKEN=$(python3 github_token.py)
gh pr create ...

# OR configure credential helper globally (recommended)
git config --global credential.helper '!python3 /path/to/git_credential_buynature.py'
```

**Problem**: "No GitHub App PEM file found"

**Solution**: Run `python3 github_setup.py` in `buy-nature-ai/skills/common-git/scripts/`

**Problem**: "Token generation failed"

**Solution**:
1. Verify PEM file exists and is readable
2. Check PEM file format (should start with `-----BEGIN RSA PRIVATE KEY-----`)
3. Verify GitHub App ID and Installation ID are correct in scripts

---

## 10. Code Review Checklist (Git-specific)

### 🔴 BLOCKING

- [ ] Branch was created from up-to-date `develop` (no stale base)
- [ ] Commit messages follow `[BNAT-{Epic}][BNAT-{US}]` format
- [ ] No `git add .` or `git add -A` in commit history
- [ ] No secrets or credentials in any commit
- [ ] Branch is rebased on latest `develop` before merge

### 🟡 WARNING

- [ ] Commits are focused (one logical change per commit)
- [ ] No debug statements left in committed code
- [ ] No commented-out code (use git history)

### 🟢 BEST PRACTICE

- [ ] Clean commit history (squashed WIP commits)
- [ ] PR description links related PRs (multi-project)
- [ ] Feature branch deleted after merge
