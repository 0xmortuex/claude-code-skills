# stale-guard — example

**Trigger:**

> we added a Redis cache in front of the team inbox endpoint last week
> (`GET /teams/:teamId/inbox-counts`, 30 min TTL, key is `inbox_counts:{teamId}`).
> today an agent said their dashboard showed tickets assigned to a
> teammate as their own. is the caching here correct?

**Response shape:**

Claude starts by naming the source of truth and the copy, and pins down
what a "correct" staleness budget would actually be before judging
anything — not just accepting the 30-minute TTL as given:

```
Copy: Redis key `inbox_counts:{teamId}` → JSON blob of ticket counts.
Source of truth: `tickets` table, filtered by `assigned_to` and `team_id`.
Staleness budget: the count is a *scoped* view, not a global aggregate —
so before asking "how old can it be," the more basic question is whether
one cached value can even correctly serve every requester.
```

Step 3 (invariant B — does the key contain every dimension the value
depends on) is where it finds the real bug, not the TTL:

```
Invariant B: the endpoint response is *per-agent* — agents see only
tickets where assigned_to = current_user, team leads see the full team.
The cache key is `inbox_counts:{teamId}` only — no user/role dimension.

  dependency          | in key?
  --------------------|--------
  team_id             | yes
  assigned_to (agent)  | NO
  role (agent vs lead) | NO

First agent to hit a cold key populates it with *their own* filtered
counts. Every other agent on the same team who requests inbox-counts
within the next 30 minutes gets served that first agent's numbers —
including, per the report, tickets assigned to a teammate showing up
as "yours." This isn't stale data, it's cross-user data: a role-scoped
result cached under a team-scoped key. BLOCK regardless of how rarely
it's noticed.
```

It also checks invariant A (every write path invalidates) instead of
stopping at the key-scoping bug, and finds a second, independent gap:

```
Invariant A — write paths that mutate `tickets.assigned_to`:
  - normal "reassign ticket" endpoint → calls cache.delete(f"inbox_counts:{team_id}") ✔
  - admin bulk-redistribute action (moves all of one agent's tickets to
    the rest of the team during PTO) → raw UPDATE via the admin panel's
    SQL console, no application code path, no invalidation ✘

Bulk redistribution is exactly when stale counts hurt most — it reassigns
dozens of tickets at once, and every agent's inbox count is wrong for up
to the full 30-minute TTL afterward, right when accurate routing matters.
```

Report matches the skill's standard format — per-copy, invariant table,
severity by consequence rather than by how it was found:

```
## Cache: inbox_counts:{teamId} (Redis, 30 min TTL)
Source of truth: tickets table (assigned_to, team_id)
Staleness budget: N/A as scoped — see invariant B

Invariant A (write-path → invalidates?):
  reassign-ticket endpoint     ✔
  admin bulk-redistribute      ✘ BLOCK (raw SQL, no cache touch)

Invariant B (dependency → in key?):
  team_id      ✔
  assigned_to  ✘ BLOCK (agent-scoped result cached under team-scoped key)
  role         ✘ BLOCK (same defect — a lead's full-team view can be
               served to an agent, or vice versa, whichever request
               populates the key first)

## Verdict: BLOCK
Fix invariant B first — it's the cross-user leak: key must be
`inbox_counts:{teamId}:{userId}:{role}`, not `{teamId}` alone. Fix
invariant A next — route bulk-redistribute through the same
invalidation the reassign endpoint uses, or move it off raw SQL
entirely. Don't ship a TTL tweak as the fix; the TTL was never the bug.
```
