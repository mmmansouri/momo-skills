---
name: common-agent
description: >-
  Execution standards for all Buy Nature agents that perform concrete actions.
  Use when: agent writes/modifies code, reviews PRs, creates/updates external systems,
  or any task where tool usage is expected. NOT for read-only analysis or planning agents.
  Ensures agents use tools effectively, verify their work, and report results with proof.
---

# Common Agent Execution Standards

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Starting a Task

### 🔴 Trust Provided Context — No Broad Exploration

Your context comes from 3 sources (in priority order):

| Source | Contains | Trust Level |
|--------|----------|-------------|
| **Task prompt** | Pre-investigated file paths, design decisions, handoff excerpts from previous agents | High |
| **codebase-state.md** | Architecture snapshot (packages, entities, routes, stores) | High |
| **Coding-guide SKILL.md** | Conventions, patterns, naming rules | High |

**Rules:**
1. **START with execution**, not exploration
2. **ONLY use Read/Grep/Glob when:**
   - Reading a file you are about to MODIFY or REVIEW (mandatory: understand before changing/reviewing)
   - Accessing a file NOT mentioned in any context source
   - Provided context seems outdated or contradictory
3. **NEVER do broad exploration** — no `Glob **/*.java`, no `Grep` across entire codebase

```
🔴 WRONG — Exploring what context already provides:
- Reading SecurityConfig.java "to understand the security setup"
- Grepping for "OrderStatus" "to find all statuses"
- Globbing src/**/*.java "to understand project structure"

✅ CORRECT — Targeted reads for execution:
- Reading OrderService.java because you are about to EDIT it
- Reading a test file to understand patterns before adding tests
- Grepping for a specific method name to find its ONE call site
```

### 🔴 Received Implementation Context

When your Task prompt includes an **"Implementation Context"** section, the orchestrator already explored the codebase and the user approved a plan.

**With Implementation Context:**
1. **Trust the context** — file paths and design decisions are pre-validated
2. **Skip broad exploration** — do NOT re-read files already described
3. **Go straight to implementation** — read coding guide, then start coding
4. **Explore only on discovery** — if you find an undocumented dependency, read that file

**Without Implementation Context (simple task):**
- Read coding guide + codebase-state.md for existing patterns
- Read only the files you will modify (not broad exploration)
- If you suspect duplication but context doesn't cover it, report a CONTEXT GAP

### 🔴 Report Context Gaps — Never Explore Silently

If provided context is insufficient:

```
CONTEXT GAP:
- Missing: [what you need]
- File: [specific file path]
- Impact: [blocked or can proceed with assumption]
```

### 🔴 Pre-Flight Check

Verify before proceeding:
- **Python 3** → Run `python3 --version` (or `python --version` on Windows). If missing → STOP with: "Python 3 is required. Install from https://python.org"
- File operations → Read/Write access to project
- Code review → Git/GitHub MCP tools accessible
- External APIs → Required MCP connections available

If critical tools unavailable → **STOP** with error + remediation steps.

### 🔴 Critical Thinking — Challenge Before Executing

You are NOT a passive executor. Before implementing, assess the task for pertinence.

**Evaluate against:**
- **Technical soundness** — Is the requested approach correct? Better alternatives?
- **Necessity** — Does this already exist? Is it redundant with existing code?
- **Consistency** — Does it violate project conventions or architecture?
- **Side effects** — Could it break something, introduce debt, or cause regressions?
- **Scope** — Is the task vague, too broad, or missing critical details?

**When you identify a concern, STOP and report a structured warning:**

```
CONCERN: [what seems off]
- Risks: [concrete consequences]
- Alternative: [better approach]
- Recommendation: [what you suggest]
```

Then wait for orchestrator response before proceeding.

**This applies even when receiving Implementation Context** — the orchestrator is not infallible. If the approved plan has a flaw you can see, raise it.

**What this does NOT mean:**
- Do NOT refuse to work or be obstructionist
- Do NOT challenge trivially correct, well-scoped tasks
- If concern is acknowledged with "proceed anyway" → execute without repeating

---

## When Executing Changes

### 🔴 Efficiency Guardrails

| Task Type | Expected Tools | Self-Check Threshold |
|-----------|---------------|---------------------|
| Simple (SDD, 1-3 files) | 15-30 | 40 |
| Complex (with Implementation Context) | 30-50 | 60 |

**If you suspect you're past the threshold:**
1. STOP and assess: making progress or looping?
2. Looping on test failures → read FULL error (`tail -100 <logFile>`), don't guess-and-fix
3. Exploring excessively → report CONTEXT GAP, don't explore silently
4. Build/test cycle > 3 iterations on same error → STOP, report failure, let orchestrator decide

**Anti-patterns:**
- Edit → test → fail → edit → test → fail (same error) = STOP after 3rd attempt
- Reading 10+ files "to understand" = broad exploration (forbidden)
- Running mvn/npm directly = context flood (use build.py wrapper)

### 🔴 Follow BUILD → UPDATE → VERIFY → REPORT

| Step | Action | Tools |
|------|--------|-------|
| **BUILD** | Read context + files to modify | Read (targeted only) |
| **UPDATE** | Apply changes atomically | Edit, Write, Bash, MCP tools |
| **VERIFY** | Confirm changes persisted, run tests | Read, Bash |
| **REPORT** | Show proof + handoff summary | Output text |

### 🔴 Tool Uses > 0

Every invocation MUST use tools. 0 tool uses = automatic failure.

```
🔴 WRONG — Describing without doing:
"We should update UserService to add the new method..."

✅ CORRECT — Actually doing:
[Read UserService.java] → [Edit to add method] → [Bash to run tests]
"Modified UserService.java:42 — added calculateDiscount(). Tests pass (12/12)."
```

---

## When Completing a Task

### 🔴 Produce Handoff Summary

Every task MUST end with this structure:

```markdown
## Handoff Summary

### Files Created/Modified
- [Created] path/to/NewFile.java — purpose
- [Modified] path/to/Existing.java:NN — what changed

### Key Discoveries
- [Unexpected findings, gotchas, decisions made with rationale]

### Context Gaps Found
- [Info missing from provided context — feeds back to orchestrator]

### For Next Agent
- [Actionable items: new endpoints, data-testid attrs, patterns to follow]
```

### 🟡 Include Proof in Report

```
[Summary of what changed]
- Modified: path/to/file.java (+X lines, -Y lines)
- Tests: NN passed, 0 failed
- Tool uses: N (Read x2, Edit x3, Bash x1)
```

### 🟡 Never Silently Fail

```
🔴 WRONG:
[Tool fails] → "I wasn't able to complete the task."

✅ CORRECT:
[Tool fails] → Diagnose → Fix → Retry → Report resolution
```

---

## Execution Checklist

### 🔴 BLOCKING
- [ ] Started with execution, not exploration
- [ ] Only read files being modified or reviewed (not broad "understanding" reads)
- [ ] Tool uses > 0
- [ ] Changes verified (read back or test)
- [ ] Handoff Summary included
- [ ] Proof shown (excerpt, diff, or test output)

### 🟡 WARNING
- [ ] Context gaps reported (not silently explored around)
- [ ] Errors diagnosed and fixed (not skipped)
- [ ] Extra files read < 5 beyond provided context
