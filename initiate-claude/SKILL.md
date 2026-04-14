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

1. Scan the project structure (`ls`, `glob`) to identify layers, packages, and entry points
2. Read key files: main config, routing, module declarations, `package.json` or `pom.xml`
3. Identify startup profiles/modes from config files, scripts, and environment variables
4. If a CLAUDE.md already exists, read it first and merge updates — preserve existing useful content instead of overwriting blindly

### 🔴 Generate Exactly These 2 Sections

Every CLAUDE.md produced by this skill contains these sections in order:

1. **Simplified Architecture** (`## Architecture`)
2. **Startup Modes** (`## Startup Modes`)

### 🔴 Load Assets by Stack

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

📄 **Asset:** `assets/{stack}/architecture-tree.md` — template + adaptation rules for the detected stack

---

## Section 2 — Startup Modes

One table listing every detected profile/mode with: Mode, Command, Description, Specifics (DB, mocks, seeds).
- Detect all profiles from: Spring `application-*.yml`, Angular `environment.*.ts`, Docker Compose files, `package.json` scripts
- Include every detected profile, even if undocumented
- 🔴 Detect application booting commands or scripts for each mode. Ask the user if any are missing or if you have any doubts about the correct command

📄 **Asset:** `assets/{stack}/startup-modes.md` — table template with detection checklist

---

## Constraints

### 🔴 Size Target
- Sections 1 and 2 combined: **< 200 lines**
  - If the project is too large, increase granularity (group by sub-domain) instead of exceeding the limit

### 🔴 Content Rules
- Use standard markdown only (headings `##`, tables, code blocks)
- Write summaries, not source code copies
  - Extract role and purpose from reading the code, then describe in your own words
- If a section already exists in the CLAUDE.md, merge updates without losing existing useful content
  - 🔴 Replace outdated information instead of appending duplicates

---

## Checklist

### 🔴 BLOCKING
- [ ] Read the project structure before generating content
- [ ] All 2 sections present in the output
- [ ] Architecture tree matches the real project structure
- [ ] Startup modes table includes all detected profiles
- [ ] Total sections 1-2 under 200 lines

### 🟡 WARNING
- [ ] Existing CLAUDE.md content preserved where still valid
- [ ] No source code copied — summaries only
- [ ] Tables use consistent column format
