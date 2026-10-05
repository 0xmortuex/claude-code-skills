# overwrite-guard — example

**Trigger:**

> a customer filed a ticket saying they updated their shipping address and
> phone number in two separate tabs within a minute of each other, and now
> the phone number is back to the old value. nothing errored on their end.
> can you check our profile save endpoint?
>
> ```python
> # models.py
> class CustomerProfile(Base):
>     __tablename__ = "customer_profiles"
>     id = Column(Integer, primary_key=True)
>     shipping_address = Column(String)
>     phone_number = Column(String)
>     version = Column(Integer, nullable=False, default=1)  # for optimistic locking
> ```
>
> ```python
> # routes.py
> @app.patch("/profiles/{profile_id}")
> def update_profile(profile_id: int, body: ProfileUpdate, db: Session):
>     profile = db.query(CustomerProfile).get(profile_id)
>     for field, value in body.dict(exclude_unset=True).items():
>         setattr(profile, field, value)
>     profile.version += 1
>     db.commit()
>     return profile
> ```

**Response shape:**

Step 1 confirms this is a real read-modify-write race on a shared record:

```
Step 1: read-modify-write on a shared record
`update_profile` loads the full `CustomerProfile` row, applies only the
fields the caller sent, and writes it back. Two tabs open on the same
profile is exactly two independent requests racing on the same row —
tab A loads the row to change the address, tab B loads it (at a version
still equal to A's) to change the phone number, both PATCH within a
minute. This is squarely the shape this skill audits, not an
atomic-increment or append-only write.
```

Step 2 finds the version column — and that it's cosmetic:

```
Step 2: is a version/revision mechanism actually wired into the write?
The `version` column exists and its comment says "for optimistic
locking," but `update_profile`'s query is `db.query(CustomerProfile).get(profile_id)`
— no version in the lookup — and the commit is a plain `UPDATE ...
SET ... WHERE id = ?` with no `AND version = ?` predicate. `version` is
incremented on every write but never checked on any write. This is the
MedCover #461 pattern exactly: a version column declared for this
purpose, never registered as an enforced predicate, so it increments
faithfully while protecting nothing.
```

Step 3 is moot here since there's nothing to check the baseline of — the report says so rather than padding the finding:

```
Step 3: baseline check
N/A — there's no enforcement to trace a baseline for. (Worth flagging
separately: even if `version` were added to the `WHERE` clause, nothing
in `ProfileUpdate` or the route signature currently gives the client a
way to send back the version it read, so the client side of the contract
would also need to change, not just the server query.)
```

Step 4 confirms there's no conflict path at all, consistent with steps 2–3:

```
Step 4: conflict handling
There's nothing to detect a conflict, so there's nothing to swallow —
the bug isn't a caught-and-ignored exception, it's that the write path
can't ever produce one. Every concurrent PATCH on this row succeeds
unconditionally; whichever request's full-row write lands last wins,
silently discarding any field changed only by the other request.
```

Report:

```
## overwrite-guard review: routes.py:update_profile

1. `update_profile` is a read-modify-write on a per-customer row two
   browser tabs (or a tab plus a support-agent edit) can race on within
   seconds (BLOCK — confirmed root cause).

2. `version` is declared on the model and incremented on every write,
   but never read back in the lookup or added to the `UPDATE`'s `WHERE`
   clause — it protects nothing today despite looking like it should
   (BLOCK, same root cause as MedCover #461).

3. N/A — no enforcement exists yet to have a wrong baseline.

4. No conflict path exists to swallow or mis-handle; there's no `409`/
   `412`/`StaleDataError` anywhere in this flow because nothing can ever
   detect the race in the first place.

## Verdict: BLOCK
Two concurrent PATCHes to the same profile — a plausible, now-confirmed
real case — silently drop whichever field only the losing request
changed, with no error on either side. The `version` column is already
there, which makes this a narrower fix than building locking from
scratch: register it as an actual precondition (SQLAlchemy
`version_id_col` in `__mapper_args__`, or hand-roll `WHERE id = ? AND
version = ?` and check the affected-row count), have `ProfileUpdate`
accept and require the version the client last read, and return `409`
with the current row on a mismatch so the client can reload and reapply
instead of silently losing the conflicting field.
```
