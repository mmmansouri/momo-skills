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
├── specification/                  # SDD workflow & templates
│   └── spec-templates/, spec-workflow-feature-planning/, spec-workflow-story-refinement/
├── ia/                             # AI/Claude meta-skills
│   └── skill-creator/, initiate-claude/
└── tools/                          # external tool symlinks (gitignored)
    └── pptx/, remotion-best-practices/
```

When you add a skill, place it under the smallest package that scopes its language /
framework / domain — that determines which apps will receive it through their junction
bridges.

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
