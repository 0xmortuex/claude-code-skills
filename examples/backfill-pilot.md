# backfill-pilot — example

**Trigger:**

> we added a `region` column to `orders` and need to backfill it for the
> ~40M existing rows from `shipping_address.country`. table's live, gets
> ~200 writes/sec. here's what I was about to run:
>
> ```sql
> UPDATE orders
> SET region = country_to_region(shipping_address ->> 'country')
> WHERE region IS NULL;
> ```

**Response shape:**

Claude scopes it before touching the mutation — the count comes first:

```
Run this before anything else, and show me the number:

  SELECT count(*) FROM orders WHERE region IS NULL;

40M is your estimate — if the real count is 10x that, the batch plan
below needs bigger numbers, and if it's 10x smaller this may not need
the full ceremony. Also: orders is live at 200 writes/sec, so new rows
keep landing with region NULL the whole time this runs. Either the
INSERT path sets region going forward (so this backfill chases a
closing set) or this script needs to run to convergence, not just once.
```

It rejects the one-shot UPDATE on the specific failure modes it invites,
not just "that's unsafe":

```
This UPDATE, run as-is, does four things wrong at 40M rows:

  - one transaction holding a lock across the whole table — on Postgres
    that's an AccessExclusive-adjacent write lock for however long 40M
    row updates take, which blocks the 200 writes/sec you said this
    table gets
  - no checkpoint — if it dies at row 30M (deploy, timeout, OOM), the
    whole thing restarts from row 0, redoing 30M writes
  - no undo — country_to_region() has edge cases (multi-country
    addresses, missing country, typos in shipping_address), and if the
    mapping is wrong there's no row-level way back short of a full
    table restore
  - no verification query defined — "it ran without erroring" isn't the
    same as "it's correct"
```

Then it produces the batched, resumable, undoable version — all seven
properties, not a subset:

```python
#!/usr/bin/env python3
"""Backfill orders.region from shipping_address->>'country'.
Dry-run by default; pass --execute to write. Resumable via
backfill_progress; safe to re-run (idempotent on already-fixed rows)."""

import argparse
import time

BATCH_SIZE = 5000
SLEEP_MS = 75
JOB_NAME = "orders_region_backfill"

def get_checkpoint(conn, job):
    row = conn.execute(
        "SELECT last_id FROM backfill_progress WHERE job = %s", (job,)
    ).fetchone()
    return row[0] if row else 0

def save_checkpoint(conn, job, last_id, updated):
    conn.execute(
        """INSERT INTO backfill_progress (job, last_id, updated_count, updated_at)
           VALUES (%s, %s, %s, now())
           ON CONFLICT (job) DO UPDATE
           SET last_id = EXCLUDED.last_id,
               updated_count = backfill_progress.updated_count + EXCLUDED.updated_count,
               updated_at = now()""",
        (job, last_id, updated),
    )
    conn.commit()

def run(conn, execute: bool):
    last_id = get_checkpoint(conn, JOB_NAME)
    print(f"resuming from id > {last_id}")

    while True:
        conn.execute("SET LOCAL lock_timeout = '2s'")
        conn.execute("SET LOCAL statement_timeout = '10s'")

        batch = conn.execute(
            """SELECT id, shipping_address ->> 'country' AS country
               FROM orders
               WHERE id > %s AND region IS DISTINCT FROM
                     country_to_region(shipping_address ->> 'country')
               ORDER BY id
               LIMIT %s""",
            (last_id, BATCH_SIZE),
        ).fetchall()

        if not batch:
            print("no rows left matching predicate — done")
            break

        if not execute:
            sample = batch[:10]
            print(f"[dry-run] batch would touch {len(batch)} rows, "
                  f"ids {batch[0].id}..{batch[-1].id}")
            for row in sample:
                print(f"  id={row.id} country={row.country!r} -> "
                      f"region={country_to_region(row.country)!r}")
            last_id = batch[-1].id
            continue

        ids = [r.id for r in batch]
        conn.execute(
            """UPDATE orders SET region = country_to_region(shipping_address ->> 'country')
               WHERE id = ANY(%s)
                 AND region IS DISTINCT FROM country_to_region(shipping_address ->> 'country')""",
            (ids,),
        )
        last_id = batch[-1].id
        save_checkpoint(conn, JOB_NAME, last_id, len(batch))
        print(f"batch ids {batch[0].id}..{last_id}, {len(batch)} touched")
        time.sleep(SLEEP_MS / 1000)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    run(get_conn(), execute=args.execute)
```

It calls out the undo capture and the verification query as separate,
required steps — not folded silently into the script above:

```
Before the first --execute run:

  CREATE TABLE backfill_undo_2026_08_08 AS
  SELECT id, region AS old_region FROM orders WHERE region IS NULL;

Drop it after a deliberate retention window (30 days is reasonable for
a column this size) once you've verified nothing needed it.

Verification — run before (baseline) and after (proof):

  -- before: how many are wrong
  SELECT count(*) FROM orders WHERE region IS NULL;
  -- after: should be 0 (or only new live rows younger than the run)
  SELECT count(*) FROM orders WHERE region IS NULL;
  -- spot-check a handful of known countries by hand
  SELECT id, shipping_address ->> 'country', region
  FROM orders WHERE id IN (<5 known ids>);
```

Finally it flags the live-table chase problem raised in scoping, since
the script alone doesn't resolve it:

```
This still won't converge on its own if new orders keep inserting with
region NULL faster than the backfill retires the backlog. Fix the
INSERT path to set region at write time first (or in the same deploy),
so this script is chasing a closed, shrinking set instead of a moving
target — then run backfill-pilot to clear what's already there.
```
