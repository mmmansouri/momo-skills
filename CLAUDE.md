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

## Boundary Map — Where to Route Updates

Use this table when adding or modifying content. Route to the first matching skill.

### "Where does this go?"

| Topic | Route to | Not to |
|---|---|---|
| SOLID, DRY, KISS, YAGNI | `common-developer` | `common-architecture` |
| Hexagonal, CQRS, DDD, ADRs | `common-architecture` | `common-developer` |
| Test strategy (what to test, coverage) | `common-developer` | `common-*-testing` |
| JUnit/Mockito/AssertJ patterns | `common-java-testing` | `common-developer` |
| Jasmine/Angular Testing Library | `common-frontend-testing` | `common-developer` |
| E2E tests, Playwright | `common-e2e-playwright` | `common-frontend-testing` |
| Spring REST controllers, CORS, error handling | `common-rest-api` | `common-security` |
| JWT, OAuth2, RBAC, Spring Security | `common-security` | `common-rest-api` |
| Angular Signals, NgRx, DI | `common-frontend-angular` | `common-typescript` |
| TypeScript generics, utility types | `common-typescript` | `common-frontend-angular` |
| Entity mapping, Hibernate, N+1 | `common-java-jpa` | `common-java-developer` |
| Records, pattern matching, streams | `common-java-developer` | `common-java-jpa` |
| Changelog structure, rollback | `common-liquibase` | `common-java-jpa` |
| Build execution (`build.py`) | `common-builder` | `common-developer` |
| Build rules (when to build) | `common-developer` Section 7 | `common-builder` |
| Branch naming, commit format, PR | `common-git` | `common-dev-ops` |
| Docker, CI/CD pipelines, K8s | `common-dev-ops` | `common-git` |
| Epic/Story section content | `spec-templates` | `spec-workflow-*` |
| Planning/refinement process | `spec-workflow-*` | `spec-templates` |

## Cross-References Between Skills

Some skills explicitly reference others. Maintain these links when renaming or restructuring.

| Source | References | How |
|---|---|---|
| `common-developer` Section 7 | `common-builder` | Delegates build execution to `build.py` |
| `common-builder` SKILL.md | `common-developer` | Points back to Section 7 for build rules |
| `spec-workflow-*` | `spec-templates` | Loads content guidance during workflow execution |
| `common-code-reviewer` | Stack-specific skills | Loads review criteria from agent's skill list |

## Writing Conventions

Follow `skill-creator` as the single source of truth for all authoring rules. Key reminders:

### Structure
- Organize sections with "When X" naming (`## When Writing New Code`)
  - Place critical rules at the top of each section
  - Add severity markers: 🔴 BLOCKING → 🟡 WARNING → 🟢 BEST PRACTICE
    - Mark rules that fail code review as 🔴
    - Mark recommendations as 🟢

### Style
- Write all instructions in imperative mood (`Validate input` instead of `You should validate input`)
- Pair every negation with a concrete alternative (`Don't use var. Use const by default, or let when reassignment is needed`)
  - When the right alternative is unclear, ask the user before deciding
- Use hierarchical indented structure (Section > Rule > Detail > Example)
  - Avoid flat bullet lists that lose relationships between concepts. Indent sub-rules under their parent rule

### Content Placement
- Place content in SKILL.md OR `references/`, never both
  - SKILL.md: rules, WRONG/CORRECT pairs, quick-reference tables
  - `references/`: detailed documentation, extended examples, catalogs
- Link references at section start with 📚 (`📚 **References:** [file.md](references/file.md)`)

### Size Targets

| Skill type | SKILL.md lines | References |
|---|---|---|
| Focused (single topic) | 100-200 | Optional |
| Standard (domain area) | 200-350 | 1-3 files |
| Comprehensive (full guide) | 300-400 | 3-6 files |

## Maintenance Rules

### Before Adding Content
1. Check the Boundary Map to identify the target skill
2. Search existing content in the target skill to avoid duplication
   - `grep -r "keyword" skill-name/`
3. Check `references/` too — content may already exist there

### Before Creating a New Skill
1. Verify no existing skill covers the topic (check Boundary Map)
2. Define 2-3 concrete use cases per `skill-creator` guidelines
3. Follow the `common-*` naming convention for reusable skills
4. Add the new skill to the Taxonomy and Boundary Map sections of this file

### When a Skill Exceeds 400 Lines
1. Extract detailed examples and catalogs to `references/`
2. Keep only rules and WRONG/CORRECT pairs in SKILL.md
3. If the skill covers two distinct domains, split it into two skills and update this file

### When Renaming or Deleting a Skill
1. Check the Cross-References table for dependent skills
2. Update all consumer projects that reference this skill in agent frontmatter
3. Update this file (Taxonomy, Boundary Map, Cross-References)
