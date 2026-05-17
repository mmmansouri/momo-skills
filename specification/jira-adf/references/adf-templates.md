# ADF Templates for Jira Cloud REST API

> Ready-to-fill ADF (Atlassian Document Format) JSON for Epics, Stories, comments,
> linking, and the most common building blocks. Send these structures to the Jira
> Cloud REST API — they will render correctly. Markdown is **not** accepted.

## Table of Contents

1. [ADF Basics](#1-adf-basics)
2. [Node Types Quick Reference](#2-node-types-quick-reference)
3. [Full Marks Reference](#3-full-marks-reference)
4. [Building Blocks: Heading / Paragraph / Bullet / Rule](#4-building-blocks-heading--paragraph--bullet--rule)
5. [Building Blocks: Table](#5-building-blocks-table)
6. [Building Blocks: Panel](#6-building-blocks-panel)
7. [Building Blocks: Code Block / Inline Code](#7-building-blocks-code-block--inline-code)
8. [Building Blocks: Link / Ordered List](#8-building-blocks-link--ordered-list)
9. [Template: Create a New User Story](#9-template-create-a-new-user-story)
10. [Template: Update US Description Only](#10-template-update-us-description-only)
11. [Template: Link Issues](#11-template-link-issues)
12. [Epic Description Template](#12-epic-description-template)
13. [Draft Story Template](#13-draft-story-template)
14. [Refined Story Template](#14-refined-story-template)
15. [E2E Companion Story Template](#15-e2e-companion-story-template)
16. [AC Block Template](#16-ac-block-template)
17. [Priority Values](#17-priority-values)

---

## 1. ADF Basics

Every ADF document has the same root:

```json
{
  "type": "doc",
  "version": 1,
  "content": [ ... ]
}
```

The `content` array holds top-level nodes (headings, paragraphs, tables, panels…). Never wrap your content in another `doc` node.

---

## 2. Node Types Quick Reference

| ADF Type | Renders As | Use For |
|---|---|---|
| `heading` (level 2) | **H2** | Section titles (Context, Acceptance Criteria) |
| `heading` (level 3) | **H3** | AC titles (AC1: Feature name) |
| `paragraph` | Text block | Regular text content |
| `bulletList` > `listItem` | Bullet list | AC requirements, dependencies |
| `orderedList` > `listItem` | Numbered list | Sequential steps |
| `rule` | Horizontal line | Section separators |
| `table` | Data table | API contracts, breakdowns |
| `panel` | Callout box | Notes, warnings, info |
| `codeBlock` | Code block | Code samples, commands |

---

## 3. Full Marks Reference

| Mark | JSON | Renders As |
|---|---|---|
| Bold | `"marks": [{ "type": "strong" }]` | **Bold** |
| Italic | `"marks": [{ "type": "em" }]` | *Italic* |
| Code | `"marks": [{ "type": "code" }]` | `inline code` |
| Strike | `"marks": [{ "type": "strike" }]` | ~~strikethrough~~ |
| Link | `"marks": [{ "type": "link", "attrs": { "href": "..." } }]` | [hyperlink] |
| Combined | `"marks": [{ "type": "strong" }, { "type": "code" }]` | **`bold code`** |

---

## 4. Building Blocks: Heading / Paragraph / Bullet / Rule

### Heading

```json
{
  "type": "heading",
  "attrs": { "level": 2 },
  "content": [{ "type": "text", "text": "Section Title" }]
}
```

### Paragraph with bold text

```json
{
  "type": "paragraph",
  "content": [
    { "type": "text", "text": "Key term", "marks": [{ "type": "strong" }] },
    { "type": "text", "text": " followed by normal text." }
  ]
}
```

### Bullet list

```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "Item 1" }] }
      ]
    },
    {
      "type": "listItem",
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "Item 2" }] }
      ]
    }
  ]
}
```

### Horizontal rule (section separator)

```json
{ "type": "rule" }
```

### AC with bold title inline (inline `strong` mark)

```json
{
  "type": "listItem",
  "content": [{
    "type": "paragraph",
    "content": [
      { "type": "text", "text": "Field validation", "marks": [{ "type": "strong" }] },
      { "type": "text", "text": " — email format validated, max 255 chars, unique per account" }
    ]
  }]
}
```

---

## 5. Building Blocks: Table

```json
{
  "type": "table",
  "attrs": { "isNumberColumnEnabled": false, "layout": "default" },
  "content": [
    {
      "type": "tableRow",
      "content": [
        {
          "type": "tableHeader",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Column A", "marks": [{ "type": "strong" }] }] }]
        },
        {
          "type": "tableHeader",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Column B", "marks": [{ "type": "strong" }] }] }]
        }
      ]
    },
    {
      "type": "tableRow",
      "content": [
        {
          "type": "tableCell",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Cell value" }] }]
        },
        {
          "type": "tableCell",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Cell value" }] }]
        }
      ]
    }
  ]
}
```

**Rules:**

- Every `tableCell` and `tableHeader` MUST contain at least one `paragraph` node.
- Use `tableHeader` for the first row (renders bold and shaded).
- `layout`: `"default"`, `"wide"`, or `"full-width"`.

---

## 6. Building Blocks: Panel

### Info Panel (blue)

```json
{
  "type": "panel",
  "attrs": { "panelType": "info" },
  "content": [
    {
      "type": "paragraph",
      "content": [{ "type": "text", "text": "Informational message here." }]
    }
  ]
}
```

### Panel Types

| `panelType` | Color | Use for |
|---|---|---|
| `info` | Blue | General information, tips |
| `note` | Yellow | Important notes, "To be refined" markers |
| `warning` | Orange | Caution, potential issues |
| `error` | Red | Critical alerts, blockers |
| `success` | Green | Completed items, confirmations |

---

## 7. Building Blocks: Code Block / Inline Code

### Code Block (fenced)

```json
{
  "type": "codeBlock",
  "attrs": { "language": "java" },
  "content": [
    { "type": "text", "text": "public record ReviewCreationRequest(\n    @NotNull Integer rating,\n    @NotBlank String comment\n) {}" }
  ]
}
```

**Supported languages:** `java`, `typescript`, `json`, `bash`, `sql`, `yaml`, `xml`, `html`, `css`, `text`.

### Inline Code

```json
{
  "type": "text",
  "text": "ReviewController",
  "marks": [{ "type": "code" }]
}
```

---

## 8. Building Blocks: Link / Ordered List

### Link mark

```json
{
  "type": "text",
  "text": "PROJ-XXX",
  "marks": [{
    "type": "link",
    "attrs": { "href": "https://your-org.atlassian.net/browse/PROJ-XXX" }
  }]
}
```

### Ordered List

```json
{
  "type": "orderedList",
  "content": [
    {
      "type": "listItem",
      "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Step 1" }] }]
    },
    {
      "type": "listItem",
      "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Step 2" }] }]
    }
  ]
}
```

---

## 9. Template: Create a New User Story

**Endpoint:** `POST /rest/api/3/issue`

```json
{
  "fields": {
    "project": { "key": "PROJ" },
    "issuetype": { "name": "Story" },
    "summary": "US title here",
    "parent": { "key": "PROJ-XX" },
    "labels": ["backend"],
    "priority": { "name": "Medium" },
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Context" }]
        },
        {
          "type": "paragraph",
          "content": [
            { "type": "text", "text": "Description of current state and why this US is needed." }
          ]
        },
        { "type": "rule" },
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Acceptance Criteria" }]
        },
        {
          "type": "heading",
          "attrs": { "level": 3 },
          "content": [{ "type": "text", "text": "AC1: Feature Name" }]
        },
        {
          "type": "bulletList",
          "content": [
            {
              "type": "listItem",
              "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Requirement 1" }] }]
            },
            {
              "type": "listItem",
              "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Requirement 2" }] }]
            }
          ]
        },
        { "type": "rule" },
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Technical Notes" }]
        },
        {
          "type": "bulletList",
          "content": [
            {
              "type": "listItem",
              "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Implementation hint or constraint" }] }]
            }
          ]
        },
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Dependencies" }]
        },
        {
          "type": "bulletList",
          "content": [
            {
              "type": "listItem",
              "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "PROJ-XX - dependency description" }] }]
            }
          ]
        }
      ]
    }
  }
}
```

---

## 10. Template: Update US Description Only

**Endpoint:** `PUT /rest/api/3/issue/{key}`

```json
{
  "fields": {
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        ...
      ]
    }
  }
}
```

> The `content` array follows the same ADF structure as the creation template. Only the `description` field is sent.

---

## 11. Template: Link Issues

**Endpoint:** `POST /rest/api/3/issueLink`

```json
{
  "type": { "name": "Relates" },
  "inwardIssue": { "key": "PROJ-101" },
  "outwardIssue": { "key": "PROJ-102" }
}
```

Common link types: `Relates`, `Blocks`, `Clones`, `Duplicates`.

---

## 12. Epic Description Template

Full ADF structure for an Epic created by the feature-planning workflow.

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Context" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "Business need and problem statement. Who benefits and why." }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Scope" }]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "In Scope" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Feature or capability included" }] }]
        }
      ]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "Out of Scope" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Explicit exclusion (prevents scope creep)" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Technical Approach" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "Affected components: ", "marks": [{ "type": "strong" }] },
        { "type": "text", "text": "backend, frontend" }
      ]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "High-level architecture description and key technical decisions." }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Story Breakdown" }]
    },
    {
      "type": "table",
      "attrs": { "isNumberColumnEnabled": false, "layout": "default" },
      "content": [
        {
          "type": "tableRow",
          "content": [
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Story", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Labels", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Dependencies", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Parallel?", "marks": [{ "type": "strong" }] }] }] }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Review entity + API endpoints" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "backend" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "None" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Yes" }] }] }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Review list/form components" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "frontend" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "API Story" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "No (needs API)" }] }] }
          ]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Dependencies" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "External system or blocking work" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Open Questions" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Unresolved decision (if any)" }] }]
        }
      ]
    }
  ]
}
```

---

## 13. Draft Story Template

Minimal ADF for stories created during feature-planning (to be refined later).

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Context" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "Part of Epic " },
        { "type": "text", "text": "PROJ-XXX", "marks": [{ "type": "strong" }] },
        { "type": "text", "text": ". Brief description of what this story delivers." }
      ]
    },
    { "type": "rule" },
    {
      "type": "panel",
      "attrs": { "panelType": "note" },
      "content": [
        {
          "type": "paragraph",
          "content": [
            { "type": "text", "text": "Status: To be refined", "marks": [{ "type": "strong" }] },
            { "type": "text", "text": " — This story needs detailed specification before implementation." }
          ]
        }
      ]
    }
  ]
}
```

---

## 14. Refined Story Template

Full ADF structure for a story after refinement workflow.

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Context" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "Part of Epic " },
        {
          "type": "text",
          "text": "PROJ-XXX: Epic Title",
          "marks": [{ "type": "link", "attrs": { "href": "https://your-org.atlassian.net/browse/PROJ-XXX" } }]
        },
        { "type": "text", "text": ". What exists today, why this story is needed." }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Functional Spec" }]
    },
    {
      "type": "paragraph",
      "content": [{ "type": "text", "text": "User-facing behavior and business rules." }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Business rule or data requirement" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Technical Spec" }]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "API Endpoints" }]
    },
    {
      "type": "table",
      "attrs": { "isNumberColumnEnabled": false, "layout": "default" },
      "content": [
        {
          "type": "tableRow",
          "content": [
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Method", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Path", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Request DTO", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Response DTO", "marks": [{ "type": "strong" }] }] }] }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "POST", "marks": [{ "type": "code" }] }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "/api/reviews", "marks": [{ "type": "code" }] }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "ReviewCreationRequest", "marks": [{ "type": "code" }] }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "ReviewRetrievalResponse", "marks": [{ "type": "code" }] }] }] }
          ]
        }
      ]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "Data Model" }]
    },
    {
      "type": "table",
      "attrs": { "isNumberColumnEnabled": false, "layout": "default" },
      "content": [
        {
          "type": "tableRow",
          "content": [
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Field", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Type", "marks": [{ "type": "strong" }] }] }] },
            { "type": "tableHeader", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Constraints", "marks": [{ "type": "strong" }] }] }] }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "rating", "marks": [{ "type": "code" }] }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Integer" }] }] },
            { "type": "tableCell", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "1-5, not null" }] }] }
          ]
        }
      ]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "Component Design (Frontend)" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{
            "type": "paragraph",
            "content": [
              { "type": "text", "text": "ReviewListComponent", "marks": [{ "type": "code" }] },
              { "type": "text", "text": " — displays paginated reviews for a product" }
            ]
          }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Acceptance Criteria" }]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "AC1: Create Review" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "POST /api/reviews with valid payload returns 201" }] }]
        },
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Review is persisted with correct product association" }] }]
        },
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Invalid rating (<1 or >5) returns 400 with validation error" }] }]
        }
      ]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "AC2: List Reviews by Product" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "GET /api/items/{id}/reviews returns paginated reviews" }] }]
        },
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Reviews sorted by creation date (newest first)" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Technical Notes" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Implementation pattern, constraint, or hint" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Out of Scope" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Explicit exclusion" }] }]
        }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Dependencies" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{
            "type": "paragraph",
            "content": [
              { "type": "text", "text": "PROJ-XXX", "marks": [{ "type": "link", "attrs": { "href": "https://your-org.atlassian.net/browse/PROJ-XXX" } }] },
              { "type": "text", "text": " — Blocking story description" }
            ]
          }]
        }
      ]
    }
  ]
}
```

---

## 15. E2E Companion Story Template

ADF structure for E2E test stories linked via "Relates".

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Context" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "E2E test coverage for " },
        {
          "type": "text",
          "text": "PROJ-YYY: Source Story Title",
          "marks": [{ "type": "link", "attrs": { "href": "https://your-org.atlassian.net/browse/PROJ-YYY" } }]
        },
        { "type": "text", "text": ". Validates user-facing behavior through end-to-end tests." }
      ]
    },
    { "type": "rule" },
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Test Scenarios" }]
    },
    {
      "type": "heading",
      "attrs": { "level": 3 },
      "content": [{ "type": "text", "text": "AC1: Scenario Title (maps to source AC1)" }]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Navigate to page, perform action, verify result" }] }]
        },
        {
          "type": "listItem",
          "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Verify error case: invalid input shows error message" }] }]
        }
      ]
    }
  ]
}
```

---

## 16. AC Block Template

A single Acceptance Criterion as an ADF block — drop this into the `content` array of any Story description, repeating with `AC2`, `AC3`, …

```json
[
  {
    "type": "heading",
    "attrs": { "level": 3 },
    "content": [{ "type": "text", "text": "AC1: Descriptive Title" }]
  },
  {
    "type": "bulletList",
    "content": [
      {
        "type": "listItem",
        "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Specific, testable requirement" }] }]
      },
      {
        "type": "listItem",
        "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Error / edge case handling" }] }]
      }
    ]
  }
]
```

### Out of Scope block (frequent companion)

```json
[
  {
    "type": "heading",
    "attrs": { "level": 2 },
    "content": [{ "type": "text", "text": "Out of Scope" }]
  },
  {
    "type": "bulletList",
    "content": [
      {
        "type": "listItem",
        "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Feature X (separate ticket)" }] }]
      }
    ]
  }
]
```

---

## 17. Priority Values

| Name | Use when |
|---|---|
| `Highest` | Critical blocker, system down |
| `High` | Important, affects many users |
| `Medium` | Standard feature work (default) |
| `Low` | Nice-to-have, minor improvement |
| `Lowest` | Cosmetic, can wait indefinitely |
