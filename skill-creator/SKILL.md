---
name: skill-creator
description: >-
  Guide for creating and reviewing AI agent skills. Use when: (1) creating a new SKILL.md
  file, (2) editing or rewriting an existing SKILL.md, (3) writing or fixing skill
  frontmatter (name, description), (4) creating references/ files for a skill,
  (5) auditing or reviewing skill quality, (6) adding severity markers or restructuring
  skill sections. Triggers on any work involving files in a skills/ directory.
  Contains structure templates, naming conventions, severity markers, and anti-patterns.
---

# Skill Creator Guide

> **Goal:** Create skills that agents can **apply immediately**, not just read.

---

## When Starting a New Skill

📚 **References:** [workflows.md](references/workflows.md) | [output-patterns.md](references/output-patterns.md)

### 🔴 Start With Use Cases, Not Code

Before writing anything, define **2-3 concrete use cases**:

```
Use Case: [Name]
Trigger: User says "[specific phrases]"
Steps:
1. [Action]
2. [Action]
Result: [What success looks like]
```

For each use case, identify:
- **Scripts** needed (deterministic operations)
- **References** that save rediscovery (schemas, docs, domain knowledge)
- **Assets** for output (templates, icons)

### Composability

Skills can load simultaneously. Design yours to work alongside others — don't assume it's the only capability available.

---

## Core Principles

### 🔴 Concise is Key

The context window is a **public good**. Claude is already very smart — only add context it doesn't already have.

Challenge each piece of information:
- "Does Claude really need this explanation?"
- "Does this paragraph justify its token cost?"

✅ **Prefer concise examples over verbose explanations.**

### 🔴 Set Appropriate Degrees of Freedom

| Freedom Level | Use When | Format |
|---------------|----------|--------|
| **High** | Multiple approaches valid, context-dependent | Text instructions |
| **Medium** | Preferred pattern exists, some variation OK | Pseudocode with parameters |
| **Low** | Operations fragile, consistency critical | Specific scripts, few params |

### 🔴 Progressive Disclosure

Three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — When skill triggers (<5K words ideal)
3. **Bundled resources** — As needed by Claude (unlimited via file reads)

Keep SKILL.md focused. Move detailed docs to `references/` and link at section start with 📚.

---

## Skill Structure

```
skill-name/
├── SKILL.md              # Required — main instructions
├── references/           # Documentation loaded as needed
│   ├── topic-1.md
│   └── topic-2.md
├── scripts/              # Executable code (Python/Bash)
│   └── helper.py
└── assets/               # Files used in output (templates, icons)
    └── template.pptx
```

### Bundled Resources

| Directory | Purpose | When to Include |
|-----------|---------|-----------------|
| **scripts/** | Deterministic, token-efficient operations | Same code rewritten repeatedly; fragile operations |
| **references/** | Documentation loaded on-demand | Claude needs to reference while working; >10K words → add grep hints in SKILL.md |
| **assets/** | Files used in output, NOT loaded into context | Templates, images, boilerplate for final output |

**Content in SKILL.md OR references/, not both.**

---

## When Writing Frontmatter

### 🔴 Description is the PRIMARY Trigger

The description determines **when Claude loads your skill**. It's the first level of progressive disclosure.

**Structure:** `[What it does] + [When to use it] + [Key capabilities]`

```yaml
# ✅ GOOD — specific, with trigger phrases
description: >-
  Analyzes Figma design files and generates developer handoff documentation.
  Use when user uploads .fig files, asks for "design specs", "component
  documentation", or "design-to-code handoff".

# ✅ GOOD — includes negative triggers
description: >-
  Advanced data analysis for CSV files. Use for statistical modeling,
  regression, clustering. Do NOT use for simple data exploration
  (use data-viz skill instead).

# 🔴 WRONG — too vague
description: Helps with projects.

# 🔴 WRONG — missing triggers
description: Creates sophisticated multi-page documentation systems.
```

### 🔴 BLOCKING — Description Rules

| Rule | Why |
|------|-----|
| Include trigger phrases users would say | Claude matches description to user input |
| Add negative triggers ("Do NOT use for...") if needed | Prevents over-triggering |
| Under **1024 characters** | Hard limit |
| **No XML tags** (`<` `>`) | Security: frontmatter appears in system prompt |
| **No "claude" or "anthropic"** in skill name | Reserved by Anthropic |

### Required and Optional Fields

```yaml
---
name: skill-name              # Required: kebab-case, must match folder name
description: >-               # Required: what + when + capabilities
  [description here]
license: MIT                   # Optional: for open-source skills
compatibility: >-              # Optional (1-500 chars): environment requirements
  Requires Claude Code with Bash access
allowed-tools: "Bash(python:*) WebFetch"  # Optional: restrict tool access
metadata:                      # Optional: custom key-value pairs
  author: Buy Nature
  version: 1.0.0
---
```

---

## When Writing Instructions

### 🔴 BLOCKING — Content Rules

| Principle | Why |
|-----------|-----|
| **Workflow-oriented sections** ("When X") | Agent knows WHEN to apply, not just WHAT exists |
| **Severity markers** (🔴/🟡/🟢) | Agent prioritizes blocking issues first |
| **WRONG/CORRECT examples** | Agent recognizes patterns to fix |
| **Inline references** (📚 at section start) | Agent finds details without scrolling |
| **Critical instructions at top** | Agent reads top-down; buried rules get missed |

### 🔴 BLOCKING — Writing Style

**Imperative mood** — Write all instructions as direct commands.

```markdown
# 🔴 WRONG — passive/conditional voice
You should validate input before processing
It is recommended to use dependency injection

# ✅ CORRECT — imperative mood
Validate input before processing
Use dependency injection
```

**Negation with alternative** — Every negation ("Don't", "Never", "Avoid") must include a concrete alternative. If the right alternative is unclear, ask the user before deciding.

```markdown
# 🔴 WRONG — negation without alternative
Don't use var for variable declarations
Avoid inline styles

# ✅ CORRECT — negation with concrete alternative
Don't use var for variable declarations. Use const by default, or let when reassignment is needed
Avoid inline styles. Use CSS modules or styled-components instead
```

**Hierarchical indented structure** — Organize instructions as Section > Subsection > Rule > Detail > Example. Flat lists lose relationships between concepts.

```markdown
# 🔴 WRONG — flat list, no hierarchy
- Use dependency injection
- Constructor injection preferred
- Avoid service locator pattern
- Always define interfaces for services

# ✅ CORRECT — indented hierarchy showing relationships
- Use dependency injection
  - Prefer constructor injection
  - Don't use service locator pattern. Use constructor or method injection instead
    ```java
    // ✅ CORRECT
    public MyService(UserRepository repo) {}
    ```
  - Define interfaces for all injected services
```

### Section Naming: Use "When X" Format

```markdown
## When Writing New Code       # ✅ Actionable
## When Handling Exceptions    # ✅ Tells agent WHEN to apply
## Best Practices              # 🔴 WRONG — too vague
## Overview                    # 🔴 WRONG — agent skips this
```

### Severity Markers

| Marker | Meaning | Agent Behavior |
|--------|---------|----------------|
| 🔴 **BLOCKING** | Fails code review, must fix | Agent fixes BEFORE other work |
| 🟡 **WARNING** | Should fix, not blocking | Agent fixes if time permits |
| 🟢 **BEST PRACTICE** | Recommended improvement | Agent applies when writing new code |

### 🟡 WARNING — Instruction Compliance Tips

When instructions aren't followed:

1. **Put critical rules at the top** — not buried in the middle
2. **Use `CRITICAL:` or `## Important` headers** — visual priority
3. **Use scripts for deterministic validation** — code is deterministic, language interpretation isn't
4. **Be specific, not ambiguous:**

```markdown
# 🔴 WRONG — vague
Make sure to validate things properly

# ✅ CORRECT — specific
CRITICAL: Before calling create_project, verify:
- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

### 🟡 WARNING — Other Content Guidelines

| Principle | Why |
|-----------|-----|
| **"Use When" descriptions** for patterns | Agent knows when pattern applies |
| **Quick reference tables** | Fast lookup during coding |
| **No duplication** — content in SKILL.md OR references, not both | Saves tokens, prevents stale content |
| **Code Review Checklist at end** | Agent validates work before finishing |

---

## When Testing Skills

### 🔴 Trigger Tests

Test that your skill loads at the right times:

```
Should trigger:
- "Help me set up a new workspace"
- "I need to create a project"          # Paraphrased
- "Initialize project for Q4 planning"  # Variation

Should NOT trigger:
- "What's the weather?"
- "Help me write Python code"
- "Create a spreadsheet"                # Unless skill handles this
```

**Debugging:** Ask Claude: *"When would you use the [skill name] skill?"* — it will quote the description back. Adjust based on what's missing.

### 🟡 Functional Tests

Verify the skill produces correct outputs:

```
Test: [scenario name]
Given: [input conditions]
When: Skill executes workflow
Then:
  - [expected output 1]
  - [expected output 2]
  - No errors
```

### Iteration Signals

| Signal | Problem | Fix |
|--------|---------|-----|
| Skill doesn't load when it should | **Under-triggering** | Add keywords and trigger phrases to description |
| Users manually enabling it | **Under-triggering** | Add more "Use when" variations |
| Skill loads for unrelated queries | **Over-triggering** | Add negative triggers ("Do NOT use for..."), be more specific |
| Inconsistent results | **Execution issue** | Improve instructions, add error handling, use scripts |
| Responses degraded / slow | **Context too large** | Move content to references/, keep SKILL.md under 5K words |

---

## SKILL.md Template

```markdown
---
name: skill-name
description: >-
  What this skill does AND when to use it. Include trigger phrases.
---

# Skill Title

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When [Situation 1]

📚 **References:** [detailed-file.md](references/detailed-file.md)

### 🔴 BLOCKING
- Rule 1 with **brief explanation**
  - Detail or sub-condition
  - Detail or sub-condition
    \`\`\`language
    // example code
    \`\`\`

### 🟡 WARNING
- Warning 1
  - Detail or context

### 🟢 BEST PRACTICE
- Recommendation 1

### Examples
\`\`\`language
// 🔴 WRONG - explanation
bad_code();

// ✅ CORRECT - explanation
good_code();
\`\`\`

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] Item 1

### 🟢 BEST PRACTICE
- [ ] Item 2
```

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| **Information dump** (500 lines of prose) | Agent gets lost, skips content | Use tables, bullets, WRONG/CORRECT pairs |
| **No priority indicators** | Everything looks equally important | Add 🔴/🟡/🟢 severity markers |
| **References only at bottom** | Agent doesn't see link until too late | Put 📚 at section start |
| **Duplicate content** (SKILL.md AND references/) | Wasted tokens, content drifts apart | Content in ONE place only |
| **Generic section names** ("Best Practices") | Agent doesn't know when to apply | Use "When X" naming |
| **Vague instructions** ("validate properly") | Claude interprets loosely | Be specific, use scripts |
| **Passive/conditional voice** ("You should...", "It is recommended...") | Agent treats it as optional, not mandatory | Use imperative mood ("Validate...", "Add...") |
| **Negation without alternative** ("Don't use X") | Agent knows what NOT to do but not what TO do | Always provide a concrete alternative |
| **Flat lists without hierarchy** | Relationships between concepts are lost | Use indented structure (Rule > Detail > Example) |

---

## Skill Size Guidelines

| Skill Type | SKILL.md Lines | References |
|------------|----------------|------------|
| Focused (single topic) | 100-200 | Optional |
| Standard (domain area) | 200-350 | 1-3 files |
| Comprehensive (full guide) | 300-400 | 3-6 files |

### If SKILL.md > 400 lines
1. Extract detailed examples to references/
2. Keep only WRONG/CORRECT pairs in SKILL.md
3. Consider splitting into multiple skills

---

## Checklist for New Skills

### 🔴 BLOCKING
- [ ] Defined 2-3 concrete use cases before writing
- [ ] YAML frontmatter with `name` and `description`
- [ ] Description includes trigger phrases ("Use when...")
- [ ] Description under 1024 characters, no XML tags
- [ ] Sections use "When X" naming
- [ ] Severity markers (🔴/🟡/🟢) on rules
- [ ] WRONG/CORRECT code examples
- [ ] Inline references (📚) at section start
- [ ] Instructions use imperative mood
- [ ] Every negation includes a concrete alternative
- [ ] Content uses hierarchical indented structure (Section > Rule > Detail)

### 🟡 WARNING
- [ ] Trigger tests pass (should/should NOT trigger)
- [ ] No duplicate content between SKILL.md and references
- [ ] SKILL.md under 400 lines
- [ ] Quick reference tables for common lookups
- [ ] No extraneous files (README, CHANGELOG)

### 🟢 BEST PRACTICE
- [ ] Functional tests defined (Given/When/Then)
- [ ] Code Review Checklist at end
- [ ] Examples match target language/framework conventions
- [ ] Progressive disclosure used for large content
- [ ] Negative triggers added if over-triggering risk
