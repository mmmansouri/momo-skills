---
name: initiate-claude
description: >-
  Initialize or update a project's CLAUDE.md with architecture overview, startup
  modes. Use when: bootstrapping a new project's CLAUDE.md.
  Example of triggers: "init CLAUDE.md", "bootstrap CLAUDE.md", "create CLAUDE.md".
  Component cartography belongs in project-specific coding-guide skills, not here.
---

# CLAUDE.md Initialization & Update

> **Goal:** Produce a CLAUDE.md that gives any AI agent instant, accurate context about a project's architecture — without reading every file.

> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

---

## When Initializing or Updating a CLAUDE.md

### 🔴 Read Before Writing

**Why:** A CLAUDE.md written from assumptions instead of the actual files ships wrong layers and dead startup commands — the exact errors this skill exists to prevent.

1. Scan the project structure (`ls`, `glob`) to identify layers, packages, and entry points
2. Read key files: main config, routing, module declarations, `package.json` or `pom.xml`
3. Identify startup profiles/modes from config files, scripts, and environment variables
4. If a CLAUDE.md already exists, read it first and merge updates — preserve existing useful content instead of overwriting blindly

### 🔴 Generate Exactly These 2 Sections

**Why:** A fixed two-section contract keeps every generated CLAUDE.md diffable and predictable, so an agent always knows where to find architecture vs. startup facts.

Every CLAUDE.md produced by this skill contains these sections in order:

1. **Simplified Architecture** (`## Architecture`)
2. **Startup Modes** (`## Startup Modes`)

### 🔴 Load Assets by Stack

**Why:** The tree and startup-mode formats differ per stack; loading the wrong stack's assets produces a CLAUDE.md whose structure does not match how the project actually boots.

After identifying the project's stack (step 2 of "Read Before Writing"), load assets from the matching subdirectory:

- If Spring Boot / Java → read assets from `assets/java/`
- If Angular → read assets from `assets/angular/`

---

## Section 1 — Simplified Architecture

Use an indented tree showing application layers from entry point to storage.
- Each node = group/package name + role in a few words after a dash
  - Adapt the hierarchy to the project's actual structure
  - Show only groups/packages, not individual classes or files
  - Omit layers that don't exist instead of leaving empty placeholders

📚 **When generating the Simplified Architecture tree → read the matching `assets/<stack>/architecture-tree.md` ([java](assets/java/architecture-tree.md) | [angular](assets/angular/architecture-tree.md)).**

---

## Section 2 — Startup Modes

🔴 **Format: structured list** — A structured list with explicit field labels that parses identically across all models.

**Why:** Explicit `**Label**:` fields survive copy-paste and model re-serialization identically, whereas positional or tabular layouts get silently reshuffled from one agent to the next.

Each startup mode gets its own `### <mode-id>` heading followed by labeled bullet fields:

```markdown
### <mode-id>
- **Category**: <pipeline|deploy|script|service|infra|maintenance|bootstrap|introspection>
- **Cwd**: <path>                        (omit if matches project root)
- **Command**: `<exact command with <placeholder> substitutions>`
- **Required flags**: `<flag1>`, `<flag2>`   (omit if none)
- **Env required**: `<VAR1>`, `<VAR2>`       (omit if none)
- **Purpose**: <one line — what it does>
- **When**: <one line — when to invoke>
- **Notes**: <optional — invariants, caveats, side-effects>
```

🔴 **Detection**:

**Why:** An undetected startup mode is an invisible way to run the app; listing every profile — even undocumented ones — is what makes the CLAUDE.md a complete operational map.

- Detect all profiles from: Spring `application-*.yml`, Angular `environment.*.ts`, Docker Compose files, `package.json` scripts, shell scripts (`*.sh`), Dagger functions (`dagger functions`), Makefile targets
- Include every detected profile, even if undocumented
- Detect the exact booting command for each mode. Ask the user if any are missing or uncertain

📚 **When generating the Startup Modes section → read the matching `assets/<stack>/startup-modes.md` ([java](assets/java/startup-modes.md) | [angular](assets/angular/startup-modes.md)).**

---

## Constraints

### 🔴 Size Target

**Why:** CLAUDE.md is loaded into every agent's context; past ~200 lines it stops being an at-a-glance map and starts costing more tokens than reading the code it summarizes.

- Sections 1 and 2 combined: **< 200 lines**
  - If the project is too large, increase granularity (group by sub-domain) instead of exceeding the limit

### 🔴 Content Rules

**Why:** CLAUDE.md is parsed by many different agents; plain markdown plus summaries (never copied source) keeps it renderable everywhere and stops it drifting out of sync with the code.

- Use standard markdown only (headings `##`/`###`, bulleted lists, code blocks)
- 🔴 NO tables in `## Startup Modes` — structured list only (see Section 2)
  - **Why:** Markdown tables truncate and wrap long booting commands and diff poorly line-by-line, so a structured list keeps each command intact and reviewable.
- Write summaries, not source code copies
  - Extract role and purpose from reading the code, then describe in your own words
- If a section already exists in the CLAUDE.md, merge updates without losing existing useful content
  - 🔴 Replace outdated information instead of appending duplicates
    - **Why:** A CLAUDE.md is a single source of truth; stale entries left beside corrected ones make an agent act on facts that no longer hold.

---

## Checklist

### 🔴 BLOCKING
- [ ] Read the project structure before generating content
- [ ] All 2 sections present in the output
- [ ] Architecture tree matches the real project structure
- [ ] Startup Modes uses structured-list format (`### <mode-id>` + labeled bullets) — NO markdown table
- [ ] Every detected profile is included (Spring profiles, Angular configurations, Docker Compose files, npm scripts, shell scripts, Dagger functions)
- [ ] No YAML anchors (`&` / `*`) used anywhere
- [ ] Placeholders in commands use literal `<angle-brackets>`
- [ ] Total sections 1-2 under 200 lines

### 🟡 WARNING
- [ ] Existing CLAUDE.md content preserved where still valid
- [ ] No source code copied — summaries only
- [ ] Empty fields omitted from mode entries
- [ ] Shared defaults factored into a single **Globals** paragraph, not repeated per mode
