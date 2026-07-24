---
name: migration-guard
description: Review a database schema migration for production hazards BEFORE it deploys — table locks that freeze traffic, data loss, deploy-order breakage, and irreversible steps. Use whenever the user writes or shows a migration (SQL, Alembic, Django, Rails, Prisma, Drizzle, Laravel…) and is about to ship it, or asks "is this migration safe", "will this lock the table", "can I run this on prod". Trigger on any ALTER TABLE / CREATE INDEX / column drop or type change headed for a database with real data — even if the user only asks you to "write a migration", guard your own output too.
---

# migration-guard

A bad code deploy rolls back in seconds. A bad migration takes a site down mid-deploy, holds a lock while every request queues behind it, or destroys data with no undo. Migrations are the highest-stakes routine change most teams make, and the failure modes are invisible in dev — a lock that's instant on 200 rows is a 10-minute outage on 200 million. Your job: read the migration like the database will execute it in production, and report what will actually happen.

This is a **review**, not a rewrite service. Findings first — each with severity, what happens in prod, and the safe alternative. Only rewrite when asked or when the fix is one line.

## First, establish the blast radius

The same DDL is safe or catastrophic depending on context. Determine (from the code, or ask — these change every verdict):

- **Engine and version** — Postgres, MySQL/InnoDB, SQLite, and MSSQL have completely different locking behavior, and versions matter (e.g. Postgres 11+ makes `ADD COLUMN ... DEFAULT` instant; MySQL 8.0 `INSTANT` ALGORITHM covers some ALTERs).
- **Table size and write traffic** — a lock that rewrites a huge, hot table is the classic outage.
- **Deploy model** — is old code still running while/after the migration runs? (Almost always yes: rolling deploys, or migration-then-deploy.)

## The hazard checklist

Walk the migration against these classes. Report only what applies.

**1. Locks / downtime**
- `CREATE INDEX` without `CONCURRENTLY` (Postgres): full write-lock for the whole build. Concurrent builds can't run inside a transaction — the migration tool needs `atomic = False` / `disable_ddl_transaction!`.
- Full-table rewrites: type changes (`ALTER COLUMN TYPE`), `NOT NULL` on MySQL, volatile defaults on old Postgres — the table is locked while every row is copied.
- `ADD CONSTRAINT ... FOREIGN KEY` / `CHECK` without `NOT VALID` (Postgres): validates every row under lock. Safe pattern: add `NOT VALID`, then `VALIDATE CONSTRAINT` separately (takes a weaker lock).
- Even a "fast" ALTER needs a brief exclusive lock — behind one long-running query it queues, and *every later query queues behind it*. Recommend a `lock_timeout` so the migration gives up instead of freezing the app.

**2. Deploy-order breakage (the one everyone misses)**
The schema and the code do not change atomically. For each change ask: *what does the still-running old code do against the new schema, and the new code against the old schema?*
- Dropping/renaming a column or table the old code still reads → errors for the entire deploy window. Renames are drops in disguise; ORMs with `SELECT *`-style loading make this worse.
- Adding a `NOT NULL` column without default → old code's INSERTs (which don't know the column) start failing instantly.
- The fix is expand/contract: add new alongside old → deploy code that writes both/reads new → backfill → drop old in a *later* migration.

**3. Data loss**
- Type narrowing (text→varchar(n), bigint→int, dropping timezone), lossy `USING` casts, truncating defaults.
- Any `DROP COLUMN`/`DROP TABLE`: is the data actually dead? Recommend rename-then-drop-next-week over trusting a code search.

**4. Rollback reality**
- Is there a down migration, and is it *honest*? A down that re-adds a dropped column does not bring the data back — that's not a rollback, it's a shape restoration. If a step is irreversible, it should be called out in the migration itself, and the backup/restore plan named.
- Mixed DDL+DML in one transaction on engines where DDL isn't transactional (MySQL): a mid-migration failure leaves it half-applied.

**5. Backfills hiding inside migrations**
`UPDATE table SET ...` for millions of rows inside a migration = one giant transaction, replication lag, lock bloat, and a deploy pipeline that times out. Backfills belong in batched scripts, not schema migrations (see the backfill-pilot skill if it's installed).

## Report format

```
## Verdict: BLOCK / CAUTION / SAFE
- [BLOCK] CREATE INDEX on orders(user_id) — plain build write-locks `orders`
  for the duration (~minutes at this size). Use CREATE INDEX CONCURRENTLY
  + disable_ddl_transaction.
- [CAUTION] Dropping `users.legacy_id` — old code reads it during rolling
  deploy. Move the drop to the next release.
- Safe: adding nullable `users.locale` (metadata-only on PG 15).
```

Severity honestly: BLOCK = will cause an outage or data loss as written. CAUTION = safe only under conditions you spell out. Don't cry wolf on a 500-row lookup table — flagging everything teaches people to ignore you; note "fine at this table's size" instead.

## Boundaries

- If you can't tell the engine, version, or table size, say which verdicts depend on it rather than guessing silently.
- Don't invent traffic numbers or table sizes. "If this table is large or hot…" with the threshold that matters is honest; "this WILL take the site down" without knowing is not.
- You review what the migration *does to a live system*, not style, naming, or whether the schema design is pretty.
