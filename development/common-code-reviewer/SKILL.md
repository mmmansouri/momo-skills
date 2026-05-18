---
name: common-code-reviewer
description: >-
  Code review workflow for GitHub PRs via the `gh` CLI with atomic
  `gh api ... --input payload.json` submissions. Use this skill whenever the
  user asks to review a PR, audit a pull request, comment on changes, post
  inline review comments, submit a review, resolve review threads, re-review
  after fixes, check a teammate's diff, or look at a merge request — even
  when they don't explicitly say "review". Contains the workflow, severity
  tagging, gh CLI integration, thread resolution, and the output contract
  for inline comments and review summaries.
---

# Code Review Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE
> Markers serve a dual role: they tag rules **inside this skill** AND they prefix every **inline comment posted on the PR** (see Output Contract).

> **Transport:** the GitHub REST API via `gh` CLI, exclusively. The MCP
> path has been retired. The canonical pattern is a single atomic
> submission via `gh api ... --input payload.json` — see
> [gh-cli-fallback.md](references/gh-cli-fallback.md) for the full reference.

---

## When Reviewing a PR

Apply these foundational stances to every review:

1. **Post on the PR** — the review must land on GitHub, not in chat output.
2. **Apply loaded skills** — review rules come from the skills currently loaded in your context (e.g., `common-security`, `common-rest-api`, `common-frontend-angular`), not from a static checklist embedded here.
3. **One atomic call** — the entire review (summary body + event + every inline comment) is submitted in a **single** `gh api ... --input payload.json` request. Never split into per-comment calls.
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
[no gh call ever made]
```
##### CORRECT
```
Assistant builds <repo>/.claude/reviews/pr-<n>/payload.json via the file-writing tool,
then runs exactly one command:

  gh api repos/<owner>/<repo>/pulls/<n>/reviews \
    --method POST \
    --input <repo>/.claude/reviews/pr-<n>/payload.json
```

#### Never inline a comment body in a shell command — write the entire payload to a JSON file first
**Why:** inline comment bodies always contain backticks (fenced code blocks), dollar signs, asterisks, and quotes. Passing them through `-f body="…"`, `printf`, HEREDOC, or any other shell-parsed mechanism leads to a quoting catastrophe — backticks become command substitution, dollars become variable expansion, mismatched quotes break the command. The `--input <file>` flag of `gh api` reads the request body byte-for-byte from disk, bypassing shell parsing entirely. This is not a style preference; it is a hard constraint enforced by the Output Contract below, which **guarantees** shell-unsafe content in every body.

##### WRONG
````
gh api repos/owner/repo/pulls/12/comments \
  --method POST \
  -f body="🔴 **BLOCKING** — Null check missing
```java
if (foo == null) throw new InvalidOrderException(\"items required\");
```"
# bash interprets the backticks as command substitution; the embedded
# quotes mismatch the outer quoting; the whole command explodes.
````

##### CORRECT
```
1. Build <repo>/.claude/reviews/pr-<n>/payload.json via the file-writing tool.
2. Submit atomically:

   gh api repos/owner/repo/pulls/12/reviews \
     --method POST \
     --input <repo>/.claude/reviews/pr-<n>/payload.json
```

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
existing_reviews = gh api repos/<owner>/<repo>/pulls/<n>/reviews

if user_message matches /(re-review|check again|check fixes|review updates)/i:
    mode = RE_REVIEW
elif any(r.user.login == self for r in existing_reviews):
    mode = RE_REVIEW
else:
    mode = INITIAL
```

---

## When Performing the Review (Workflow)

📚 **All gh CLI commands for the workflow below are documented in
[gh-cli-fallback.md](references/gh-cli-fallback.md)** (the historical
filename is preserved — gh is no longer a fallback, it is the canonical
transport).

### Step 1 — Fetch PR info and detect mode
```bash
gh pr view <n> --repo <owner>/<repo> \
  --json title,body,state,files,additions,deletions,headRefName,baseRefName
gh pr diff <n> --repo <owner>/<repo>
gh api repos/<owner>/<repo>/pulls/<n>/reviews
```
If RE-REVIEW mode, also fetch threads:
```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments
```
Extract per thread: `id`, `path`, `line`, `body`, `in_reply_to_id`,
`position` (null ⇒ outdated).

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

1. Fetch current code:
   `gh api repos/<owner>/<repo>/contents/<path>?ref=<PR_head> --jq .content | base64 -d`.
2. Compare the original issue with the current code; check if `position`
   is null (⇒ the diff hunk changed under the comment ⇒ likely fixed).
3. **If FIXED** → resolve via `scripts/resolve-thread.sh <thread.id>`
   (see [thread-resolution-graphql.md](references/thread-resolution-graphql.md)).
4. **If NOT FIXED** → leave unresolved; include it in the new `comments[]`
   payload if you want to repost / emphasize.
5. Scan for NEW issues not covered by existing threads.

### Step 3 — Build the payload file

Write `<repo>/.claude/reviews/pr-<n>/payload.json` via your file-writing
tool. **Never** assemble it through shell echo / HEREDOC / printf.

Shape:
```json
{
  "body":  "<Initial-Review or Re-review summary markdown>",
  "event": "REQUEST_CHANGES" | "APPROVE" | "COMMENT",
  "comments": [
    {"path": "...", "line": <n>, "side": "RIGHT", "body": "<inline per Output Contract>"}
  ]
}
```

### Step 4 — Submit atomically

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews \
  --method POST \
  --input <repo>/.claude/reviews/pr-<n>/payload.json
```

| Findings include | `event` value |
|------------------|--------------|
| Any 🔴 BLOCKING (new or still-open) | `REQUEST_CHANGES` |
| Only 🟡 / 🟢, or all previously-blocking now resolved | `APPROVE` |
| Inline comments only, no summary verdict | `COMMENT` |

### Step 5 — Verify

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews \
  --jq '.[-1] | {id, state, html_url, submitted_at}'
```

If the most recent review is not the one you just submitted, inspect the
HTTP response from Step 4 — `gh` returns non-zero on API failure but
exit code alone is not always reliable; the verification call is
load-bearing.

---

## When Errors Occur

| Error | Response |
|-------|----------|
| PR not found | "Unable to find PR #<n> on `<owner>/<repo>`. Verify the number and repository." |
| Large PR (>50 files) | "Large PR detected (<file_count> files). Reviewing critical paths first; consider splitting the PR." |
| `gh api` returns `422 invalid path` | A comment targets a file not in the diff. Drop the bad entry from `comments[]`, rewrite the file, resubmit. |
| `gh api` returns `422 line/position required` | A comment targets a line outside the diff hunk. Recompute the line from `gh pr diff` and retry. |
| `gh api` returns `401/403` | `gh auth refresh -h github.com -s repo`. |
| Thread resolution failed | Add a comment "Resolved manually" with the thread ID; continue. |

---

## Output Contract

When producing review artifacts, deliver each in this exact form:

| Artifact | Required Form |
|----------|---------------|
| **Inline comment** | First line = severity marker + bold tag + one-line title. Blank line. 2-3 sentence explanation. Blank line. `**Suggestion:**` + fenced code block with the fix. See template below. |
| **Initial review summary** | Markdown using the Initial Review template: Overall Assessment, Issues Found counts, Review Tasks table, BLOCKING / WARNING / BEST PRACTICE sections, What's Good, Recommendation. |
| **Re-review summary** | Markdown using the Re-review template: Overall Assessment, Resolution Progress counts, Task Tracker (✅ / ⬜ / 🆕), Recommendation. |
| **Submission** | Single `gh api ... --input payload.json` call with `body`, `event`, `comments[]`. |
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
