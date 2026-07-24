---
name: skew-check
description: Review a change for mixed-version deploy hazards — the window during every rolling/canary deploy when OLD and NEW code run at the same time against shared state. Use before deploying changes that touch queue/event message shapes, cache or session serialization, RPC/API payloads between your own services, feature-flag payloads, or anything persisted that another version will read. Trigger on "is this safe to roll out", "will this break during deploy", canary/rolling-deploy prep, and proactively when a diff renames or retypes a field that crosses a process boundary.
---

# skew-check

Code review checks that the new version is correct. Almost nobody checks the state every real deploy actually passes through: **vN-1 and vN running simultaneously**, sharing queues, caches, sessions, and each other's API calls — plus the mirror image, a rollback, where vN-1 comes back and meets data vN already wrote. Changes that are perfectly correct at rest break in this window: a renamed queue field old consumers can't parse, a new session format old pods can't read, an enum value old code treats as fatal. These surface as "transient errors during every rollout" that everyone learns to ignore.

The discipline is one question asked systematically: **for every shared surface this diff touches, can each version read what the other writes, for the whole overlap window?**

## Step 1: inventory the shared surfaces in the diff

Walk the diff and list every point where data crosses a process or time boundary:

- **Queue / event messages** — anything produced to a broker or event store. Special: these *outlive the deploy* — a message written by vN-2 can be replayed next month, so compatibility here is durable, not just deploy-window.
- **Cache values** — serialized objects in Redis/memcached that both versions read.
- **Sessions / cookies / tokens** — old pods will receive sessions minted by new pods, and vice versa, on every request during the rollout.
- **RPC/API contracts between your own services** — services deploy independently; "we updated both sides" still means a window where they disagree.
- **Feature-flag payloads and config blobs** — new config schema read by old code.
- **DB rows** — shape changes are migration-guard's job (use it); *value semantics* changes (a status string meaning something new) are yours.

Changes with no shared surface (pure UI, internal refactors) are SAFE by inspection — say so in one line and stop.

## Step 2: run the four compatibility directions per surface

For each touched surface, check all four (people reliably check only the first):

1. **New reads old** — vN deserializes data vN-1 wrote. (Renamed/removed fields, stricter parsers, exhaustive enum matches all fail here.)
2. **Old reads new** — vN-1 deserializes data vN wrote *during the overlap*. (Added required fields, new enum values, changed encodings fail here — and this is the one nobody tests, because old code "doesn't exist" anymore in CI.)
3. **Rollback: old reads new's leftovers** — if vN is reverted an hour later, vN-1 meets everything vN persisted. A deploy is only reversible if this direction holds.
4. **Replay: new reads ancient** — for durable stores (queues with retention, event sourcing), vN must read messages from versions long gone. Deserialize a corpus of real historical messages in a test if the store is event-sourced.

Format-specific rules for durable data: protobuf — field numbers are immutable, never reuse them, use `reserved`; Avro — added fields need defaults; JSON — additive-only changes with tolerant readers (unknown fields ignored, missing fields defaulted).

## Step 3: prescribe the fix per hazard

The universal recipe is **expand → migrate → contract**, spread over more than one release:

- Renaming a field: release 1 writes both names and reads either; release 2 (after retention window / all sessions expired) drops the old.
- New enum value: ship readers that tolerate it *first*, producers that emit it *second*.
- Session/cache format change: version the payload (`v` field or key prefix `sess:v2:`); old code keeps its keyspace until it's gone.
- Queue envelope: a version field in every message from day one; consumers dispatch on it.
- If the surface can't be made compatible (rare), the honest alternative is a drain-and-stop deploy — say that explicitly rather than pretending rolling is safe.

## Report

```
## Skew verdict: BLOCK / CAUTION / SAFE
- [BLOCK] session payload: `userId` renamed to `uid` — old pods throw on
  every request routed to them during rollout, and rollback breaks all
  sessions minted by vN. Fix: write both fields this release, drop next.
- [SAFE] internal refactor of the parser — no shared surface.
```

One line per surface, including the SAFE ones — the value of the review is knowing everything was checked, not just reading the failures.

## Boundaries

- DB *schema* changes → migration-guard (this skill covers the data's meaning, not its DDL).
- You usually can't run vN-1 here; reason from the old code in git (`git show <last-release>:path`) — cite the old reader's actual parsing behavior, don't guess it.
- Single-instance apps with atomic restarts have no overlap window — but rollback (direction 3) and durable queues (direction 4) still apply; don't wave those off.
