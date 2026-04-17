# Startup Modes — Spring Boot / Java Backend

Stack-specific detection + example. Format rules (structured list, no tables, no anchors, per-mode template) are in `SKILL.md` Section 2.

## Detection Checklist

- Read every `application-*.yml` / `application-*.properties` — one mode per Spring profile
- Scan `docker-compose*.yml` / `compose.*.yml` for containerized modes
- Check `pom.xml` for `spring-boot-maven-plugin` run configurations and Maven profiles
- Check project root for `Makefile`, `*.sh`, or README-documented run commands
- Note which profiles use H2 vs PostgreSQL, which enable mocks vs real external services
- 🔴 Confirm each booting command with the user if uncertain

## Typical Field Values for Java/Spring

- **Category**: `dev` | `local` | `test` | `staging` | `prod` | `script`
- **Command patterns**: `./mvnw spring-boot:run -Dspring-boot.run.profiles=<name>` · `docker compose up` · `./mvnw test` · `docker run -e SPRING_PROFILES_ACTIVE=<name> <image>`
- **Env required** (typical): `SPRING_PROFILES_ACTIVE`, `SPRING_DATASOURCE_URL`, `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`
- **Notes** (typical): DB engine (H2/Postgres), mocks enabled/disabled, seed data, Flyway/Liquibase migration behavior

## Concrete Example

```markdown
**Globals** — cwd: `<project-root>` · active profile via `SPRING_PROFILES_ACTIVE` · DB host pattern: `postgres:5432`.

### dev
- **Category**: dev
- **Command**: `./mvnw spring-boot:run -Dspring-boot.run.profiles=dev`
- **Purpose**: Local development with hot reload
- **When**: day-to-day coding
- **Notes**: H2 in-memory, seed data loaded at startup, mocks enabled for external APIs
```
