---
name: backfill-pilot
description: Write or review a production data backfill/repair safely — the one-off script that updates millions of live rows to fix bad data, populate a new column, or migrate a format. Use whenever the user needs to "backfill", "fix the data in prod", "migrate existing rows", "run a one-off script against the database", or shows an UPDATE/DELETE meant to touch a large or live table. These scripts are written once, run once, and have no test suite — which is exactly why they destroy data more often than any other kind of code.
---

# backfill-pilot

A backfill is production surgery: a script with no tests, run once, against the only copy of the data, usually under time pressure. The difference between a safe one and a disaster is not cleverness — it's a short list of non-negotiable properties. Your job is to produce (or review toward) a script that has all of them, and to refuse the tempting one-liner that has none.

The tempting one-liner — `UPDATE users SET plan = 'free' WHERE plan IS NULL` — fails four ways at scale: one giant lock-holding transaction, no way to see progress, no way to resume if it dies at row 40M, and no record of what it changed if it turns out to be wrong.

## First: scope the operation

Ask (or read from context) — the answers change the design:
- **How many rows will actually change?** Run the `SELECT count(*)` version of the predicate FIRST — off-by-1000x expectations are how "quick fixes" become incidents. Show the count before writing the mutation.
- **Is the table live?** Reads mid-backfill see half-migrated data; is that OK? Do writes keep creating rows that need the fix (→ backfill must be re-runnable at the end, or new writes fixed *first* so the backfill chases a closed set)?
- **Engine + replication** — batch size and throttle depend on it (huge transactions → replica lag → stale reads elsewhere).

## The non-negotiable properties

**1. Batched, small transactions.** Loop: claim next batch (1k–10k rows), mutate, commit, repeat. Never one transaction for the whole thing — commits bound lock hold-time, replication lag, and undo/WAL growth.

**2. Keyset pagination, not OFFSET, not a moving predicate.** Walk an indexed immutable key (`WHERE id > $last ORDER BY id LIMIT $n`), remembering `$last`. `OFFSET` re-scans and skips rows as data shifts under it. And beware the self-defeating predicate: paginating on `WHERE plan IS NULL` while setting `plan` changes which rows match page 2 — with keyset-on-id it's harmless; combined with OFFSET it silently skips half the rows.

**3. Resumable + idempotent.** The script WILL be interrupted (deploy, OOM, Ctrl-C). Persist the last completed key (a checkpoint table beats a log line: `backfill_progress(job, last_id, updated_count)`); on start, resume from it. Re-running any batch must be harmless — the mutation should be a no-op on already-fixed rows (`SET x = ... WHERE x IS DISTINCT FROM ...` or the predicate itself excludes fixed rows).

**4. Undo path that actually exists.** Before mutating, save what you're about to change: `INSERT INTO backfill_undo_<date> SELECT id, old_column FROM ... WHERE <predicate>` (or export to a file). "We have nightly backups" is not an undo path — restoring a 2 TB backup to fix one column is a day of downtime. Row-level undo is an UPDATE-from-join away. State the retention: drop the undo table after N days, deliberately.

**5. Dry-run mode, on by default.** `--execute` to actually write. Dry run prints: rows matched, sample of before→after for ~10 rows, batch count. The user (or you) eyeballs the sample — this catches the wrong-join and the timezone-shifted-date before they happen 40M times.

**6. Throttle + kill switch.** Sleep between batches (even 50–100 ms transforms the load profile); make batch size and sleep flags so it can be tuned mid-run. A `lock_timeout`/`statement_timeout` so a lock conflict aborts the batch instead of queueing the whole app behind it. Log every batch: `batch 412/3900, ids 1044000..1046500, 2431 updated, 12 skipped`.

**7. Verification query, written BEFORE running.** Define done as a query: "after this, `SELECT count(*) FROM t WHERE <bad-state>` = 0 and `SELECT count(*) WHERE <good-state>` grew by ~N". Run it before (baseline), after (proof), and spot-check a few known-affected IDs by hand. A backfill without a verification query is a hope, not an operation.

## Review mode

When handed an existing backfill, check exactly the seven properties above and report which are missing, each with the concrete failure it invites ("no checkpoint → a crash at hour 3 restarts from zero → doubles the write load you throttled to avoid"). BLOCK on: unbatched mass UPDATE/DELETE on a live table, no undo capture for destructive changes, OFFSET pagination, no verification.

## Boundaries

- Never run the mutating version yourself without the user's explicit go — produce the script, show the dry-run output, hand over the trigger. (Running the read-only dry run / counts is fine and encouraged.)
- If the "backfill" is actually a schema change in disguise (adding columns, constraints), route the DDL part through migration review (see migration-guard) — this skill owns the DML.
- Small static table (< ~100k rows, low traffic)? Say plainly that a single transaction + undo capture + verification is enough — don't ceremonialize a 2-second operation into a week. The checklist scales down; the undo and verification never drop.
