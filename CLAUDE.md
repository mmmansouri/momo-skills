# Momo Skills — Skill Library Cartography
> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Reusable skill library. Skills are bridged into each application via Windows junctions
(`<app>/.claude/skills/<skill> → momo-skills/<package>/<skill>`), so each app sees only
the skills relevant to its stack. Project-specific (one-off) skills still belong in
each project's own `skills/` directory, not here.

## Package Layout

Skills are organized in 4 top-level packages:

```
momo-skills/
├── development/                    # coding skills
│   ├── common-developer/, common-architecture/, common-git/, common-code-reviewer/
│   ├── backend/
│   │   ├── java/                   # common-java-developer/, common-java-jpa/, common-java-testing/
│   │   └── spring/                 # common-spring-boot-config/, common-rest-api/, common-security/, common-liquibase/
│   └── frontend/
│       ├── common-typescript/
│       └── angular/                # common-frontend-angular/, common-frontend-design/, common-frontend-testing/, common-e2e-playwright/
├── specification/                  # spec workflow, content quality, sizing, ADF format
│   └── spec-workflow/, spec-content/, common-story-sizing/, jira-adf/
├── ia/                             # AI/Claude meta-skills
│   └── skill-creator/, initiate-claude/
└── tools/                          # external vendored skills — symlinks, gitignored
    └── pptx/, remotion-best-practices/
```

When you add a skill, place it under the smallest package that scopes its language /
framework / domain — that determines which apps will receive it through their junction
bridges.

🟡 `tools/` entries are vendored Anthropic skills synced from `~/.agents/skills`.
Do NOT edit them or reformat them to this library's conventions — changes would be
lost on sync and they follow upstream structure.

## Naming Convention

🔴 Skill names are kebab-case and MUST match their folder name. Generic reusable
skills are prefixed `common-` (e.g. `common-java-testing`); project deltas live in
the project's own repo prefixed with the project name (e.g. `buy-nature-git`).
Meta/spec skills use their plain topic name (`skill-creator`, `spec-content`).
**Why:** the description — not the name — is the triggering mechanism; the name's
job is stable identity across junctions, indexes, and cross-skill pointers.

## 🔴 Maintenance Rules

### Before Adding Content
1. Search existing content in the target skill to avoid duplication
   - `grep -r "keyword" skill-name/`
2. Check `references/` too — content may already exist there

### When a Skill Grows Past 400 Lines
1. Warn the user: the hard limit is **500 lines** (`skill-creator` is the SSOT).
2. Propose moving detail to `references/` or, if the skill covers two distinct
   domains, splitting it into multiple single-domain skills.

### Before Creating a New Skill
1. Verify no existing skill covers the topic

### When Renaming or Deleting a Skill
1. Warn the user about the related skills or references
2. Update every junction and cross-skill pointer that targets it

## Writing Conventions

Follow `skill-creator` as the single source of truth for all authoring rules. Key reminders:

- Description = the trigger: third person, pushy, trigger phrases, under 1024 chars.
- Sections use "When X" naming; rules carry 🔴/🟡/🟢 markers; every 🔴 has a `**Why:**` line.
- Reference call-outs use `📚 **When <trigger> → read [ref](references/ref.md).**` — trigger first.
- References stay one level deep from SKILL.md (no ref→ref chains); content lives in
  SKILL.md OR references/, never both.
