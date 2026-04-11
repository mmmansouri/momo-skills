# Output Patterns

Use these patterns when skills need to produce consistent, high-quality output.

## Template Pattern

Provide templates for output format. Match strictness to your needs.

### Strict Template (API responses, data formats)

```markdown
## Report structure

ALWAYS use this exact template:

# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```

### Flexible Template (when adaptation is useful)

```markdown
## Report structure

Here is a sensible default, but use your judgment:

# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on discoveries]

## Recommendations
[Tailor to specific context]

Adjust sections as needed for the analysis type.
```

## Examples Pattern

For skills where output quality depends on seeing examples, provide input/output pairs:

```markdown
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation

Follow this style: type(scope): brief description, then detailed explanation.
```

**Why examples work:** They help Claude understand the desired style and detail level more clearly than descriptions alone.

## Quality Checklist Pattern

For ensuring output meets standards:

```markdown
## Before submitting, verify:

### 🔴 Required
- [ ] All tests pass
- [ ] No console errors
- [ ] Follows naming conventions

### 🟢 Recommended
- [ ] Code is documented
- [ ] Edge cases handled
```
