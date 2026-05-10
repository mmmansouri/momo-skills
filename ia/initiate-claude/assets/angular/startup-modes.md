# Startup Modes — Angular Frontend

Stack-specific detection + example. Format rules (structured list, no tables, no anchors, per-mode template) are in `SKILL.md` Section 2.

## Detection Checklist

- Read `package.json` → `scripts` block — every script is a potential mode
- Read `angular.json` → `projects.<app>.architect.{serve,build,test}.configurations.*`
- Read every `src/environments/environment.*.ts` — one per configuration
- Check `proxy.conf.json` / `proxy.conf.js` for backend proxying
- Check `docker-compose*.yml` if the app is containerized
- Check project root for E2E runners (Playwright, Cypress) — their configs live in `playwright.config.ts` / `cypress.config.ts`
- 🔴 Confirm each booting command with the user if uncertain

## Typical Field Values for Angular

- **Category**: `dev` | `build` | `test` | `e2e` | `serve` | `script`
- **Command patterns**: `npm start` · `ng serve --configuration=<name>` · `npm run build -- --configuration=<name>` · `npm test` · `npm run e2e`
- **Env required** (typical): runtime env vars are rare; configuration lives in `environment.*.ts` files instead
- **Notes** (typical): which `environment.*.ts` is used, proxy config path, output dir (`dist/<app>/`), port, headless/watch mode in CI

## Concrete Example

```markdown
**Globals** — cwd: `<project-root>` · package manager: `npm` · default dev port: `4200` · env files: `environment.*.ts`.

### dev
- **Category**: dev
- **Command**: `npm start` (alias of `ng serve --configuration=development`)
- **Purpose**: Local dev server with live reload
- **When**: day-to-day coding
- **Notes**: uses `environment.ts`; proxy config in `proxy.conf.json` routes `/api` → backend
```
