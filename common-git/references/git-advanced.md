# Git Advanced Topics

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## Interactive Rebase

### 🟢 BEST PRACTICE - Clean Up Commits Before PR

```bash
# Squash last 3 commits into 1
git rebase -i HEAD~3

# Editor opens:
pick abc1234 WIP: start checkout
pick def5678 Fix typo
pick ghi9012 Add tests

# Change to:
pick abc1234 WIP: start checkout
squash def5678 Fix typo
squash ghi9012 Add tests

# Result: 3 commits become 1 with a combined message
```

### Reword Commit Messages

```bash
git rebase -i HEAD~2

# Change pick to reword:
reword abc1234 bad commit message
reword def5678 another bad one

# Editor will open for each to rewrite messages
```

---

## Stash Changes

### 🟢 BEST PRACTICE - Save Work in Progress

```bash
# Save current work
git stash
# OR with a descriptive message
git stash save "WIP: checkout form validation"

# List stashes
git stash list
# stash@{0}: WIP: checkout form validation
# stash@{1}: On feature/ABC: cart updates

# Apply latest stash (keep in stash list)
git stash apply

# Apply and remove from stash list
git stash pop

# Apply specific stash
git stash apply stash@{1}

# Drop specific stash
git stash drop stash@{0}

# Clear all stashes
git stash clear
```

### Common Use Case: Switch Branches with Uncommitted Work

```bash
# Save current work
git stash save "WIP: checkout validation"

# Switch to another feature
git checkout feature/BNAT-124-product-search
# ... work on it ...

# Go back to original feature
git checkout feature/BNAT-123-checkout
git stash pop
```

---

## Undo Changes

### Unstage Files

```bash
# Unstage specific file (keeps changes in working dir)
git restore --staged src/main/java/Order.java

# Unstage all files
git restore --staged .
```

### 🟡 WARNING - Discard Local Changes

```bash
# ⚠️ This permanently deletes uncommitted changes

# Discard changes in specific file
git restore src/main/java/Order.java

# Discard ALL local changes
git restore .
```

### Undo Last Commit

```bash
# Undo commit, keep changes STAGED (safest)
git reset --soft HEAD~1

# Undo commit, keep changes UNSTAGED
git reset HEAD~1

# ⚠️ Undo commit AND discard changes (DANGEROUS - data loss)
git reset --hard HEAD~1
```

### 🟢 BEST PRACTICE - Revert (Safe Undo for Pushed Commits)

```bash
# Create a new commit that undoes a previous commit
git revert abc1234

# Revert multiple commits without auto-committing
git revert --no-commit abc1234
git revert --no-commit def5678
git commit -m "[BNAT-XXX] Revert changes from BNAT-123"
```

---

## Cherry-Pick

### 🟢 BEST PRACTICE - Apply Specific Commits from Another Branch

```bash
# Apply a single commit
git cherry-pick abc1234

# Apply multiple commits
git cherry-pick abc1234 def5678 ghi9012

# Cherry-pick without auto-committing (to review first)
git cherry-pick --no-commit abc1234
```

---

## Tags (Releases)

```bash
# List tags
git tag

# Create annotated tag (recommended)
git tag -a v1.0.0 -m "Release version 1.0.0"

# Tag a specific commit
git tag -a v1.0.1 abc1234 -m "Hotfix release"

# Push tag to remote
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0
```

---

## Common Scenarios

### Fix Mistake in Last Commit

```bash
# Edit files to fix the mistake
git add fixed-file.java

# Amend last commit (keeps same message)
git commit --amend --no-edit

# Force push safely (only on feature branch!)
git push --force-with-lease
```

### Split Large Commit into Smaller Ones

```bash
# Undo last commit, keep changes unstaged
git reset HEAD~1

# Stage and commit separately
git add CheckoutService.java
git commit -m "[BNAT-123] Add checkout service"

git add CheckoutController.java
git commit -m "[BNAT-123] Add checkout controller"

git add CheckoutServiceTest.java
git commit -m "[BNAT-123] Add checkout tests"
```

### Find Which Commit Introduced a Bug

```bash
# Start bisect
git bisect start
git bisect bad          # Current commit is broken
git bisect good v1.0.0  # Last known good version

# Git checks out middle commit - test it, then:
git bisect good  # if this commit is OK
git bisect bad   # if this commit has the bug

# Repeat until Git identifies the first bad commit
# When done:
git bisect reset
```

---

## Git Aliases (Time Savers)

```bash
# Add to ~/.gitconfig
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = restore --staged
    last = log -1 HEAD
    lg = log --oneline --graph --decorate --all
    amend = commit --amend --no-edit
    undo = reset HEAD~1
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"
```
