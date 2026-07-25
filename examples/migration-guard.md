# migration-guard — example

**Trigger:**

> can you check if this migration is safe to run on prod tonight?
>
> ```python
> def upgrade():
>     op.add_column('orders', sa.Column('region', sa.String(), nullable=False))
>     op.execute("UPDATE orders SET region = 'us-east-1'")
>     op.create_index('ix_orders_region', 'orders', ['region'])
> ```
>
> orders has about 40M rows, Postgres 13, rolling deploy.

**Response shape:**

Claude establishes blast radius (engine/version, table size, deploy model —
already given here), walks the hazard checklist, and reports a verdict, not a
rewrite:

```
## Verdict: BLOCK

- [BLOCK] `add_column(..., nullable=False)` with no server default — on
  Postgres 13 this is a metadata-only change UNTIL you try to enforce
  NOT NULL against existing rows, which this does implicitly via the
  UPDATE below running first. Old code mid-rolling-deploy still issues
  INSERTs that don't set `region` — those will fail against the NOT NULL
  constraint the instant it's applied, for the whole deploy window.

- [BLOCK] `UPDATE orders SET region = ...` inside the migration — one
  transaction touching 40M rows. This holds row locks for the duration,
  bloats WAL, and will likely blow past any migration-runner timeout.
  This is a backfill hiding inside a migration, not a schema change.

- [CAUTION] `CREATE INDEX` without `CONCURRENTLY` — plain build
  write-locks `orders` for the build's duration. At 40M rows that's
  minutes of blocked writes, not instant.

Safe alternative (expand/contract):
  1. This migration: add `region` as NULLABLE, no default.
  2. Deploy code that writes `region` on every new/updated order.
  3. Backfill existing rows in a batched, resumable script (see
     backfill-pilot) — not inside a migration transaction.
  4. A later migration: `CREATE INDEX CONCURRENTLY`, then only after
     the backfill is verified complete, add the NOT NULL constraint
     (Postgres 13 can validate this without a full table rewrite via
     a CHECK constraint added NOT VALID + VALIDATE CONSTRAINT first).
```

It doesn't rewrite the migration unprompted — the verdict and the safe
alternative are the deliverable unless asked to apply the fix.
