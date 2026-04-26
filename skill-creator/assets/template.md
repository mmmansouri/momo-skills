# SKILL.md Template

Copy this scaffold when starting a new SKILL.md. The template encodes the structure rules from `../SKILL.md` (severity markers, "When X" sections, BLOCKING/WARNING/BEST PRACTICE tiers, WRONG/CORRECT examples, Code Review Checklist).

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
    ```language
    // example code
    ```

### 🟡 WARNING
- Warning 1
  - Detail or context

### 🟢 BEST PRACTICE
- Recommendation 1

### Examples

Rule-level WRONG/CORRECT pair:

```language
// 🔴 WRONG - explanation
bad_code();

// ✅ CORRECT - explanation
good_code();
```

End-to-end Input → Process → Output trace (mandatory if the skill produces content):

**Input prompt** : "[realistic user request]"
**Process**     : [steps the skill drives]
**Output**      :
```
[exact output the skill produces]
```

---

## Output Format

[If your skill produces, transforms, or audits content, define the schema/template here. Required by `When Writing Instructions → Define the Output Contract` rule.]

---

## Code Review Checklist

### 🔴 BLOCKING
- [ ] Item 1

### 🟢 BEST PRACTICE
- [ ] Item 2
```

## Adapting the Template

- **Validator/linter skills** : add a section per `../SKILL.md → When Building Validator/Linter Skills` (RFC 2119 mapping, spec-cited test examples).
- **Audit/review skills** : the audit output should LEAD with the single deepest defect; cap findings at ≤10 distinct issues. See `../SKILL.md → When Auditing or Reviewing Existing Skills`.
- **Multi-domain skills** : split when >400 lines or when covering 2+ distinct domains (per project CLAUDE.md).
