---
name: common-git
description: >-
  Generic Git version control workflow and conventions. Use when: starting work
  on a ticket (branch creation), committing code, pushing changes, creating PRs,
  rebasing, keeping branches up-to-date, cleaning up merged branches, or
  recovering from git mistakes. Contains branching rules, commit hygiene,
  protected-branch safety, and rebase strategy. Project-agnostic — base branch
  and ticket prefix are parameterizable. For project-specific conventions
  (Jira prefix, commit format, GitHub App auth), load the matching project skill
  alongside this one.
---

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

📚 **References:**
- [git-quick-reference.md](references/git-quick-reference.md) — command lookup tables (rebase, stash, undo, cherry-pick, tags, blame/log search, reflog, bisect, aliases) + recovery anti-patterns
- [git-cross-platform.md](references/git-cross-platform.md) — CRLF/autocrlf, hooks on Windows/Unix, gitignore patterns, Windows path-length

> **Parameterization:** scripts read `BASE_BRANCH` (default `develop`) and `JIRA_PREFIX` (default `TICKET`) from the environment. Override in your shell or via CLI flags.

---

## 1. When Starting Work on a Ticket

### 🔴 BLOCKING — Sync Before Branching

**Why:** branching from a stale local base produces immediate merge conflicts and reviewers see noise unrelated to your change.

```bash
# 1. Switch to base branch (default: develop)
git checkout develop

# 2. Pull latest from remote
git pull origin develop

# 3. Create feature branch from up-to-date base
git checkout -b feature/TICKET-123-short-description

# 4. Verify branch point
git log --oneline -3
```

```bash
# ❌ WRONG — branch without syncing
git checkout -b feature/TICKET-123-my-feature   # from wherever you are

# ❌ WRONG — branch from stale base
git checkout develop
git checkout -b feature/TICKET-123-my-feature   # skipped pull

# ✅ CORRECT — always sync first
git checkout develop && git pull origin develop
git checkout -b feature/TICKET-123-my-feature
```

### 🔴 BLOCKING — Branch Naming Convention

**Why:** consistent prefixes let CI, review tooling, and `git_cleanup_branches.py` filter branches reliably; arbitrary names break automation.

**Pattern:** `<type>/<ticket>-<short-description-kebab>`

| Type | Usage | Example |
|---|---|---|
| `feature/` | New features | `feature/TICKET-123-add-checkout-flow` |
| `bugfix/` | Bug fixes | `bugfix/TICKET-789-fix-cart-total` |
| `hotfix/` | Production fixes | `hotfix/TICKET-202-payment-error` |
| `release/` | Release branches | `release/v1.2.0` |

### Main Branches

```
main (or master)        Production-ready ; protected ; tagged releases
develop                 Integration branch ; base for ALL feature branches
```

---

## 2. When Committing

### 🔴 BLOCKING — Stage Specific Files

**Why:** `git add .` silently includes secrets, debug files, IDE artifacts, and unrelated changes that pollute the diff and compromise security.

```bash
# ❌ WRONG — stages everything
git add .
git add -A

# ✅ CORRECT — stage explicitly
git add src/main/java/com/example/CheckoutService.java
git add src/test/java/com/example/CheckoutServiceTest.java
```

### 🔴 BLOCKING — Reference the Ticket in the Commit Message

**Why:** the link between code change and business context disappears after merge unless it lives in the commit message itself ; reviewers, blame, and changelog tools all rely on it.

**Generic format** (override in your project skill if you have a custom one):
```
[TICKET-123] Short imperative summary

Optional body explaining the WHY.

Co-Authored-By: <model> <noreply@anthropic.com>
```

### 🟡 WARNING — Commit Message Quality

- Imperative mood: *"Add"* not *"Added"*
- First line ≤ 72 characters
- Body explains the **why**, not the **what** (the diff already shows what)
- One logical change per commit

### 🔴 BLOCKING — Pre-Commit Checklist

**Why:** broken builds on `develop` block every other developer ; secrets in history are extremely costly to remove.

- [ ] Tests pass
- [ ] Build succeeds
- [ ] No secrets, tokens, or credentials in staged files
- [ ] No debug statements (`console.log`, `System.out.println`, `print()`, `debugger`)
- [ ] No commented-out code (use git history instead)
- [ ] Files staged explicitly (not `git add .`)
- [ ] Commit message references the ticket

---

## 3. When Pushing

### 🔴 BLOCKING — Never Push Directly to Protected Branches

**Why:** protected branches (`main`, `master`, `develop`, `release/*`) gate releases ; direct pushes bypass review, CI, and rollback safety.

```bash
# ❌ WRONG
git push origin develop
git push origin main

# ✅ CORRECT — push your feature branch, open a PR
git push -u origin feature/TICKET-123-add-checkout-flow
```

Use `scripts/git_safe_push.py` to enforce this automatically.

### 🟢 BEST PRACTICE — First Push vs. Subsequent

```bash
# First push (sets upstream tracking)
git push -u origin feature/TICKET-123-add-checkout-flow

# Subsequent pushes
git push
```

---

## 4. When Keeping Branch Up-to-Date

### 🟢 BEST PRACTICE — Rebase Your Feature on the Base Branch

```bash
git fetch origin develop
git rebase origin/develop

# On conflict: resolve files, then continue
git add <resolved-files>
git rebase --continue

# Force-push safely (your feature branch only)
git push --force-with-lease origin feature/TICKET-123-add-checkout-flow
```

### 🔴 BLOCKING — Never Rebase Public/Shared Branches

**Why:** rebasing rewrites history ; doing it on a shared branch breaks every other clone of the repo and can lose work.

```bash
# ❌ WRONG — rewrites shared history
git checkout develop
git rebase feature/my-feature

# ✅ CORRECT — merge into shared branches
git checkout develop
git merge feature/my-feature
```

📚 See [git-quick-reference.md](references/git-quick-reference.md) for interactive rebase, history rewriting, and recovery commands.

---

## 5. When Creating a PR

### 🔴 BLOCKING — Branch Must Be Up-to-Date Before PR

**Why:** an out-of-date branch hides conflicts from reviewers and from CI ; the merge that follows surprises everyone.

```bash
git fetch origin develop
git rebase origin/develop
# Resolve conflicts if any
git push --force-with-lease
```

### Generic PR Format

```
Title: [TICKET-123] Short description

Body:
## Summary
- What changed and why

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual verification done
```

Project-specific PR formatting (org-wide footers, GitHub App authorship, multi-ticket prefixes) belongs in the project skill, not here.

### 🟢 BEST PRACTICE — After PR Approval

```bash
# Squash merge (clean history)
gh pr merge <PR-number> --squash

# Cleanup
git branch -d feature/TICKET-123-add-checkout-flow
git push origin --delete feature/TICKET-123-add-checkout-flow   # if not auto-deleted
```

---

## 6. When Working Across Multiple Repos

### 🟢 BEST PRACTICE — Matching Branches

When a feature spans repos (backend + frontend), create matching branches:

```bash
cd backend  && git checkout develop && git pull && git checkout -b feature/TICKET-123-checkout
cd frontend && git checkout develop && git pull && git checkout -b feature/TICKET-123-checkout
```

- Same ticket reference in commits across all repos
- Cross-link PR URLs in descriptions
- Open PRs in **all** affected repos

---

## 7. When Cleaning Up

### 🟢 BEST PRACTICE — Remove Merged Branches

```bash
# Inspect first (dry run)
python3 scripts/git_cleanup_branches.py --repo $(pwd) --dry-run

# Delete merged branches
python3 scripts/git_cleanup_branches.py --repo $(pwd)
```

Override base branch with `--base-branch main` or `BASE_BRANCH=main`.

---

## 8. Git Safety Scripts

> All scripts return JSON on stdout. Parse with `json.loads()` or `jq`.
> Scripts live in `scripts/` next to this `SKILL.md`.

### Resolving the Scripts Directory

```bash
# Auto-detect (works on any environment)
GIT_SCRIPTS=$(find ~ -path "*/common-git/scripts/git_utils.py" -type f 2>/dev/null | head -1 | xargs dirname)
```

### Script Reference

| Script | Purpose | Key Checks |
|---|---|---|
| `git_utils.py` | Shared helpers (read as reference, not executed) | `run_git`, `is_protected_branch`, `validate_branch_name` |
| `git_status_report.py` | JSON status (single repo or workspace) | branch, divergence, uncommitted, stale, merged candidates |
| `git_safe_push.py` | Push with safety checks | protected branch block, divergence warning, first-push handling |
| `git_cleanup_branches.py` | Delete merged branches | `--dry-run`, `--auto`, `--base-branch` |

### Recommended Workflow

```bash
# Start of day
python3 $GIT_SCRIPTS/git_status_report.py --repo $(pwd)

# Before pushing
python3 $GIT_SCRIPTS/git_safe_push.py --repo $(pwd)

# Periodically
python3 $GIT_SCRIPTS/git_cleanup_branches.py --repo $(pwd) --dry-run
```

For ticket-prefixed branch creation and commit formatting (e.g., `[TICKET-123]` formats), use your project skill's wrappers.

---

## 9. Code Review Checklist (Git-specific)

### 🔴 BLOCKING

- [ ] Branch was created from up-to-date base (no stale base)
- [ ] No `git add .` or `git add -A` patterns visible in commit history
- [ ] No secrets, tokens, or credentials in any commit
- [ ] Branch is rebased on latest base before merge

### 🟡 WARNING

- [ ] Commits are focused (one logical change per commit)
- [ ] No debug statements left in committed code
- [ ] No commented-out code
- [ ] Commit messages reference a ticket

### 🟢 BEST PRACTICE

- [ ] Clean commit history (WIP commits squashed)
- [ ] PR description links related PRs (multi-repo features)
- [ ] Feature branch deleted after merge
