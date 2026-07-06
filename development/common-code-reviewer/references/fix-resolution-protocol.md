# Fix Resolution Protocol

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

This reference is the **contract for fix authors** (the agent that
consumes the review — typically a dev agent in fix-review mode, e.g.
`buy-nature-dev` Path C). The reviewer never executes this protocol; it
owns only the contract definition. The fix author reads this file.

---

## When Marking a Comment Fixed

### 🔴 BLOCKING

#### Mark a comment fixed by editing its body — flip `- [ ]` → `- [x]`, never repost
**Why:** the checkbox state IS the persistent signal across runs. Posting
a reply ("done!") does not flip the box, and a re-review pass driven by
the parent skill's `Step 2B` will see the box still unchecked and re-flag
the issue. Editing the original comment is the only operation the
re-review skill knows how to read.

#### Edit via PATCH with `--input <file>`, under the fix-author identity — never inline the body
**Why:** the same anti-quoting rule that governs the initial review
applies to the edit. Comment bodies contain backticks, dollars, fenced
code. Use `gh api` PATCH with a file payload. And the edit **mutates the
PR**, so it runs through the **fix-author** identity the host project
designates — `$FIX_GH`, the mirror of the reviewer's `$REVIEW_GH`; when
undefined it is plain `gh`, so single-identity projects are unaffected:

```bash
FIX_GH="${FIX_GH:-gh}"   # host overrides with a role-scoped wrapper (e.g. dev role)

# Build <repo>/.claude/reviews/pr-<n>/edit-<comment_id>.json containing:
# {"body": "<original body with - [ ] flipped to - [x]>"}

$FIX_GH api repos/<owner>/<repo>/pulls/comments/<comment_id> \
  --method PATCH \
  --input <repo>/.claude/reviews/pr-<n>/edit-<comment_id>.json
```

The body must preserve the original comment **byte-for-byte** except for
the single `- [ ]` → `- [x]` substitution. Rewriting the suggestion,
trimming whitespace, or "improving" the wording corrupts the audit trail
and may confuse re-review's checkbox detection.

---

## When the Box and the Thread Diverge

### 🟡 WARNING

#### Checking the box does NOT resolve the GitHub thread — that stays the reviewer's call
**Why:** `- [x] Fixed` means "fix author claims the fix is in".
`resolve-thread.sh` means "reviewer has verified the code matches". They
are decoupled by design: the fix author cannot self-certify a fix as
valid. Re-review (`Step 2B` of the parent skill) reads the checkbox,
re-verifies against the current code, and *then* resolves the thread.

**Identity note (GitHub Apps vs user PATs):** a GitHub **App** installation
token with `pull_requests: write` can edit review comments AND reviews
authored by a **different** actor — authorship is *not* required for App
tokens. So a split reviewer/fix-author identity (two distinct Apps) still
lets the fix author flip `- [ ]` → `- [x]` directly via PATCH/PUT — no
fallback needed.
This differs from **user PATs**: a user may only edit comments they
authored. If (and only if) a fix author runs under a user PAT that did not
author the comment, fall back to **replying** to the thread with a
`- [x] Fixed (claimed)` line and let the reviewer flip the original box on
the next pass.

---

## When Handling 🟢 BEST PRACTICE Comments

### 🟢 BEST PRACTICE

#### Skip 🟢 comments — they carry no checkbox by design
🟢 suggestions are not actions. If a 🟢 suggestion is implemented anyway,
the resulting diff in the next push speaks for itself; no edit is
required. Leave the 🟢 comment alone — the lack of checkbox is the
signal.
