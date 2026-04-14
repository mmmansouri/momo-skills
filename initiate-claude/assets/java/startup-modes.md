# Startup Modes — Spring Boot / Java Backend

## Table Template

| Mode | Command | Description | Specifics (DB, mocks, seeds…) |
|---|---|---|---|
| `dev` | `./mvnw spring-boot:run -Dspring.profiles.active=dev` | Local development | H2 in-memory, seed data loaded |
| `local` | `docker compose up` | Full local stack | PostgreSQL, no mocks |
| `local-e2e` | `docker compose -f docker-compose.e2e.yml up` | E2E test environment | PostgreSQL, seeded test data |
| `test` | `mvn test` | Unit/integration tests | H2 in-memory, mock services |
| `prod` | `docker run -e SPRING_PROFILES_ACTIVE=prod` | Production | ENV vars for all secrets |

## Detection Checklist

- Check `application-*.yml` / `application-*.properties` for all Spring profiles
- Check `docker-compose*.yml` for containerized modes
- Check `pom.xml` for spring-boot-maven-plugin configuration
- Check project root for Makefile, shell scripts, or README with run commands
- Note which profiles use H2 vs PostgreSQL, mock vs real external services
