# Git Quick Reference

> Tables only — for commands whose exact syntax you forget. Not a tutorial.
> Examples use `TICKET-XXX` as the generic ticket prefix.

## Contents

- [Branch ops](#branch-ops)
- [History rewriting (rebase, amend, squash)](#history-rewriting)
- [Stash](#stash)
- [Undo, reset, revert](#undo-reset-revert)
- [Cherry-pick & tags](#cherry-pick--tags)
- [Inspection](#inspection)
- [Recovery (reflog, bisect)](#recovery)
- [🔴 BLOCKING — recovery anti-patterns](#blocking--recovery-anti-patterns)
- [Useful aliases](#useful-aliases)

---

## Branch ops

| Goal | Command |
|---|---|
| Create from up-to-date base | `git checkout develop && git pull && git checkout -b feature/TICKET-123-x` |
| Rename current branch | `git branch -m new-name` |
| Delete local (safe — refuses if unmerged) | `git branch -d <branch>` |
| Delete local (force) | `git branch -D <branch>` |
| Delete remote | `git push origin --delete <branch>` |
| List branches merged into base | `git branch --merged develop` |

## History rewriting

| Goal | Command |
|---|---|
| Squash last N commits | `git rebase -i HEAD~N` → mark `squash`/`fixup` |
| Reword last N | `git rebase -i HEAD~N` → mark `reword` |
| Fix mistake in last commit | `git add <file> && git commit --amend --no-edit` |
| Split last commit | `git reset HEAD~1` → re-stage + commit in pieces |
| Rebase feature on updated base | `git fetch origin develop && git rebase origin/develop` |
| Push after rebase | `git push --force-with-lease` |
| Abort an in-progress rebase | `git rebase --abort` |
| Continue rebase after conflict | `git add <files> && git rebase --continue` |

## Stash

| Goal | Command |
|---|---|
| Save WIP | `git stash push -m "msg"` |
| Save including untracked | `git stash push -u -m "msg"` |
| List | `git stash list` |
| Apply latest (keep in stash) | `git stash apply` |
| Apply latest + remove from stash | `git stash pop` |
| Apply specific | `git stash apply stash@{N}` |
| Drop one | `git stash drop stash@{N}` |
| Clear all | `git stash clear` |

## Undo, reset, revert

| Goal | Command | Destructive? |
|---|---|---|
| Unstage file | `git restore --staged <file>` | no |
| Discard unstaged change | `git restore <file>` | yes (work-tree) |
| Undo last commit, keep staged | `git reset --soft HEAD~1` | no |
| Undo last commit, keep unstaged | `git reset HEAD~1` | no |
| Undo last commit + discard | `git reset --hard HEAD~1` | **yes** |
| Revert pushed commit (safe) | `git revert <sha>` | no (creates new commit) |
| Revert range without commit | `git revert --no-commit <sha1> <sha2> && git commit` | no |

## Cherry-pick & tags

| Goal | Command |
|---|---|
| Apply commit | `git cherry-pick <sha>` |
| Apply without commit (review first) | `git cherry-pick --no-commit <sha>` |
| Annotated tag | `git tag -a v1.0.0 -m "Release 1.0.0"` |
| Tag a specific commit | `git tag -a v1.0.1 <sha> -m "msg"` |
| Push one tag | `git push origin v1.0.0` |
| Push all tags | `git push origin --tags` |
| Delete tag local + remote | `git tag -d v1.0.0 && git push origin --delete v1.0.0` |

## Inspection

| Goal | Command |
|---|---|
| Who/when on each line | `git blame <file>` |
| Same, ignoring whitespace commits | `git blame -w <file>` |
| Commits adding/removing string | `git log -S "needle"` |
| Commits whose diff matches regex | `git log -G "fetch\\(.*\\)"` |
| Commits touching file (with diffs) | `git log -p -- <file>` |
| Filter by author / message / date | `git log --author=X --grep=Y --since="2 weeks ago"` |

## Recovery

| Scenario | Recovery |
|---|---|
| Find any past HEAD position | `git reflog` (look for `HEAD@{N}`) |
| Restore branch tip pre-mistake | `git reset --hard HEAD@{N}` or `git reset --hard ORIG_HEAD` |
| Recover deleted branch | `git reflog \| grep "checkout: moving from <name>"` → `git branch <name> <sha>` |
| Recover deleted file | `git log --diff-filter=D -- <path>` → `git checkout <sha>^ -- <path>` |
| Inspect dangling objects (pre-GC) | `git fsck --lost-found` |
| Find first bad commit (manual) | `git bisect start && git bisect bad && git bisect good <sha>` → test → `good`/`bad` → `git bisect reset` |
| Find first bad commit (automated) | `git bisect start HEAD <good-sha> && git bisect run ./test.sh && git bisect reset` |

## 🔴 BLOCKING — Recovery anti-patterns

### Never run `git gc --prune=now` while recovering lost work

**Why:** `--prune=now` overrides the 14/30-day safety window and immediately deletes the dangling objects you're trying to restore — irreversible.

```bash
# ❌ WRONG — destroys recovery candidates
git gc --prune=now --aggressive

# ✅ CORRECT during a recovery — pause auto-gc instead
git config gc.auto 0
# ...recover...
git config --unset gc.auto
```

### Never `--force` push to a shared branch

**Why:** rewrites history for every other clone of the repo and can lose work that was pushed in parallel.

Use `--force-with-lease` (refuses if remote moved) on **your own** feature branches only.

## Useful aliases

```ini
# ~/.gitconfig
[alias]
    st       = status
    co       = checkout
    br       = branch
    last     = log -1 HEAD
    lg       = log --oneline --graph --decorate --all
    unstage  = restore --staged
    amend    = commit --amend --no-edit
    undo     = reset HEAD~1
    cleanup  = "!git branch --merged | grep -vE '^\\*|main|master|develop' | xargs -r -n 1 git branch -d"
```
