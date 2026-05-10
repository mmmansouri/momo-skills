# Liquibase Code Review Checklist

> Severity: 🔴 BLOCKING (must fix) · 🟡 WARNING (should fix) · 🟢 BEST PRACTICE.
> Use this checklist when reviewing a PR that adds or modifies Liquibase changesets.

---

## Table of Contents

1. [🔴 BLOCKING — Must Fix Before Merge](#-blocking--must-fix-before-merge)
2. [🟡 WARNING — Should Fix](#-warning--should-fix)
3. [🟢 BEST PRACTICE — Recommended](#-best-practice--recommended)
4. [Reviewer Workflow](#reviewer-workflow)

---

## 🔴 BLOCKING — Must Fix Before Merge

- [ ] **One change per changeset** — no multi-change changesets that auto-commit DDL midway
- [ ] **Rollback provided** — auto-rollback for safe ops (`createTable`, `addColumn`, `createIndex`); explicit `rollback:` block for destructive ops (`dropTable`, `dropColumn`, `insert`, `sql`)
- [ ] **Unique ID + author** — follows `<project>-<entity>-<sequence>-<action>` naming
- [ ] **Master changelog discipline** — only `include` / `includeAll`, no inline changesets
- [ ] **No edits to applied changesets** — new changesets for new behavior; `validCheckSum: any` only for non-functional edits (typo, comment)
- [ ] **Destructive change on live table uses Expand-Contract** — `dropColumn`, `renameColumn`, `NOT NULL`, `ALTER COLUMN TYPE` split across multiple deploys
- [ ] **PostgreSQL index on live table** — `CREATE INDEX CONCURRENTLY` + `runInTransaction: false` (never bare `CREATE INDEX`)
- [ ] **No `runWith: psql`/`sqlplus`/`sqlcmd` in OSS-only deployments** — these are Liquibase Secure features

---

## 🟡 WARNING — Should Fix

- [ ] **Modern attribute names** — `contextFilter` / `labelFilter` (not legacy `context` / `labels`)
- [ ] **Idempotent preconditions** — `tableExists`, `columnExists`, `viewExists` with `onFail: MARK_RAN` where re-runs are possible
- [ ] **No mention of Liquibase Hub** — sunset; redirect to Operations Reports (Secure) or self-hosted log aggregation
- [ ] **No bare `insert` for evolving seed data** — prefer `loadUpdateData` for upsert semantics
- [ ] **`splitStatements: false`** explicitly set when SQL contains `$$` blocks, multi-statement DDL, or PL/pgSQL functions
- [ ] **`endDelimiter` set correctly** for non-standard delimiters in raw SQL changes

---

## 🟢 BEST PRACTICE — Recommended

- [ ] **Group changesets by feature, not by type** — `items/`, `orders/`, not `tables/`, `indexes/`, `foreign-keys/`
- [ ] **Filenames carry `MMYYYY` timestamp** — keeps `includeAll` deterministic
- [ ] **`tag` changeset at release boundaries** — enables `liquibase rollback v2.0`
- [ ] **`loadUpdateData` for seed data** — idempotent upsert by primary key
- [ ] **Rollback exercised in staging** before production deploy
- [ ] **CI runs `validate` + `status` + (Secure) `checks run`** before `update` against the ephemeral DB
- [ ] **`logicalFilePath`** declared when a changeset file was moved or renamed
- [ ] **`modifyChangeSets`** used to factor common attributes (`runWith`, `idPrefix`, `idSuffix`) across imported batches
- [ ] **Comments on changeset** — populated `comment:` field for non-trivial changes (also caught by `ChangesetCommentCheck` policy in Secure)

---

## Reviewer Workflow

1. **Run `liquibase validate`** locally — catches syntax + checksum issues the PR may have introduced
2. **Run `liquibase status --verbose`** — confirms which changesets the PR adds
3. **Run `liquibase update-sql`** — read the generated SQL, look for `ACCESS EXCLUSIVE` operations and full table scans
4. **For destructive PRs**: walk the Expand-Contract sequence in your head — identify which deploy each changeset belongs to
5. **For Secure environments**: confirm `liquibase checks run --check-status=MAJOR` passes locally before approving
