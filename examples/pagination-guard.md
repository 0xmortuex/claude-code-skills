# pagination-guard — example

**Trigger:**

> we added a "export all leads as CSV" button last month. a customer just
> filed a support ticket saying a lead they know exists isn't in their
> export, and when they re-ran it an hour later it was there but a
> *different* lead was missing. we page through in batches of 500. here's
> the export job:
>
> ```python
> def export_leads(account_id):
>     rows = []
>     offset = 0
>     while True:
>         page = db.execute(
>             "SELECT id, name, email, created_at FROM leads "
>             "WHERE account_id = %s ORDER BY created_at "
>             "LIMIT 500 OFFSET %s",
>             (account_id, offset),
>         )
>         if not page:
>             break
>         rows.extend(page)
>         offset += 500
>     return write_csv(rows)
> ```
>
> leads get created continuously (inbound form submits) and occasionally
> deleted (spam cleanup job runs hourly). nothing else touches this query.

**Response shape:**

Step 2 finds the first problem — the sort has no tiebreaker:

```
Step 2: ORDER BY created_at has no unique tiebreaker
`created_at` is not guaranteed unique — any two leads created in the same
database-timestamp tick tie, and their relative order across a page
boundary is undefined. With enough rows this alone can show a lead twice
or skip it even on a perfectly static table.
```

Step 3 finds the real explanation for this specific report — the offset
shift under concurrent deletes:

```
Step 3: OFFSET shifts under concurrent delete
The hourly spam-cleanup job deletes leads while this export is mid-run.
`OFFSET 500` on the next page means "skip the first 500 rows of the
result set *as it exists right now*" — if a lead ordered before position
500 was deleted since the previous page fetch, every later row shifts up
by one, and the next OFFSET 500 now starts one row later than it should:
the row that should be first on this page was already the last row
returned on the previous page (an apparent duplicate, if it ties Step 2),
or, more often here, a lead right at the new boundary is never fetched at
all — it's "skipped" by exactly the number of rows deleted ahead of it
since the scan started. This fully explains the ticket: a different lead
missing each run is consistent with "whichever lead happened to sit near
a boundary when cleanup ran," not a one-off fluke.
```

Step 5 names the severity:

```
Step 5: consumer needs a complete enumeration
This isn't an infinite-scroll feed where a glitch is a UX nit — it's a
full customer-facing export where "every lead, exactly once" is the whole
point of the feature. Treat both findings as BLOCK, not CAUTION.
```

Report:

```
## pagination-guard review: export_leads, offset pagination over a live table

1. `ORDER BY created_at` has no unique tiebreaker — add the primary key as
   a secondary sort column (BLOCK, Step 2): `ORDER BY created_at, id`.

2. `OFFSET` pagination over a table with concurrent deletes (the hourly
   spam-cleanup job) structurally cannot guarantee "every row exactly
   once" — a delete ahead of the current offset shifts every later row
   and skips or duplicates one on the next fetch. This is the actual
   cause of the ticket, not a one-off (BLOCK, Step 3).

3. Fix: switch to keyset pagination anchored on the tiebroken sort key —
   `WHERE (created_at, id) > (%s, %s) ORDER BY created_at, id LIMIT 500`,
   carrying the last row's `(created_at, id)` forward as the cursor
   instead of a row count. A delete or insert anywhere else in the table
   no longer moves where the next page starts.

## Verdict: BLOCK
Offset pagination against a table the cleanup job actively deletes from,
with no unique tiebreaker, will keep skipping or duplicating leads on
every export that overlaps a cleanup run. Move to keyset pagination on
`(created_at, id)` before this export can be trusted as complete.
```
