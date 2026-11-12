# digest-guard — example

**Trigger:**

> an analyst on our EU sales team says they got this week's "regional
> pipeline" dashboard digest in their inbox, but it had rows from the APAC
> region they've never had access to in the app itself. the digest was set
> up by someone who used to have cross-region access and left the company
> two months ago — their Looker account was deactivated, but the schedule
> is still firing weekly. also, anyone on the team can hit "subscribe me"
> on an existing digest without an admin re-granting anything. can you
> audit how our scheduled digests handle this?

**Response shape:**

Check 1 finds the stale-snapshot gap:

```
Check 1: access checked once, not on every send
The digest job stores the row-level-security filter as a snapshot on the
schedule row at creation time (`schedule.rls_filter_json`), not re-derived
from the owner's live role on every run. The former employee's account
being deactivated changed nothing about that stored filter — it's still
the cross-region grant they had when the schedule was created, and the
weekly cron just replays it.
```

Check 2 finds the self-subscribe path, matching the pattern behind
Metabase's CVE-2023-23629:

```
Check 2: self-subscribe inherits the schedule's access, not the
subscriber's
`POST /digests/:id/subscribe` adds the caller's user_id to the
recipient list with no re-check of what that user is independently
allowed to see — it's the same shape CVE-2023-23629 patched in Metabase,
where a sandboxed user could add themselves to someone else's existing
dashboard subscription and receive the creator's unfiltered data. Here,
any team member could have self-subscribed to this exact digest and
gotten the same APAC rows, not just this one case where it happened to
be the owner who'd had the access.
```

Check 3 confirms the owner-deprovisioning blind spot:

```
Check 3: deprovisioning didn't touch the schedule
The owner's account is deactivated in the identity provider and in the
app's own user table, but nothing in deactivation looks for schedules
they own and disables or re-validates them. The cron that fires this
digest doesn't check "is this owner's account still active" at all — it
just re-runs the stored query under the stored filter.
```

Report:

```
## digest-guard review: "regional pipeline" dashboard digest

1. `schedule.rls_filter_json` is captured once at creation and never
   refreshed — the owner's access two months ago is still what gates
   every send today, regardless of what's changed since (BLOCK,
   Check 1).

2. `/digests/:id/subscribe` adds a recipient with no check of the
   subscriber's own access — the same bypass CVE-2023-23629 patched in
   Metabase. This isn't limited to the owner's case; any lower-access
   team member can self-subscribe to any existing digest and inherit
   its filter (BLOCK, Check 2).

3. Account deactivation has no hook into owned schedules — a
   deprovisioned owner's digests keep firing indefinitely on the access
   they had before deprovisioning, with no alert and no automatic
   disable (BLOCK, Check 3).

4. Fix, in order of leverage: re-derive the RLS filter from the owner's
   *current* role on every send instead of a stored snapshot; make
   self-subscribe re-validate the subscriber's own access against the
   content before adding them, not just append a recipient row; and add
   an owner-deprovisioning hook that disables (or forces re-review of)
   every schedule the deactivated account owns.

## Verdict: BLOCK
All three gaps are independently sufficient to explain the leak, and
any one of them lets this recur with a different owner or a different
self-subscriber tomorrow even if this specific digest gets fixed by
hand today.
```
