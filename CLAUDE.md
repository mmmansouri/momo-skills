# Momo Skills — Skill Library Cartography
> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

Reusable skill library consumed via symlink (`~/.claude/skills → momo-skills`).
Available to all projects on this machine. Project-specific skills belong in each project's own `skills/` directory, not here.

## Naming Convention

🔴  Use gerund form (verb + -ing) for Skill names, as this clearly describes the activity or capability the Skill provides.

## 🔴 Maintenance Rules

### Before Adding Content
1. Search existing content in the target skill to avoid duplication
   - `grep -r "keyword" skill-name/`
2. Check `references/` too — content may already exist there

### 🔴 When a Skill Exceeds 400 Lines
1. Warn the user and propose splitting the skill into focused sub-skills,
2. If the skill covers two distinct domains propose to the user to split it into multiple skills, each focused on a single domain.

### 🔴 Before Creating a New Skill
1. Verify no existing skill covers the topic

### 🔴 When Renaming or Deleting a Skill
2. Warn the user about the related skills or references


## Writing Conventions

Follow `skill-creator` as the single source of truth for all authoring rules. Key reminders:
