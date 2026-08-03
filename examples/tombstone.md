# tombstone — example

**Trigger:**

> can I drop the `users.legacy_referrer_code` column? ran `grep -r
> legacy_referrer_code` across the whole repo and the ORM model is the only
> hit — nothing reads or writes it anymore in our code.

**Response shape:**

Claude doesn't accept the grep as the final word — it classifies reachability
first, since a DB column is exactly the kind of surface other things can
touch without going through this repo's ORM at all:

```
grep proves nothing in *this repo* references legacy_referrer_code anymore
— that's real, but it's not the same claim as "nothing reads this column."
A DB column is externally reachable by definition: anything with a
connection string can SELECT it, whether or not it goes through your ORM.
Before deleting, I need evidence from the database itself, not just from
this repo's source.
```

It picks the evidence source that actually matches a DB column (not app
logs, which wouldn't catch a caller with its own connection string):

```
Checked pg_stat_statements for any SELECT/UPDATE touching
legacy_referrer_code over the last 30 days: zero. That covers this repo's
own traffic pattern, but pg_stat_statements only sees what ran while the
extension was collecting — it doesn't tell us about tools with direct
DB access we can't see from here (BI dashboards, another team's service,
an analyst's ad-hoc query script).
```

Rather than declaring it safe on the stats alone, it flags exactly who
else needs to be asked before this counts as proven:

```
Before this is safe to drop:
  - confirm no BI/analytics tool queries this table directly (ask
    whoever owns the warehouse sync / Looker / Metabase connection)
  - check for any read replica consumers with their own queries
  - 30 days is a reasonable window for a column touched by normal request
    traffic, but if referrer attribution is used in a monthly reporting
    job, that job's cadence — not the request traffic's — is what decides
    the window
```

Only with that confirmed does it move to the delete step, and it matches
rollback cost to blast radius rather than defaulting to a hard delete:

```
verdict: safe to drop, low blast radius (single internal table, no BI
  dependency confirmed via #data-eng, 2026-08-03)
  — go straight to a normal migration dropping the column; no need for
  a two-step deprecate/null-out cycle since nothing external reads it.
  Put the pg_stat_statements query and the #data-eng confirmation in the
  migration's PR description so the person who gets paged later can see
  exactly what was checked.
```
