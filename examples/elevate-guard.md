# elevate-guard — example

**Trigger:**

> we added a break-glass "request temporary admin" button for on-call —
> 15 minutes of superadmin, then it's supposed to drop automatically.
> someone noticed the countdown hit zero but they could still hit admin
> endpoints for a while after. here's the relevant code:
>
> ```js
> // grant a time-boxed elevation
> router.post('/break-glass/activate', requireOncall, async (req, res) => {
>   const grant = await ElevationGrant.create({
>     userId: req.user.id,
>     role: 'superadmin',
>     expiresAt: Date.now() + 15 * 60 * 1000,
>   });
>   const token = jwt.sign(
>     { sub: req.user.id, role: 'superadmin', grantId: grant.id },
>     SIGNING_SECRET,
>     { expiresIn: '8h' } // matches the normal session TTL
>   );
>   res.json({ token, expiresAt: grant.expiresAt });
> });
>
> // authorization check used by every admin-only route
> function requireSuperadmin(req, res, next) {
>   const payload = jwt.verify(req.headers.authorization.split(' ')[1], SIGNING_SECRET);
>   if (payload.role !== 'superadmin') return res.status(403).end();
>   req.user = payload;
>   next(); // no check against ElevationGrant.expiresAt at all
> }
>
> // cron, supposed to run every minute
> // cron: * * * * * node jobs/expireGrants.js
> ```
>
> `jobs/expireGrants.js`:
> ```js
> const stale = await ElevationGrant.findExpired();
> for (const g of stale) await ElevationGrant.update(g.id, { active: false });
> ```

**Response shape:**

Step 1 traces what the authorization check actually reads:

```
Step 1: what requireSuperadmin reads
The elevated role is baked into the JWT issued at activation time —
`{ role: 'superadmin', grantId }` — signed with an 8-hour expiry that
matches the *normal* session TTL, not the grant's own 15-minute window.
`requireSuperadmin` verifies the JWT's signature and its own expiry,
then trusts `payload.role` directly. It never looks up `ElevationGrant`
by `grantId` to check `expiresAt`. The UI countdown is computed
client-side from the `expiresAt` the activation response returned —
nothing server-side ever re-checks that number again.
```

Step 2 traces the job that's supposed to end it:

```
Step 2: the revocation job
`jobs/expireGrants.js` flips `ElevationGrant.active` to false on
expired rows — but nothing in the request path reads `active` either.
Even if the cron runs exactly on schedule, it has no effect, because
`requireSuperadmin` never consulted the grants table in the first
place; it only validates the JWT, which keeps asserting
`role: 'superadmin'` for its own full 8-hour life regardless of what
the grants table says. Separately: there's no monitoring on the cron
itself — if a worker crash silently drops ticks, nothing would surface
that either, but it's moot here since the job was never on the
authorization path to begin with.
```

Report:

```
## elevate-guard review: break-glass elevation

1. `requireSuperadmin` authorizes off a `role` claim baked into the JWT
   at activation time and never re-reads `ElevationGrant.expiresAt` —
   the grant's own 15-minute window has no effect on the authorization
   check at all (BLOCK — this is the root cause the countdown-after-
   zero report traces back to).

2. The JWT's own expiry is set to 8 hours, matching the normal session
   TTL rather than the grant's 15-minute window, so even a client that
   discarded the token at "0:00" could have kept using a copy of it
   for the full 8 hours (BLOCK, compounds #1).

3. `jobs/expireGrants.js` correctly flips `active=false` on schedule,
   but that field is never consulted anywhere in the request path —
   the job runs and succeeds while accomplishing nothing (BLOCK: a
   revocation mechanism that's wired to no authorization check is
   equivalent to having none).

## Verdict: BLOCK
The elevation's UI countdown is decorative. Authorization is decided
entirely by a JWT claim set once at activation and valid for 8 hours;
neither the grant's own `expiresAt` nor the cron job that updates
`active` is ever read by `requireSuperadmin`. Fix: have
`requireSuperadmin` look up the live grant by `grantId` and check
`expiresAt`/`active` on every request instead of trusting the JWT's
`role` claim, and scope the JWT's own expiry to the grant's window
(15 minutes), not the ambient session TTL — so even an unconsulted
grants table fails safe once the token itself dies.
```
