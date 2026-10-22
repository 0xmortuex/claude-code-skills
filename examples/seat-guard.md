# seat-guard — example

**Trigger:**

> we're on a 25-seat plan but billing says we have 28 active users. nobody
> remembers inviting that many people and the invite screen definitely blocks
> us once we hit 25. we also just turned on Okta SCIM provisioning last month
> and offboarded three contractors around the same time — can you figure out
> what's going on before I email support?
>
> ```js
> // invites.js — manual "invite user" flow
> async function inviteUser(orgId, email) {
>   const org = await db.orgs.findById(orgId);
>   const activeCount = await db.users.count({ orgId, status: 'active' });
>   if (activeCount >= org.seatLimit) throw new Error('Seat limit reached');
>   return db.users.create({ orgId, email, status: 'pending' });
> }
>
> async function deactivateUser(userId) {
>   await db.users.update(userId, { status: 'inactive' });
>   // used_seats counter is untouched here
> }
> ```
>
> ```js
> // scim.js — Okta SCIM provisioning webhook, added last month
> async function scimCreateUser(orgId, scimPayload) {
>   // no seat check at all — provisions directly
>   return db.users.create({ orgId, email: scimPayload.email, status: 'active' });
> }
> ```
>
> ```sql
> -- org.seatLimit is compared against a live COUNT() in invites.js,
> -- but the billing dashboard reads a separate `orgs.used_seats` column
> -- that only `inviteUser`'s acceptance step increments, and nothing
> -- decrements on deactivation.
> ```

**Response shape:**

Step 1 checks the manual invite path for the race and finds it's not the active bug here (it's a live `COUNT()`, not a race-prone counter), but flags it as fragile anyway since nothing locks the row between the count and the create.

Step 2 finds the real divergence — two different seat tallies:

```
Step 2: deactivation vs. the enforcement source
inviteUser checks a live COUNT(status='active') — correct in principle,
but the *billing dashboard* the customer is looking at reads
`orgs.used_seats`, a separate counter only ever incremented on
acceptance and never decremented by deactivateUser. The three offboarded
contractors are marked status='inactive' (correctly invisible to
inviteUser's own count) but used_seats still includes them — that's
where "28" in billing comes from, and it isn't the same number the
invite screen is blocking against. Two sources of truth for one seat
limit, drifting independently.
```

Step 3 finds the actual overage mechanism — SCIM bypassing enforcement entirely:

```
Step 3: provisioning paths
scimCreateUser writes status: 'active' directly with no seat check of
any kind — it doesn't call inviteUser's logic, read org.seatLimit, or
touch used_seats. Every user Okta pushes via SCIM is invisible to both
seat-tracking mechanisms until someone manually reconciles. This is the
real source of being over the limit: SCIM, turned on last month, has
been silently adding active users the whole time, while the invite
screen's 25-seat block only ever applied to the one path that still
checks it.
```

Report:

```
## seat-guard review: 25-seat plan showing 28 active users

1. Two disconnected seat sources: `inviteUser` enforces against a live
   COUNT(status='active'); the billing dashboard reads `used_seats`,
   which deactivation never decrements. Contractors offboarded this
   month are correctly excluded from one and incorrectly still counted
   in the other (BLOCK — pick one source of truth and make both paths
   read it).

2. `scimCreateUser` provisions directly with zero seat enforcement —
   not a reimplementation that drifted, no check at all. This is why
   the org is over its limit despite the invite screen blocking at 25:
   SCIM has been adding active users outside every mechanism that was
   supposed to stop that (BLOCK — this is the actual incident).

3. `inviteUser`'s count-then-create has no transaction or row lock
   between the COUNT and the create — not today's bug, but two
   simultaneous invites could still both pass once this is otherwise
   fixed (CAUTION — wrap in a transaction or switch to a conditional
   atomic UPDATE on a single counter now, while this code is already
   being touched).

## Verdict: BLOCK
Make `used_seats` and SCIM both read-and-write the same enforcement
path `inviteUser` uses — a single atomic counter or a live COUNT(),
chosen once. Decrement it (or let the COUNT() naturally reflect it) the
moment `deactivateUser` runs. Add the identical seat check to
`scimCreateUser` before the Okta integration provisions another user,
and reconcile the current 28 down to what the 25-seat plan actually
allows before support closes the ticket.
```
