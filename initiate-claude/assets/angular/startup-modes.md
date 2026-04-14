# Startup Modes — Angular Frontend

## Table Template

| Mode | Command | Description | Specifics |
|---|---|---|---|
| `dev` | `ng serve` | Dev server with HMR | API proxy to localhost:8080 |
| `prod build` | `ng build --configuration=production` | Production build | Optimized, AOT compiled |
| `e2e` | `npx playwright test` | E2E tests | Against running dev server |

## Detection Checklist

- Check `angular.json` → `projects.*.architect.build.configurations` for build configurations
- Check `package.json` → `scripts` for serve/build/test commands
- Check `proxy.conf.json` or `proxy.conf.js` for API proxy configuration
- Check `src/environments/` for environment files
- Check project root for Docker Compose files, Makefile, or README with run commands
