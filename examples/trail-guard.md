# trail-guard — example

**Trigger:**

> we got asked during a customer escalation "who canceled this subscription
> and refunded them" and couldn't answer it from our audit log — the row
> just wasn't there. can you check whether we're actually logging every
> admin action, not just that one? here's the admin router:
>
> ```js
> // routes/admin.js
> router.post('/admin/subscriptions/:id/cancel', requireAdmin, async (req, res) => {
>   const sub = await Subscription.findById(req.params.id);
>   if (!sub) return res.status(404).end();
>   await sub.cancel();
>   await auditLog.write({ actor: req.admin.id, action: 'subscription.cancel', target: sub.id });
>   res.json({ ok: true });
> });
>
> router.post('/admin/subscriptions/:id/refund', requireAdmin, async (req, res) => {
>   const sub = await Subscription.findById(req.params.id);
>   if (!sub) return res.status(404).end();
>   if (sub.status !== 'canceled') return res.status(400).json({ error: 'not canceled' });
>   await stripe.refunds.create({ charge: sub.lastChargeId });
>   res.json({ ok: true });
> });
>
> router.post('/admin/subscriptions/bulk-cancel', requireAdmin, async (req, res) => {
>   await Subscription.updateMany({ _id: { $in: req.body.ids } }, { status: 'canceled' });
>   res.json({ ok: true, count: req.body.ids.length });
> });
> ```

**Response shape:**

Step 1 builds the list from the router, not from existing `auditLog` calls:

```
Step 1: mutating surfaces from routes/admin.js
Three POST (mutating) admin routes: subscription cancel, subscription
refund, subscription bulk-cancel. All three are admin-only
(`requireAdmin`) and touch billing state, so all three are in scope.
```

Step 2 checks whether each one reaches a log call on every exit path:

```
Step 2: exit-path coverage
- cancel: has an `auditLog.write` call, placed after `sub.cancel()` and
  before the response — reached on the success path. The 404 early
  return skips it, but a cancel on a nonexistent id has no state change
  to record, so that's not a gap.
- refund: NO auditLog.write call anywhere in the handler. The refund
  actually moves money via Stripe and there is no record of who
  triggered it or when — this is the exact gap the escalation hit.
- bulk-cancel: NO auditLog.write call. Also uses `updateMany` directly
  rather than looping through the single-cancel handler, so it doesn't
  inherit that handler's logging either.
```

Step 3 asks whether this is opt-in or enforced:

```
Step 3: opt-in vs. structural
No middleware, decorator, or route-registration check ties `POST
/admin/*` routes to a required audit call — `cancel`'s logging is
present only because whoever wrote it remembered to add the line. There
is nothing that would fail a build or a test if a fourth admin route
shipped tomorrow with the same gap `refund` and `bulk-cancel` have
today. This is the root cause, not just two missing lines: the pattern
`ROCm/spur`'s audit-middleware PR (#870) fixed is the same one here —
"auditing was opt-in per handler, so anything added next started
unaudited."
```

Step 4 confirms the bulk path independently, since it was already caught in step 2:

```
Step 4: bulk path
bulk-cancel is exactly the "separate code path" case this step warns
about — it calls `Subscription.updateMany` directly instead of the
per-subscription cancel logic, so even if refund's gap gets fixed by
copying cancel's line, bulk-cancel needs its own fix, not an inherited
one.
```

Report matches the skill's lead-with-root-cause order:

```
## trail-guard review: routes/admin.js

1. Audit coverage is opt-in with no enforcement (BLOCK — root cause):
   nothing ties a new `POST /admin/*` route to a required audit-log
   call; `cancel`'s coverage is incidental, not guaranteed. Fix:
   move audit logging into middleware that wraps every admin route (or
   add a route-registration completeness check that fails when a new
   mutating route isn't classified), the same shape as the fix this
   skill is grounded in, rather than trusting each new handler to add
   its own call.

2. `refund` has no audit-log entry at all (BLOCK — confirmed root cause
   of the escalation): an admin-triggered Stripe refund moving real
   money has zero record of actor or timestamp. This is the specific
   gap that made "who refunded this" unanswerable.

3. `bulk-cancel` has no audit-log entry and bypasses the single-cancel
   logging by calling `updateMany` directly (BLOCK): an admin can
   cancel any number of subscriptions with no record of who did it, how
   many, or which ones.

## Verdict: BLOCK
Two of three admin billing actions have zero audit coverage, and the
one that does isn't protected against regressing — it's simply the one
handler where someone remembered. Fix `refund` and `bulk-cancel`
directly, then close the root cause in finding 1 so the next admin
route doesn't reopen the same gap.
```
