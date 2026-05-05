# gh CLI Fallback Reference

Use this reference when an MCP GitHub call fails. Each section maps a workflow operation to its `gh` equivalent.

## Table of Contents

- [Auth & Setup](#auth--setup)
- [Read Operations](#read-operations)
- [Write Operations](#write-operations)
- [Fallback Decision Algorithm](#fallback-decision-algorithm)

---

## Auth & Setup

`gh` CLI must be authenticated (`gh auth status`). Replace `<owner>/<repo>` with the project's slug (e.g., `acme/api-svc`).

---

## Read Operations

### Get PR details
```bash
gh pr view <n> --repo <owner>/<repo> --json title,body,state,files,additions,deletions
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

## Write Operations

### Submit a review (with summary body)
```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews \
  --method POST \
  -f event="REQUEST_CHANGES" \
  -f body="<summary>"
```
`event` ∈ `APPROVE | REQUEST_CHANGES | COMMENT`.

### Add an inline review comment
```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments \
  --method POST \
  -f body="<marker + comment>" \
  -f path="src/..." \
  -f line=42 \
  -f side="RIGHT"
```

### Add a general PR comment
```bash
gh pr comment <n> --repo <owner>/<repo> --body "<text>"
```

---

## Fallback Decision Algorithm

```
for op in workflow_operations:
    try:
        result = mcp_tool(op)
    except McpError:
        log("MCP failed for " + op + ", falling back to gh CLI")
        try:
            result = gh_cli(op)
        except CliError as e:
            log("gh CLI also failed for " + op + ": " + str(e))
            failures.append(op)
            continue
    accumulate(result)

if failures:
    report_failures_at_end(failures)
```

Apply this per operation, not per workflow — partial degradation is preferred over aborting the entire review.
