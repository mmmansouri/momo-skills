---
name: skill-creator
description: >-
  Guide for creating and/or reviewing AI agent skills. Use when: (1) creating a new SKILL.md
  file, (2) editing, reviewing or rewriting an existing SKILL.md, (3) writing or fixing skill
  frontmatter (name, description), (4) creating references/ files for a skill,
  (5) auditing or reviewing skill quality, (6) adding severity markers or restructuring
  skill sections. Triggers on any work involving files in a skills/ directory.
  Contains structure templates, naming conventions, severity markers, and anti-patterns.
---

# Skill Creator Guide
> **Severity Levels:** 🔴 BLOCKING | 🟡 WARNING | 🟢 BEST PRACTICE

> **Goals:** 
>- Create skills that agents can **apply immediately**, not just read.
>- Review skills for **actionability, clarity, optimization and maintainability**.

> **Algorithm Overview**
>
> **Creating a new skill** — follow `When Starting a New Skill` in this exact order :
> 1. Capture Intent
> 2. Interview & Research
> 3. Define Use Cases
> 4. Build Evaluations
> 5. Write SKILL.md
> 6. Test the Skill
>
> **Reviewing or auditing an existing skill** — skip the creation flow ; check the skill against these points (full details of each points is the dedicated sections below):
> 1. Skill Description Rules
> 2. Skill Content Rules
> 3. Define the Output Contract
> 4. Writing Style
> 5. Section Naming
> 6. Severity Markers
> 7. Explain the Why
> 8. Bundled scripts well built — see `## When Bundling Scripts` + `references/scripts-guide.md`
> 9. Anti-Patterns
> 10. Size — under 500 lines (`## Skill Size Guidelines`)
> 11. Checklist for New Skills (final cross-check)
> 12. Core Principles (Concise / Degrees of Freedom / Progressive Disclosure / Lack of Surprise)
> 13. Test Coverage — see `## When Testing Skills`
> 14. File hygiene — no orphan files in `references/` / `scripts/` / `assets/` ; references one level deep from SKILL.md
>
> **Bundling scripts** with the skill — also load `When Bundling Scripts` and its `scripts-guide.md` reference.

---

## Core Principles

### 🔴 Concise is Key

The context window is a **public good**. Claude is already very smart — only add context it doesn't already have.

Challenge each piece of information:
- "Does Claude really need this explanation?"
- "Does this paragraph justify its token cost?"

✅ **Prefer concise examples over verbose explanations.**

### 🔴 Set Appropriate Degrees of Freedom

- **High freedom**
  - *Use when* : multiple approaches valid, context-dependent
  - *Format* : text instructions
- **Medium freedom**
  - *Use when* : preferred pattern exists, some variation OK
  - *Format* : pseudocode with parameters
- **Low freedom**
  - *Use when* : operations fragile, consistency critical
  - *Format* : specific scripts, few params

### 🔴 Progressive Disclosure

Three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — When skill triggers (<5K words ideal)
3. **Bundled resources** — As needed by Claude (unlimited via file reads)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Keep SKILL.md focused. Move detailed docs to `references/` and link at section start with 📚.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents
- **Keep references one level deep from SKILL.md.** Nested links (SKILL.md → A.md → B.md) cause Claude to preview deeper files with `head -100` and miss content. Every reference must be linkable directly from SKILL.md.
- **Add a Table of Contents to any reference file >100 lines.** Claude often previews long files; without a TOC, scope is invisible.

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

### 🔴 Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

### Composability

Skills can load simultaneously. Design yours to work alongside others — don't assume it's the only capability available.

---

## When Starting a New Skill

Follow these steps in order. Each step prevents a failure mode in later steps.

### Step 1 — 🔴 Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

**Why** : without explicit intent capture, the skill encodes the agent's *interpretation* of the request rather than the user's actual need. The gap surfaces only at use time, when the skill misfires.

### Step 2 — 🔴 Interview & Research

Proactively ask about : edge cases, I/O formats, example files, success criteria, dependencies. Wait to write test prompts until this is ironed out.

Check available MCPs and similar existing skills — research in parallel via subagents when possible, otherwise inline. Come back with context, don't burden the user.

### Step 3 — 🔴 Define Use Cases

Define **2-3 concrete use cases** :

```
Use Case: [Name]
Trigger: User says "[specific phrases]"
Steps:
1. [Action]
2. [Action]
Result: [What success looks like]
```

For each use case, identify :
- **Scripts** needed (deterministic operations)
- **References** that save rediscovery (schemas, docs, domain knowledge)
- **Assets** for output (templates, icons)

### Step 4 — 🔴 Build Evaluations BEFORE Writing the Skill

Eval-driven development prevents skills that solve imagined problems.

1. Run Claude on representative tasks **without** the skill — log specific failures.
2. Build ≥3 eval scenarios from the gaps observed.
3. Establish a baseline (Claude vanilla score against the rubric).
4. Write the **minimal** SKILL.md needed to pass the evals.
5. Iterate against the baseline ; stop when marginal gains plateau.

**Why** : without baselines, skill quality is invisible — you can't tell if content adds value or is just decoration.

### Step 5 — 🔴 Write the SKILL.md

Based on the user interview, fill in these components :

- **name**:  kebab-case, **gerund form** (verb + -ing), must match folder name
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

#### Skill directory Structure

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

🔴 **Content in SKILL.md OR references/, not both.**

### Step 6 — 🔴 Test the Skill

📚 **See section** : `When Testing Skills` (below) for full test patterns (Trigger / Functional / Multi-model / Claude A-B).

**Iteration loop** :
1. Run tests (Trigger first ; then Functional / Multi-model / Claude A-B as applicable).
2. On failure → diagnose the gap → return to Step 5 to refine SKILL.md.
3. Re-run failing tests.
4. Stop when all 🔴 Trigger Tests pass AND the skill matches or beats the Step 4 baseline.

**Why** : without explicit post-write validation, skills ship with under-/over-triggering bugs that surface only at use-time, when the cost of fixing them is highest.

---

## Skill Writing rules

### 🔴 Skill Description Rules
- Write in third person ("Processes…", "Generates…") : Write in third person ("Processes…", "Generates…")
- Include trigger phrases users would say : Claude matches description to user input
- Add negative triggers ("Do NOT use for...") if needed : Prevents over-triggering
- Under 1024 characters : Hard limit
- No XML tags (`<` `>`) : Security: frontmatter appears in system prompt

#### 🔴**Combat under-triggering with a pushy description**
Claude tends to *not* load skills when they would actually be useful. Counter this with explicit context-of-use phrasing. **Why** : the description is the only signal Claude has at trigger-time. A neutral description loses to silence ; a pushy one loads the skill in adjacent contexts where it would help.

### 🔴 Skill Content Rules

- Workflow-oriented sections ("When X"): agent knows WHEN to apply, not just WHAT exists
- Use severity markers so agent prioritizes blocking issues first
- Provide WRONG/CORRECT examples: agent recognizes patterns to fix
- Inline references (📚 at section start): agent finds details without scrolling
- Critical instructions at top: agent reads top-down; buried rules get missed
- **Use `CRITICAL:` or `## Important` headers** — visual priority
- **Use scripts for deterministic validation** — code is deterministic, language interpretation isn't
- **Be specific, not ambiguous:**
- "Use When" descriptions for patterns : agent knows when to apply, not just that the pattern exists
- Use Quick reference tables for fast lookup during coding, no need to re-read paragraphs
- No duplication: content must in either SKILL.md OR references, not both: saves tokens, prevents stale content

### 🔴 Define the Output Contract

If your skill **produces, transforms, or audits content** (validators, generators, reviewers, extractors), define the exact form of output:

- **Schema** — e.g., JSON envelope `{value, source, confidence, errors: []}`
- **Template** — fixed markdown structure with named sections
- **Worked example** — input → command → exact output

Add an `## Output Format` section to SKILL.md OR document the schema in `references/output-schema.md`.

**Why** : without an explicit contract, agents drift toward inconsistent outputs. The contract is what makes the skill's output reusable downstream.

### 🔴 Writing Style

**Imperative mood** — Write all instructions as direct commands.
**Negation with alternative** — Every negation ("Don't", "Never", "Avoid") must include a concrete alternative. If the right alternative is unclear, ask the user before deciding.
**Hierarchical indented structure** — Organize instructions as Section > Subsection > Rule > Detail > Example. Flat lists lose relationships between concepts.


### 🔴 Section Naming

Use "When X" Format, not generic labels. This tells the agent WHEN to apply the rules, not just WHAT the rules are.

```markdown
## When Writing New Code       # ✅ Actionable
## When Handling Exceptions    # ✅ Tells agent WHEN to apply
## Best Practices              # 🔴 WRONG — too vague
## Overview                    # 🔴 WRONG — agent skips this
```

### 🔴 Severity Markers

Use these to signal which rules are non-negotiable, which are important but not deal-breakers, and which are nice-to-haves. This helps the agent prioritize what to fix when applying the skill.

- 🔴 **BLOCKING**
  - *Meaning* : fails code review, must fix
  - *Agent behavior* : fixes BEFORE other work
- 🟡 **WARNING**
  - *Meaning* : should fix, not blocking
  - *Agent behavior* : fixes if time permits
- 🟢 **BEST PRACTICE**
  - *Meaning* : recommended improvement
  - *Agent behavior* : applies when writing new code

### 🔴 Explain the Why

Every 🔴 BLOCKING rule MUST be followed by a one-line `**Why:**` justification anchored in domain reasoning.

```markdown
# 🔴 WRONG — rule without rationale
### 🔴 BLOCKING — Reject titles ending with a period
- Treat as validation error

# ✅ CORRECT — rule with Why
### 🔴 BLOCKING — Trailing period is a warning, not an error
**Why** : Conventional Commits 1.0 doesn't prohibit it normatively. Failing on style would reject spec-compliant titles.
- Treat as warning; don't fail validation
```

The `Why:` forces the agent applying your skill to reason about the domain *before* applying the rule. Without it, rigid rules propagate to contexts where they shouldn't.


---

## When Bundling Scripts

📚 Load the following reference when your skill includes scripts that the agent needs to execute as part of the workflow. This ensures the agent knows how write, run and validate them and what to expect : [scripts-guide.md](references/scripts-guide.md)

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

### 🔴 Functional Tests

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

### 🟡 Test Across Models

Run the skill against every model that may load it :

- **Haiku** — does it have enough guidance to act?
- **Sonnet** — are instructions clear and efficient?
- **Opus** — is the skill over-explaining things Opus already knows?

Skills tuned only for Opus often under-guide Haiku.

### 🟡 Iterate with Claude A / Claude B

- **Claude A** (skill author session) — uses your domain context to draft and refine the skill.
- **Claude B** (fresh session, skill loaded) — executes real tasks; reveals gaps.
- Loop : observe Claude B failure → bring back to Claude A with the specific failure → refine SKILL.md → re-test.

**Why** : Claude A can't see its own blind spots. Claude B's behavior on real tasks is the only ground truth.

### Iteration Signals

- **Skill doesn't load when it should**
  - *Problem* : under-triggering
  - *Fix* : add keywords and trigger phrases to description
- **Users manually enabling it**
  - *Problem* : under-triggering
  - *Fix* : add more "Use when" variations
- **Skill loads for unrelated queries**
  - *Problem* : over-triggering
  - *Fix* : add negative triggers ("Do NOT use for..."), be more specific
- **Inconsistent results**
  - *Problem* : execution issue
  - *Fix* : improve instructions, add error handling, use scripts
- **Responses degraded / slow**
  - *Problem* : context too large
  - *Fix* : move content to references/, keep SKILL.md under 5K words

---

## SKILL.md Reference Example

Use **this very file** (`skill-creator/SKILL.md`) as the canonical example to mimic. It demonstrates : frontmatter, severity tiers, "When X" sections, WRONG/CORRECT examples, Output Contract rule, Anti-Patterns list, Checklist. Read its structure, copy its patterns.

---

## Anti-Patterns

- **Information dump** (500 lines of prose)
  - *Why it fails* : agent gets lost, skips content
  - *Fix* : use tables, bullets, WRONG/CORRECT pairs
- **No priority indicators**
  - *Why it fails* : everything looks equally important
  - *Fix* : add 🔴/🟡/🟢 severity markers
- **References only at bottom**
  - *Why it fails* : agent doesn't see link until too late
  - *Fix* : put 📚 at section start
- **Duplicate content** (SKILL.md AND references/)
  - *Why it fails* : wasted tokens, content drifts apart
  - *Fix* : content in ONE place only
- **Generic section names** ("Best Practices")
  - *Why it fails* : agent doesn't know when to apply
  - *Fix* : use "When X" naming
- **Vague instructions** ("validate properly")
  - *Why it fails* : Claude interprets loosely
  - *Fix* : be specific, use scripts
- **Passive/conditional voice** ("You should...", "It is recommended...")
  - *Why it fails* : agent treats it as optional, not mandatory
  - *Fix* : use imperative mood ("Validate...", "Add...")
- **Negation without alternative** ("Don't use X")
  - *Why it fails* : agent knows what NOT to do but not what TO do
  - *Fix* : always provide a concrete alternative
- **Flat lists without hierarchy**
  - *Why it fails* : relationships between concepts are lost
  - *Fix* : use indented structure (Rule > Detail > Example)
- **Windows-style paths** (`scripts\helper.py`)
  - *Why it fails* : breaks on Unix ; Claude often runs in Linux sandbox
  - *Fix* : always forward slashes (`scripts/helper.py`)
- **Time-sensitive content** ("after August 2025…")
  - *Why it fails* : becomes wrong silently
  - *Fix* : move legacy details into a `## Old patterns` section with `<details>` collapsibles
- **Inconsistent terminology** (alternating "endpoint" / "URL" / "path")
  - *Why it fails* : pattern matching fails when wording drifts
  - *Fix* : pick one term per concept and keep it everywhere
- **Too many options** ("use X or Y or Z…")
  - *Why it fails* : decision paralysis, agent picks randomly
  - *Fix* : provide a default + one escape hatch ("Use X. For edge case Y, use Z")

---

## Skill Size Guidelines

- **Focused** (single topic) — 100–200 lines ; references optional
- **Standard** (domain area) — 200–350 lines ; 1–3 reference files
- **Comprehensive** (full guide) — 300–500 lines ; 3–6 reference files

### If SKILL.md > 500 lines
1. Extract detailed examples to references/
2. Keep only WRONG/CORRECT pairs in SKILL.md
3. Consider splitting into multiple skills

---

## Checklist for New Skills

### 🔴 BLOCKING
- [ ] Built ≥3 evaluations BEFORE writing the skill, with a baseline
- [ ] Defined 2-3 concrete use cases before writing
- [ ] YAML frontmatter with `name` and `description`
- [ ] Description written in **third person** ("Processes…", not "I can…")
- [ ] Description includes trigger phrases ("Use when...")
- [ ] Description under 1024 characters, no XML tags
- [ ] Sections use "When X" naming
- [ ] Severity markers (🔴/🟡/🟢) on rules
- [ ] WRONG/CORRECT code examples
- [ ] Inline references (📚) at section start
- [ ] **References one level deep from SKILL.md** (no nested chains)
- [ ] Reference files >100 lines have a Table of Contents
- [ ] Instructions use imperative mood
- [ ] Every negation includes a concrete alternative
- [ ] Content uses hierarchical indented structure (Section > Rule > Detail)
- [ ] Every 🔴 BLOCKING rule has a `**Why:**` line anchored in domain reasoning
- [ ] Output contract defined (schema/template/worked example) if skill produces content
- [ ] End-to-end Input→Output example included (not only rule-level WRONG/CORRECT)
- [ ] If skill bundles scripts: each handles errors explicitly + no voodoo constants + execute-vs-read intent stated
- [ ] If skill bundles a validator script: tested against ≥5 spec-cited examples (positive + negative)
- [ ] If skill is an audit/review skill: leads with single deepest defect (not flat enumeration)
- [ ] Trigger tests pass (should/should NOT trigger)

### 🟡 WARNING
- [ ] Tested with **Haiku, Sonnet, AND Opus**
- [ ] No duplicate content between SKILL.md and references
- [ ] SKILL.md under 500 lines
- [ ] Quick reference tables for common lookups
- [ ] **Forward slashes in all paths** (no `\`)
- [ ] No time-sensitive references in the body (legacy → `## Old patterns` w/ `<details>`)
- [ ] Consistent terminology throughout (one term per concept)
- [ ] No "too many options" — provide a default + one escape hatch
- [ ] MCP tool refs use fully qualified `ServerName:tool_name`
- [ ] No extraneous files (README, CHANGELOG)

### 🟢 BEST PRACTICE
- [ ] Functional tests defined (Given/When/Then)
- [ ] Iterated using Claude A / Claude B loop
- [ ] Code Review Checklist at end
- [ ] Examples match target language/framework conventions
- [ ] Progressive disclosure used for large content
- [ ] Negative triggers added if over-triggering risk
