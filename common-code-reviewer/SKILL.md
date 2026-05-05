---
name: common-code-reviewer
description: >-
  Code review workflow for GitHub PRs via MCP tools with gh CLI fallback. Use this
  skill whenever the user asks to review a PR, audit a pull request, comment on
  changes, post inline review comments, submit a review, resolve review threads,
  re-review after fixes, check a teammate's diff, or look at a merge request —
  even when they don't explicitly say "review". Contains the workflow, severity
  tagging, MCP/CLI integration, thread resolution, and the output contract for
  inline comments and review summaries.
---

# Code Review Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> Markers serve a dual role: they tag rules **inside this skill** AND they prefix every **inline comment posted on the PR** (see Output Contract).

---

## When Reviewing a PR

Apply these foundational stances to every review:

1. **Post on the PR** — the review must land on GitHub, not in chat output.
2. **Apply loaded skills** — review rules come from the skills currently loaded in your context (e.g., `common-security`, `common-rest-api`, `common-frontend-angular`), not from a static checklist embedded here.
3. **MCP-first, gh fallback** — try MCP tools first; fall back to `gh` CLI only when an MCP call fails.
4. **Tag every comment** — every inline comment carries a 🔴 / 🟡 / 🟢 marker.

### 🔴 BLOCKING

#### Always post the review on the GitHub PR — never return it as chat text only
**Why:** a review the user has to copy-paste is a review that will not be acted on. The PR is the canonical surface — comments anchor on lines, threads track resolution, notifications fire from PR events. Chat-only output bypasses every audit and follow-up mechanism the team relies on.

##### WRONG
```
Assistant: "Here is my review:
- Line 42: BLOCKING — null check missing
- Line 78: WARNING — magic number
..."
[no MCP / gh call ever made]
```
##### CORRECT
```
Assistant calls:
  mcp__github__pull_request_review_write(method: "create", ...)
  mcp__github__add_comment_to_pending_review(...)        // per finding
  mcp__github__pull_request_review_write(method: "submit_pending", ...)
Assistant: "Review submitted on PR #123 as REQUEST_CHANGES — 2 BLOCKING, 1 WARNING."
```

#### Try MCP tools first; fall back to `gh` CLI only after a confirmed MCP failure
**Why:** MCP tools return structured objects (typed responses, parsed thread IDs, automatic auth); `gh` CLI returns raw text or JSON the agent must re-parse. Skipping MCP discards typing and increases parsing-error surface; falling back proactively when MCP would have worked also adds latency and burns tokens.

#### Tag every inline comment with a 🔴 / 🟡 / 🟢 marker matching its review action
**Why:** the marker drives the review's submission event — any 🔴 ⇒ `REQUEST_CHANGES`, only 🟡 / 🟢 ⇒ `APPROVE`. Without explicit tagging the agent (and the next re-review pass) cannot derive the correct event mechanically, leading to mis-submitted reviews where blocking issues land as `APPROVE`.

##### WRONG
````
"Add a null check here, otherwise this NPEs on empty input."
[no marker → re-review cannot tell if this was blocking or nitpick]
````
##### CORRECT
````
🔴 **BLOCKING** — Null check missing

`processOrder(order)` dereferences `order.items` without a null guard.
On empty payloads this throws NPE before reaching validation.

**Suggestion:**
```java
if (order.items == null || order.items.isEmpty()) {
    throw new InvalidOrderException("items required");
}
```
````

---

## When Detecting Review Mode

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Initial Review** | No prior review from this agent on the PR | Full review + task tracker in summary |
| **Re-review** | Prior review by this agent exists OR user says "re-review", "check again", "check fixes", "review updates" | Analyze threads, resolve fixed ones, find new issues |

### Detection Algorithm
```
existing_reviews = mcp__github__pull_request_read(method="get_reviews", ...)

if user_message matches /(re-review|check again|check fixes|review updates)/i:
    mode = RE_REVIEW
elif any(r.author == self for r in existing_reviews):
    mode = RE_REVIEW
else:
    mode = INITIAL
```

---

## When Performing the Review (Workflow)

📚 **References:** [gh-cli-fallback.md](references/gh-cli-fallback.md)

### Step 1 — Fetch PR info and detect mode
```
mcp__github__pull_request_read(method: "get",          owner: "<owner>", repo: "<repo>", pullNumber: <n>)
mcp__github__pull_request_read(method: "get_reviews",  owner: "<owner>", repo: "<repo>", pullNumber: <n>)
mcp__github__pull_request_read(method: "get_diff",     owner: "<owner>", repo: "<repo>", pullNumber: <n>)
mcp__github__pull_request_read(method: "get_files",    owner: "<owner>", repo: "<repo>", pullNumber: <n>)
```
If RE-REVIEW mode, also fetch threads:
```
mcp__github__pull_request_read(method: "get_review_comments", owner: "<owner>", repo: "<repo>", pullNumber: <n>)
```
Extract per thread: `id`, `path`, `line`, `body`, `isResolved`, `isOutdated`.

### Step 2 — Analyze changed files

For each changed file, apply rules from the **skill loaded in your context that matches the file type**. The orchestrating agent definition provides the file-pattern → skill mapping. Illustrative examples:

| File pattern | Likely loaded skill |
|--------------|---------------------|
| `*.java`, `*.kt` | `common-java-developer`, `common-java-jpa`, `common-java-testing` |
| `*.ts` (Angular) | `common-frontend-angular`, `common-frontend-testing` |
| `*Controller.java`, REST endpoints | `common-rest-api` |
| Anything touching auth, crypto, or input handling | `common-security` |

### Step 2B — (Re-review only) Analyze existing threads

Skip in INITIAL mode. For each **unresolved** thread:

1. Fetch current code: `mcp__github__get_file_contents(... ref: <PR_head>)`.
2. Compare original issue with current code; check `isOutdated` (true ⇒ code changed ⇒ likely fixed).
3. **If FIXED** → resolve via `scripts/resolve-thread.sh <thread.id>` (see [thread-resolution-graphql.md](references/thread-resolution-graphql.md)).
4. **If NOT FIXED** → leave unresolved; repost the issue if context warrants emphasis.
5. Scan for NEW issues not covered by existing threads.

### Step 3 — Create pending review
```
mcp__github__pull_request_review_write(method: "create", owner: "<owner>", repo: "<repo>", pullNumber: <n>)
```

### Step 4 — Add inline comments (one per finding)
```
mcp__github__add_comment_to_pending_review(
  owner: "<owner>", repo: "<repo>", pullNumber: <n>,
  path: "<path>", line: <n>, side: "RIGHT", subjectType: "LINE",
  body: "<comment per Output Contract>"
)
```

### Step 5 — Submit review

| Findings include | Submit event |
|------------------|--------------|
| Any 🔴 BLOCKING (new or still-open) | `REQUEST_CHANGES` |
| Only 🟡 / 🟢, or all previously-blocking now resolved | `APPROVE` |

```
mcp__github__pull_request_review_write(
  method: "submit_pending", owner: "<owner>", repo: "<repo>", pullNumber: <n>,
  event: "<REQUEST_CHANGES | APPROVE>", body: "<summary per Output Contract>"
)
```

### Step 6 — Verify

Re-fetch reviews. If the submitted review is not visible, fall back to `gh` CLI (see [gh-cli-fallback.md](references/gh-cli-fallback.md)) to repost the summary as a PR comment.

---

## When Errors Occur

| Error | Response |
|-------|----------|
| PR not found | "Unable to find PR #<n> on `<owner>/<repo>`. Verify the number and repository." |
| Large PR (>50 files) | "Large PR detected (<file_count> files). Reviewing critical paths first; consider splitting the PR." |
| MCP call failed | Log `MCP failed: <op>`, invoke `gh` CLI equivalent, continue. |
| `gh` CLI also failed | Log error, continue with remaining ops, list failures in final output. |
| Thread resolution failed | Add a comment "Resolved manually" with the thread ID; continue. |

---

## Output Contract

When producing review artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Inline comment** | First line = severity marker + bold tag + one-line title. Blank line. 2-3 sentence explanation. Blank line. `**Suggestion:**` + fenced code block with the fix. See template below. |
| **Initial review summary** | Markdown using the Initial Review template: Overall Assessment, Issues Found counts, Review Tasks table, BLOCKING / WARNING / BEST PRACTICE sections, What's Good, Recommendation. |
| **Re-review summary** | Markdown using the Re-review template: Overall Assessment, Resolution Progress counts, Task Tracker (✅ / ⬜ / 🆕), Recommendation. |
| **Thread resolution** | `scripts/resolve-thread.sh <thread_id>` — never an inline `gh api graphql` block in the conversation. |

### Inline Comment Template
````
🔴 **BLOCKING** — <one-line title>

<2-3 sentence explanation of the issue and its concrete consequence>

**Suggestion:**
```<lang>
<concrete fix>
```
````

### Initial Review Template
```markdown
## 🔍 Code Review Summary

### Overall Assessment
<1-2 sentences>

### Issues Found
| Severity | Count |
|----------|-------|
| 🔴 BLOCKING | X |
| 🟡 WARNING | X |
| 🟢 BEST PRACTICE | X |

### 📋 Review Tasks
| Status | File | Line | Issue |
|--------|------|------|-------|
| ⬜ | `path` | 42 | 🔴 brief |

**Total: X tasks open**

### 🔴 BLOCKING (Must Fix)
- `file:line` — brief

### 🟡 WARNING (Should Fix)
- `file:line` — brief

### 🟢 Suggestions
- `file:line` — brief

### ✅ What's Good
- <positive note>

### Recommendation
**APPROVE | REQUEST_CHANGES** — <justification>
```

### Re-review Template
```markdown
## 🔄 Re-review Summary

### Overall Assessment
<1-2 sentences on progress>

### Resolution Progress
| Status | Count |
|--------|-------|
| ✅ Resolved | X |
| ⬜ Still Open | X |
| 🆕 New Issues | X |

### 📋 Task Tracker
| Status | File | Line | Issue |
|--------|------|------|-------|
| ✅ | `path` | 42 | 🔴 fixed |
| ⬜ | `path` | 78 | 🟡 still present |
| 🆕 | `path` | 12 | 🔴 new |

**Progress: X/Y resolved (Z%) — N new**

### Recommendation
**APPROVE | REQUEST_CHANGES** — <justification>
```
