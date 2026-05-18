# GitHub CLI Reference for Code Review

> This is the **primary** reference for posting reviews via the GitHub REST
> API using the `gh` CLI. The MCP path has been retired (see SKILL.md
> §"When Posting a Review" for the rationale).
>
> The historical filename `gh-cli-fallback.md` is preserved so that legacy
> links keep working — but `gh` is no longer a fallback, it is the canonical
> transport.

## Table of Contents

- [Auth & Setup](#auth--setup)
- [Read Operations](#read-operations)
- [Posting a Review (Atomic Pattern)](#posting-a-review-atomic-pattern)
- [Why a File, Not an Inline Body](#why-a-file-not-an-inline-body)
- [Re-review Operations](#re-review-operations)
- [Error Recovery](#error-recovery)

---

## Auth & Setup

`gh` CLI must be authenticated (`gh auth status`). Replace `<owner>/<repo>`
with the project's slug (e.g., `acme/api-svc`).

---

## Read Operations

### Get PR details
```bash
gh pr view <n> --repo <owner>/<repo> \
  --json title,body,state,files,additions,deletions,headRefName,baseRefName
```

### Get PR diff
```bash
gh pr diff <n> --repo <owner>/<repo>
```

### Get PR file paths
```bash
gh pr view <n> --repo <owner>/<repo> --json files --jq '.files[].path'
```

### Read file from PR branch
```bash
gh api repos/<owner>/<repo>/contents/<path>?ref=<branch> --jq '.content' | base64 -d
```

### Get existing reviews
```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews
```

### Get review comments (threads)
```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments
```

---

## Posting a Review (Atomic Pattern)

The endpoint `POST /repos/{owner}/{repo}/pulls/{n}/reviews` accepts the
entire review — summary body + event + inline comments — in a single JSON
payload. Use this. Never split into N+2 separate calls.

### Step 1 — Build the payload as a JSON file

Write the file via your editor's file-writing tool (e.g. the `Write` tool
of Claude Code, or `tee`/`jq -n`). **Never** assemble it through `echo`,
`printf`, HEREDOC, or `gh api -f body=`. The body strings will contain
backticks, dollar signs, asterisks and quotes — bash will explode.

Canonical path (recommended): `<repo>/.claude/reviews/pr-<n>/payload.json`

Shape:

```json
{
  "body": "## 🔍 Code Review Summary\n\n### Overall Assessment\n…",
  "event": "REQUEST_CHANGES",
  "comments": [
    {
      "path": "src/path/File.java",
      "line": 42,
      "side": "RIGHT",
      "body": "🔴 **BLOCKING** — Null check missing\n\n…\n\n**Suggestion:**\n```java\nif (foo == null) …\n```"
    },
    {
      "path": "src/path/File.ts",
      "line": 18,
      "side": "RIGHT",
      "body": "🟡 **WARNING** — …"
    }
  ]
}
```

| Field | Value | Notes |
|-------|-------|-------|
| `body` | string | Summary markdown. Per the Output Contract — Initial / Re-review template. |
| `event` | `APPROVE` \| `REQUEST_CHANGES` \| `COMMENT` | Drives the submission state. Per the severity rule in `SKILL.md`. |
| `comments[]` | array | One object per inline finding. Empty array `[]` if no inline (rare, but allowed). |
| `comments[].path` | string | Path relative to repo root. Must match a file changed in the PR. |
| `comments[].line` | integer | Line number on `side`. For multi-line, also pass `start_line` + `start_side` (see GitHub REST docs). |
| `comments[].side` | `LEFT` \| `RIGHT` | Almost always `RIGHT` (the new state). |
| `comments[].body` | string | The inline comment markdown. Same Output Contract. |

### Step 2 — Submit atomically

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews \
  --method POST \
  --input <repo>/.claude/reviews/pr-<n>/payload.json
```

One HTTP request creates the review with all inline comments, in the
submitted state defined by `event`. **No pending review, no separate
submit step.** If the call fails, nothing is posted (atomic).

### Step 3 — Capture the review URL

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews \
  --jq '.[-1] | {id, state, html_url, submitted_at}'
```

Use this in the final summary returned to the user.

---

## Why a File, Not an Inline Body

The `-f/--raw-field` and `-F/--field` flags of `gh api` pass values
through shell-parsed key=value pairs. Comment bodies in this skill
**always** contain at least one of: backticks (fenced code blocks),
dollar signs (variable references mentioned in suggestions), quotes,
asterisks. The shell will interpret these before `gh` sees the value.

### WRONG — and reproduces the "agent stuck in quoting hell" failure mode

```bash
gh api repos/owner/repo/pulls/12/comments \
  --method POST \
  -f body="🔴 **BLOCKING** — Null check missing

  ```java
  if (foo == null) throw new InvalidOrderException(\"items required\");
  ```"
  # ↑ bash interprets the backticks as command substitution; the quotes in
  # the suggested code mismatch the outer quoting; whole command explodes.
```

### CORRECT — payload written via the file-writing tool

```bash
# 1. Write payload.json via the file-writing tool (zero shell parsing).
# 2. One atomic call:
gh api repos/owner/repo/pulls/12/reviews \
  --method POST \
  --input /path/to/payload.json
```

This rule is not a style preference — it is a hard constraint. The
Output Contract guarantees shell-unsafe content in every body.

---

## Re-review Operations

### List existing review threads with body + outdated flag
```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments \
  --jq '.[] | {id, path, line, body, in_reply_to_id, position}'
```

### Resolve a thread (GraphQL — see `thread-resolution-graphql.md`)
```bash
buy-nature-ai/skills/common-code-reviewer/scripts/resolve-thread.sh <thread_id>
```
(Path depends on how this skill is installed; adapt accordingly.)

### Reply to a thread (when posting an addendum)

Add the same `comments[]` payload pattern but with `in_reply_to_id` set
on the relevant entry. Note: GitHub's create-review endpoint does not
accept `in_reply_to_id` directly — for thread replies, use the dedicated
`POST /pulls/<n>/comments` endpoint with the same `--input file` pattern
(payload shape `{body, in_reply_to_id}`).

---

## Error Recovery

| Symptom | Cause | Recovery |
|---------|-------|----------|
| `HTTP 422 — Unprocessable Entity, invalid path` | A comment targets a file not in the PR diff | Drop the bad entry from `comments[]` and resubmit. The whole payload is atomic — partial submissions are not possible. |
| `HTTP 422 — line/position required` | Line number is on an unchanged line in the diff hunk | Recompute the line against `gh pr diff` and update the entry. |
| `HTTP 401 / 403` | Token expired or lacks scope | Run `gh auth refresh -h github.com -s repo` and retry. |
| `gh: command not found` | gh CLI missing on the host | Install gh (or, in an agent context, escalate to the user). Do not try to substitute with curl + manual auth. |
| Payload file missing / unreadable | Tooling forgot to write it | Re-run the payload construction step; do not retry the gh call until the file is non-empty JSON. |

---

## Quick Cheatsheet

| Operation | Command |
|-----------|---------|
| Create + submit review atomically | `gh api repos/.../pulls/<n>/reviews --method POST --input payload.json` |
| Get last review URL | `gh api repos/.../pulls/<n>/reviews --jq '.[-1].html_url'` |
| Reply to a thread | `gh api repos/.../pulls/<n>/comments --method POST --input reply.json` |
| Resolve a thread | `scripts/resolve-thread.sh <thread_id>` |
| Add a top-level PR comment (not a review) | `gh pr comment <n> --repo <owner>/<repo> --body-file file.md` |
