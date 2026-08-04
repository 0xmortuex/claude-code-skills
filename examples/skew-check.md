# skew-check — example

**Trigger:**

> about to roll this out as a normal rolling deploy (no maintenance window).
> the diff makes `customerId` required on the `order.created` event we
> publish to Kafka, and adds a new `PARTIALLY_REFUNDED` value to the
> `status` enum on the same message. is this safe?

**Response shape:**

Claude inventories the one shared surface in the diff and calls out that
`order.created` is a queue message — meaning "the deploy window" isn't the
whole risk, because messages outlive the pods that wrote them:

```
Shared surface: `order.created` Kafka message, consumed by at least the
billing and analytics services (checking `git grep 'order.created'` in
both). This is a durable topic with retention, not just an in-memory RPC —
compatibility has to hold for however long messages sit before consumers
catch up, not just for the rollout window.
```

It runs both changes through all four directions, not just "will new code
break" — and flags the one people skip:

```
1. New reads old (vN reads a message vN-1 wrote):
   customerId — old messages don't have it. If the new consumer code
   does `msg.customerId.toUpperCase()` without a null check, this throws
   on every pre-deploy message still in the topic. [BLOCK]
   status enum — old messages never contain PARTIALLY_REFUNDED, nothing
   to handle here. [SAFE]

2. Old reads new (vN-1 reads a message vN wrote, during the overlap):
   customerId — old consumers ignore unknown-but-present fields (checked:
   the billing consumer deserializes with a tolerant JSON reader). [SAFE]
   status enum — old billing code does an exhaustive switch on status and
   throws MatchError on an unhandled case. The instant one new-version pod
   publishes a PARTIALLY_REFUNDED event, every still-running old pod that
   consumes it crashes. [BLOCK]

3. Rollback (old reads new's leftovers):
   Same failure as #2, and worse — if vN is rolled back an hour in, every
   PARTIALLY_REFUNDED message already published is now unreadable by the
   reverted code with no way to reprocess it except a manual patch. [BLOCK]

4. Replay (new reads ancient):
   customerId — topic retention is 7 days; messages from before this
   release will still be replayed by consumer restarts/backfills within
   that window, same missing-field risk as direction 1. [BLOCK, same fix]
```

Then it prescribes the fix per hazard instead of a blanket "add a null
check", using expand → migrate → contract:

```
customerId: don't make it required in the schema at all yet. Release 1 —
  producer starts always setting it, consumers treat it as optional and
  fall back to the current lookup-by-orderId path. Release 2, once the
  7-day retention window has fully rolled past release 1 — consumers can
  assume it's present, *then* tighten the schema to required.

status enum: ship the reader change first, alone. Release 1 — every
  consumer's switch gets a default/unknown-value branch (log + skip, don't
  crash). Release 2 — once that's fully deployed, the producer starts
  emitting PARTIALLY_REFUNDED. Never ship producer and reader in the same
  release for an enum addition.
```

And gives the final verdict in the skill's report format, one line per
surface including what's fine as-is:

```
## Skew verdict: BLOCK
- [BLOCK] order.created.customerId: required-field add reaches old
  consumers and ancient replayed messages within the 7-day retention
  window. Fix: optional this release, required next.
- [BLOCK] order.created.status: new enum value crashes old consumers'
  exhaustive switch during rollout and breaks rollback. Fix: ship
  tolerant readers first, producer change in a later release.

Do not deploy as a single rolling release. Split into the two releases
above; each one alone is safe to roll out normally.
```
