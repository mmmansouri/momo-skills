# Momo Skills — Skill Library Cartography

Reusable skill library consumed via symlink (`~/.claude/skills → momo-skills`).
Available to all projects on this machine. Project-specific skills belong in each project's own `skills/` directory, not here.

## Naming Convention

- `common-*` — Reusable across any project
- `spec-*` — Specification and Jira workflow skills
- `skill-creator` — Meta skill for authoring other skills

## Skill Taxonomy

### Backend Java (6 skills)

| Skill | Scope | Boundary |
|---|---|---|
| `common-java-developer` | Java language (17-25): records, pattern matching, sealed classes, streams, Optional | Language-level only. Place framework-specific code (Spring, JPA) in dedicated skills |
| `common-java-jpa` | JPA/Hibernate 6.x, Spring Data JPA 3.x: entities, relationships, queries, caching | Persistence layer only. Place REST endpoints in `common-rest-api` |
| `common-java-testing` | JUnit 5, Mockito, AssertJ: test implementation, mocking patterns, assertions | Test implementation (HOW to write tests). Place test strategy (WHAT to test, coverage) in `common-developer` |
| `common-rest-api` | REST API design + Spring Boot controllers: URIs, HTTP methods, pagination, CORS, error handling, exception handlers | Everything HTTP request/response. Place authentication/authorization in `common-security` |
| `common-security` | Auth/authz only: OWASP, JWT, OAuth2, RBAC, Spring Security config, password hashing | Authentication and authorization exclusively. Place CORS, error responses, and HTTP config in `common-rest-api` |
| `common-liquibase` | Database migrations: changelogs, changesets, rollback, Spring Boot config | Schema evolution only. Place entity mapping in `common-java-jpa` |

### Frontend Angular (4 skills)

| Skill | Scope | Boundary |
|---|---|---|
| `common-frontend-angular` | Angular 17-21 framework: components, Signals, NgRx, routing, forms, HTTP services | Angular-specific APIs. Place language-level TypeScript patterns in `common-typescript` |
| `common-frontend-design` | UI/UX: layouts, typography, color, accessibility, responsive design | Design discipline and visual quality. Place component implementation in `common-frontend-angular` |
| `common-frontend-testing` | Jasmine + Angular Testing Library: component tests, service tests, mock patterns | Test implementation (HOW to write tests). Place test strategy (WHAT to test, coverage) in `common-developer` |
| `common-typescript` | TypeScript 4.x-5.x language: strict mode, generics, utility types, type narrowing, async/await | Language-level only. Place Angular-specific patterns (Signals, DI, decorators) in `common-frontend-angular` |

### Cross-Cutting (8 skills)

| Skill | Scope | Boundary |
|---|---|---|
| `common-developer` | Universal dev practices: SOLID, DRY, KISS, YAGNI, Clean Code, test strategy (what/when to test, coverage targets), build validation | Strategy and principles. Place implementation details in stack-specific skills (`common-java-*`, `common-frontend-*`) |
| `common-architecture` | System design: Hexagonal, CQRS, DDD, ADRs, C4 diagrams, trade-off evaluation | Architecture decisions. Place coding principles (SOLID, Clean Code) in `common-developer` |
| `common-agent` | Agent execution standards: tool usage verification, BUILD→UPDATE→VERIFY→REPORT workflow | Agent behavior. Place coding practices in `common-developer` |
| `common-git` | Git workflow: branching, commits, PRs, GitHub App auth | Version control only. Place CI/CD pipelines in `common-dev-ops` |
| `common-code-reviewer` | PR review process: MCP tools, gh CLI, severity markers, thread resolution | Review workflow. Place review criteria in stack-specific skills |
| `common-builder` | Build wrapper scripts (Python): `build.py`, log capture, JSON summary | Build execution (HOW to build safely). Place build rules (WHEN to build) in `common-developer` Section 7 |
| `common-dev-ops` | CI/CD, Docker, Kubernetes, Terraform, GitOps, observability | Infrastructure and deployment. Place application code practices in `common-developer` |
| `common-e2e-playwright` | E2E testing with Playwright: page objects, fixtures, async patterns, CI integration | E2E test implementation. Place unit/integration testing in `common-java-testing` or `common-frontend-testing` |

### Specification (3 skills)

| Skill | Scope | Boundary |
|---|---|---|
| `spec-templates` | Content guidance: WHAT to write in Epic/Story sections (context, scope, ACs) | Content structure. Place ADF formatting in project-level `buy-nature-jira-writer` |
| `spec-workflow-feature-planning` | Feature planning process: Epic creation, story decomposition, user checkpoints | Workflow orchestration. Place section content guidance in `spec-templates` |
| `spec-workflow-story-refinement` | Story refinement process: functional/technical specs, AC writing, E2E companion stories | Workflow orchestration. Place section content guidance in `spec-templates` |

### Meta (1 skill)

| Skill | Scope |
|---|---|
| `skill-creator` | Skill authoring guide: structure, frontmatter, severity markers, anti-patterns, testing |

## 🔴 Maintenance Rules

### Before Adding Content
1. Check the Boundary Map to identify the target skill
2. Search existing content in the target skill to avoid duplication
   - `grep -r "keyword" skill-name/`
3. Check `references/` too — content may already exist there

### 🔴 When a Skill Exceeds 400 Lines
1. Warn the user and propose splitting the skill into focused sub-skills,
2. If the skill covers two distinct domains, split it into two skills and update this file

### 🔴 Before Creating a New Skill
1. Verify no existing skill covers the topic (check Boundary Map)

### 🔴 When Renaming or Deleting a Skill
1. Check the Cross-References table for dependent skills
2. Warn the user about the related skills or references,
2. Update all consumer projects that reference this skill in agent frontmatter
3. Update this CLAUDE.md: remove or rename in Taxonomy, Boundary Map, and Cross-References

### When Adding Agent (in a consumer project)
1. Check the Taxonomy to select the correct skills for the agent's frontmatter
2. Update this CLAUDE.md Cross-References table if the agent introduces a new inter-skill dependency

### 🔴 CLAUDE.md Update Is Mandatory
Every change to the skill library (create, rename, delete, split, merge, new cross-reference) requires a corresponding update to this file. Treat a skill change without a CLAUDE.md update as incomplete work.
