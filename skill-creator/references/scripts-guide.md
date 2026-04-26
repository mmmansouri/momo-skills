# Bundling Scripts in a Skill

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Rules for **any** Python/Bash/Node script shipped under `scripts/` in a skill bundle.

## Contents
- [Solve, Don't Punt](#blocking--solve-dont-punt)
- [No Voodoo Constants](#blocking--no-voodoo-constants)
- [Make Execute-vs-Read Intent Explicit](#blocking--make-execute-vs-read-intent-explicit)
- [Plan-Validate-Execute Pattern](#warning--plan-validate-execute-pattern)
- [Package Dependencies](#warning--package-dependencies)
- [MCP Tool References](#warning--mcp-tool-references)
- [Don't Assume Tools Are Installed](#dont-assume-tools-are-installed)

---

## 🔴 BLOCKING — Solve, Don't Punt

Scripts must handle errors explicitly. Don't return raw exceptions and let Claude debug a stack trace.

```python
# 🔴 WRONG — punts to Claude
def read(path):
    return open(path).read()

# ✅ CORRECT — solves the failure
def read(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        # Caller expects empty content rather than failure
        return ""
```

**Why** : Claude can't always recover mid-task from a stack trace, especially on Windows path issues or missing dependencies. A graceful default is more recoverable than an exception.

## 🔴 BLOCKING — No Voodoo Constants

Justify every magic number with a one-line comment ("Ousterhout's law").

```python
# 🔴 WRONG — voodoo
TIMEOUT = 47

# ✅ CORRECT — self-documenting
# HTTP requests typically resolve in <30s; 30 covers slow connections.
REQUEST_TIMEOUT = 30
```

**Why** : if you don't know the right value, neither will Claude. Document the reasoning.

## 🔴 BLOCKING — Make Execute-vs-Read Intent Explicit

For each script, state the usage mode :

- **Execute** : `Run scripts/analyze_form.py to extract fields.`
- **Read as reference** : `See scripts/analyze_form.py for the field-extraction algorithm.`

Without this, Claude defaults to reading (consuming tokens) instead of executing.

## 🟡 WARNING — Plan-Validate-Execute Pattern

For batch or destructive operations, force an intermediate plan file :

1. Generate `changes.json` with proposed actions
2. Validate `changes.json` against a schema script
3. Execute only after validation passes

**Why** : reversible planning catches mistakes before the destructive step ; useful for skills that mutate files, run migrations, or apply bulk edits.

## 🟡 WARNING — Package Dependencies

| Environment | Network access |
|---|---|
| claude.ai | npm + PyPI + GitHub OK |
| Claude API | NO network, NO runtime install |

List required packages explicitly in SKILL.md. Don't assume `pip install` will succeed at runtime.

## 🟡 WARNING — MCP Tool References

Use fully qualified names : `ServerName:tool_name` (e.g., `BigQuery:bigquery_schema`, not `bigquery_schema`). Without the prefix, Claude may fail to locate the tool when multiple MCP servers are loaded.

## 🟢 Don't Assume Tools Are Installed

Before importing a library, document the install command :

```markdown
Install required package: `pip install pypdf`

Then use it:
\`\`\`python
from pypdf import PdfReader
\`\`\`
```
