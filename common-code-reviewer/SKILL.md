---
name: common-code-reviewer
description: >-
  Code review workflow for GitHub PRs via MCP tools + gh CLI fallback.
  Use when: reviewing PRs, posting inline comments, submitting reviews,
  resolving threads, re-reviewing after fixes. Contains review workflow,
  summary formats, thread resolution commands, and MCP/CLI integration.
---

# Code Review Workflow

Standardized PR review process for all Buy Nature code reviewers.

## Core Rules

- **You MUST post the review directly on the GitHub PR** — never just return text
- Use MCP tools first, fall back to `gh` CLI if they fail
- Apply severity markers consistently
- Apply rules from your **loaded skills** — do NOT rely on inline checklists

## Severity Markers

| Marker | Meaning | Review Action |
|--------|---------|---------------|
| 🔴 **BLOCKING** | Must fix before merge | REQUEST_CHANGES |
| 🟡 **WARNING** | Should fix, tech debt if ignored | Mentioned in summary |
| 🟢 **BEST PRACTICE** | Nice to have, optional | APPROVE with suggestions |

## Review Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Initial Review** | Default — no prior reviews from this agent | Full code review + task tracker in summary |
| **Re-review** | User says "re-review"/"check again"/"check fixes" OR prior reviews exist | Analyze threads, resolve fixed ones, find new issues |

### Mode Detection Logic

```
1. Fetch existing reviews via get_reviews
2. Check if any review was authored by this agent (bot/authenticated user)
3. If prior reviews exist → RE-REVIEW mode
4. If user explicitly says "re-review", "check again", "review updates", "check fixes" → RE-REVIEW mode
5. Otherwise → INITIAL REVIEW mode
```

---

## Posting Reviews: MCP Tools (Primary) + gh CLI (Fallback)

Always try MCP tools first. If a call fails, immediately fall back to `gh` CLI via Bash.

### MCP Tools (Primary)

| Action | MCP Tool |
|--------|----------|
| Get PR details | `mcp__github__pull_request_read` (method: "get") |
| Get PR diff | `mcp__github__pull_request_read` (method: "get_diff") |
| Get PR files | `mcp__github__pull_request_read` (method: "get_files") |
| Get PR reviews | `mcp__github__pull_request_read` (method: "get_reviews") |
| Get review threads | `mcp__github__pull_request_read` (method: "get_review_comments") |
| Read file from PR branch | `mcp__github__get_file_contents` |
| Create pending review | `mcp__github__pull_request_review_write` (method: "create") |
| Add inline comment | `mcp__github__add_comment_to_pending_review` |
| Submit review | `mcp__github__pull_request_review_write` (method: "submit_pending") |
| Add general comment | `mcp__github__add_issue_comment` |

### gh CLI Fallback (via Bash)

Replace `OWNER/REPO` with the correct value (e.g., `buynature/buy-nature-back`):

```bash
# Get PR details
gh pr view <number> --repo OWNER/REPO --json title,body,state,files,additions,deletions

# Get PR diff
gh pr diff <number> --repo OWNER/REPO

# Get PR files
gh pr view <number> --repo OWNER/REPO --json files --jq '.files[].path'

# Read file from PR branch
gh api repos/OWNER/REPO/contents/<path>?ref=<branch> --jq '.content' | base64 -d

# Submit review
gh api repos/OWNER/REPO/pulls/<number>/reviews \
  --method POST \
  -f event="REQUEST_CHANGES" \
  -f body="Review summary here"

# Add inline comment
gh api repos/OWNER/REPO/pulls/<number>/comments \
  --method POST \
  -f body="Comment text" \
  -f path="src/..." \
  -f line=42 \
  -f side="RIGHT"

# Add general comment
gh pr comment <number> --repo OWNER/REPO --body "Comment text"
```

### Fallback Decision Logic

```
For each GitHub operation:
  1. Try MCP tool
  2. If MCP tool returns an error or is unavailable:
     a. Log: "MCP tool failed, falling back to gh CLI"
     b. Execute equivalent gh command via Bash
  3. If gh CLI also fails:
     a. Log the error
     b. Continue with remaining operations
     c. Report failures in final output
```

---

## Review Workflow

### Step 1: Get PR Information & Detect Mode

**1a. Fetch PR details:**
```
mcp__github__pull_request_read(method: "get", owner: "buynature", repo: "<repo>", pullNumber: <number>)
```

**1b. Fetch existing reviews to detect mode:**
```
mcp__github__pull_request_read(method: "get_reviews", owner: "buynature", repo: "<repo>", pullNumber: <number>)
```

**1c. If RE-REVIEW mode — fetch existing review threads:**
```
mcp__github__pull_request_read(method: "get_review_comments", owner: "buynature", repo: "<repo>", pullNumber: <number>)
```

Extract from each thread: `id`, `path`, `line`, `body`, `isResolved`, `isOutdated`.

**1d. Get the diff and files changed (both modes):**
```
mcp__github__pull_request_read(method: "get_diff", owner: "buynature", repo: "<repo>", pullNumber: <number>)
mcp__github__pull_request_read(method: "get_files", owner: "buynature", repo: "<repo>", pullNumber: <number>)
```

### Step 2: Analyze Changed Files

Apply relevant rules from your **loaded skills** based on file type. See your agent definition for the **file pattern → skill mapping** table.

### Step 2B: Re-review — Analyze Existing Threads (RE-REVIEW MODE ONLY)

Skip this step in Initial Review mode.

For each **unresolved** thread:

1. **Read current code:**
```
mcp__github__get_file_contents(owner: "buynature", repo: "<repo>", path: <thread.path>, ref: <PR_head_branch>)
```

2. **Determine if fixed:** Compare original issue with current code. Check `isOutdated` flag (if true, code changed → likely fixed).

3. **If FIXED → Resolve via GraphQL:**
```bash
gh api graphql \
  --field threadId="<PRRT_xxx>" \
  -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
```

> No MCP tool can resolve threads — GraphQL via `gh` CLI is the only way.

4. **If NOT FIXED → Leave unresolved.**

5. **Scan for NEW issues** not already covered by existing threads.

### Step 3: Create Pending Review

```
mcp__github__pull_request_review_write(method: "create", owner: "buynature", repo: "<repo>", pullNumber: <number>)
```

### Step 4: Add Inline Comments

```
mcp__github__add_comment_to_pending_review(
  owner: "buynature", repo: "<repo>", pullNumber: <number>,
  path: "src/...", line: <line_number>, side: "RIGHT", subjectType: "LINE",
  body: "🔴 **BLOCKING** - Issue title\n\nExplanation...\n\n**Suggestion:**\n```\n// fix\n```"
)
```

### Step 5: Submit Review

**If BLOCKING issues (new or still-open):**
```
mcp__github__pull_request_review_write(
  method: "submit_pending", owner: "buynature", repo: "<repo>", pullNumber: <number>,
  event: "REQUEST_CHANGES", body: "[Summary — see formats below]"
)
```

**If only WARNING/BEST PRACTICE (or all resolved):**
```
mcp__github__pull_request_review_write(
  method: "submit_pending", owner: "buynature", repo: "<repo>", pullNumber: <number>,
  event: "APPROVE", body: "[Summary — see formats below]"
)
```

### Step 6: Verify Review Was Posted

Fetch reviews again. If not visible, fall back to `gh` CLI to post a comment with the full review summary.

---

## Review Summary Formats

### Initial Review

```markdown
## 🔍 Code Review Summary

### Overall Assessment
[1-2 sentences]

### Issues Found

| Severity | Count |
|----------|-------|
| 🔴 BLOCKING | X |
| 🟡 WARNING | X |
| 🟢 BEST PRACTICE | X |

### 📋 Review Tasks

| Status | File | Line | Issue |
|--------|------|------|-------|
| ⬜ | `File` | 42 | 🔴 Brief description |
| ⬜ | `File` | 15 | 🟡 Brief description |

**Total: X tasks open**

### 🔴 BLOCKING Issues (Must Fix)
- `File:42` - Brief description

### 🟡 WARNING Issues (Should Fix)
- `File:15` - Brief description

### 🟢 Suggestions
- `File:30` - Brief description

### ✅ What's Good
- [Positive feedback]

### Recommendation
**[APPROVE / REQUEST_CHANGES]** - [Justification]
```

### Re-review

```markdown
## 🔄 Re-review Summary

### Overall Assessment
[1-2 sentences about progress]

### Resolution Progress

| Status | Count |
|--------|-------|
| ✅ Resolved | X |
| ⬜ Still Open | X |
| 🆕 New Issues | X |

### 📋 Task Tracker

| Status | File | Line | Issue |
|--------|------|------|-------|
| ✅ | `File` | 42 | 🔴 Fixed |
| ⬜ | `File` | 78 | 🟡 Still present |
| 🆕 | `File` | 12 | 🔴 New issue |

**Progress: X/Y previous tasks resolved (Z%) — N new issues found**

### Recommendation
**[APPROVE / REQUEST_CHANGES]** - [Justification]
```

---

## Thread Resolution Commands (GraphQL)

Thread resolution is **only available via GitHub GraphQL API**.

### Resolve a Thread

```bash
gh api graphql \
  --field threadId="PRRT_xxx" \
  -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
```

### Unresolve a Thread

```bash
gh api graphql \
  --field threadId="PRRT_xxx" \
  -f query='
    mutation($threadId: ID!) {
      unresolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
```

### Query Thread Status

```bash
gh api graphql \
  --field nodeId="PRRT_xxx" \
  -f query='
    query($nodeId: ID!) {
      node(id: $nodeId) {
        ... on PullRequestReviewThread {
          isResolved
          isOutdated
          comments(first: 1) {
            nodes { body path line }
          }
        }
      }
    }'
```

### Error Handling for GraphQL

If mutation fails: log error, add comment noting manual resolution needed, continue with remaining threads.

---

## Error Handling

| Error | Response |
|-------|----------|
| PR Not Found | "Unable to find PR #XXX. Verify the PR number and repository." |
| Large PR (>50 files) | "Large PR detected. Consider splitting. Reviewing critical paths..." |
| Thread Resolution Failed | "Could not resolve thread. Please resolve manually on GitHub." |
