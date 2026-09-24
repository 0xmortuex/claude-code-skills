# proration-guard — example

**Trigger:**

> a customer says they redeemed a $20 promo credit and got dropped from
> Pro Annual to a free-tier plan, and separately someone else says they
> canceled mid-cycle and still got billed the "no proration" cancellation
> fee we advertise as free. can you check our plan-change code? here's the
> billing module:
>
> ```js
> // billing/subscriptions.js
> async function upgradeSubscription(accountId, newPlanId) {
>   const sub = await Subscription.get(accountId);
>   await stripe.subscriptions.update(sub.stripeId, {
>     items: [{ id: sub.itemId, price: newPlanId }],
>     proration_behavior: 'create_prorations',
>   });
>   await sub.update({ planId: newPlanId });
>   return { ok: true };
> }
>
> async function scheduleDowngrade(accountId, newPlanId) {
>   const sub = await Subscription.get(accountId);
>   await sub.update({ pendingPlanId: newPlanId, pendingAt: sub.currentPeriodEnd });
>   return { ok: true };
> }
>
> // cancellation policy (docs/pricing.md): "Cancel anytime — no proration,
> // no cancellation fee, access continues until the period you already paid for ends."
> async function adminCancelImmediate(accountId) {
>   const sub = await Subscription.get(accountId);
>   const credit = computeUnusedTimeCredit(sub, new Date());
>   await stripe.subscriptions.cancel(sub.stripeId, { prorate: true });
>   await Ledger.credit(accountId, credit);
>   await sub.update({ status: 'canceled' });
>   return { ok: true };
> }
>
> async function redeemVoucher(accountId, voucherCode) {
>   const voucher = await Voucher.lookup(voucherCode);
>   const sub = await Subscription.get(accountId);
>   await Ledger.credit(accountId, voucher.amountCents);
>   if (voucher.type === 'gift_subscription') {
>     await sub.update({ planId: voucher.giftPlanId });
>     await Invoice.create({ accountId, planId: voucher.giftPlanId, amountCents: 0 });
>   }
>   return { ok: true };
> }
> ```

**Response shape:**

Step 1 maps every path that touches plan or period state, not just the two named in the ticket:

```
Step 1: plan-change surfaces
Four: upgradeSubscription (immediate, prorated), scheduleDowngrade
(deferred to period end), adminCancelImmediate (support-tool
cancellation), and redeemVoucher (credit redemption — but it also
writes `planId` and creates an invoice for one voucher type, so it's
in scope even though "redeem a voucher" doesn't sound like a plan
change).
```

Step 2 checks the proration math against the plan's own documented policy:

```
Step 2: math vs. documented policy
- upgradeSubscription: `create_prorations` matches the expected
  immediate-upgrade behavior. No issue.
- scheduleDowngrade: correctly deferred to `currentPeriodEnd`, no
  credit issued now. Matches expectations for a downgrade.
- adminCancelImmediate: docs/pricing.md promises "no proration, no
  cancellation fee" on cancel — but the code passes `prorate: true` to
  Stripe AND separately computes and issues its own unused-time credit
  via `computeUnusedTimeCredit`, doubling the credit on top of
  whatever Stripe's own proration already does. This is the exact
  Kill Bill #698 shape: the documented policy says no proration, a
  different code path (the admin tool, not the customer-facing
  cancel) prorates anyway — and here it prorates twice.
```

Step 3 traces the voucher-redemption path since it writes plan state:

```
Step 3: credit/voucher crossing into plan-change state
`redeemVoucher` is supposed to add a balance. For `gift_subscription`
vouchers it also calls `sub.update({ planId: voucher.giftPlanId })` —
silently overwriting whatever plan the customer was actually on, with
no check for what `giftPlanId` maps to relative to their current tier.
A Pro Annual subscriber whose gift voucher points at a free-tier gift
plan ID gets downgraded from Pro Annual to free with no upgrade path
back and no confirmation step. It also unconditionally creates a new
$0 invoice on top of whatever invoice is already scheduled for the
account's real plan, rather than replacing or suppressing it — this
matches the reported "unauthorized duplicate invoices" pattern
exactly (claude-code#51168).
```

Step 4 checks concurrent/repeated plan-change requests:

```
Step 4: races and double-submits
scheduleDowngrade has no idempotency check and no read of an existing
`pendingPlanId` before overwriting it — two downgrade clicks (or one
retried request) silently replace the first scheduled change with the
second, with no record either happened. Not the reported bug, but a
second, independent gap in the same function.
```

Report leads with the two confirmed root causes from the ticket, then the independent gap found along the way:

```
## proration-guard review: billing/subscriptions.js

1. `redeemVoucher` can silently downgrade a paying customer's real plan
   (BLOCK — confirmed root cause of the reported bug): a
   `gift_subscription` voucher overwrites `planId` unconditionally with
   no check against the account's current tier, and creates a second
   invoice without touching the one already scheduled. Fix: gift
   vouchers should apply to a separate gift-entitlement record, never
   overwrite `planId` on an existing paid subscription; if a plan
   change is genuinely intended, gate it behind an explicit
   confirmation and compare against the current tier first.

2. `adminCancelImmediate` prorates in two places while the documented
   policy promises no proration on cancel at all (BLOCK — confirmed
   root cause of the second report): Stripe's own `prorate: true` and
   a separately computed `computeUnusedTimeCredit` both run, doubling
   the credit issued, and both contradict docs/pricing.md's "no
   proration" promise. Fix: either the docs are wrong and need
   updating, or this handler needs to match `scheduleDowngrade`'s
   deferred, no-credit behavior instead of Stripe's immediate-cancel
   default.

3. `scheduleDowngrade` isn't idempotent against a repeated or
   double-submitted request (CAUTION — not reported, found in review):
   a retry silently replaces a pending scheduled change with no log or
   conflict check. Fix: read the existing `pendingPlanId` first and
   either reject, confirm, or explicitly replace-with-record rather
   than blind overwrite.

## Verdict: BLOCK
Both reported bugs trace to real, confirmed root causes — a voucher
path that reaches into plan state it shouldn't touch, and a
cancellation path that contradicts its own advertised policy. Fix
both before the next voucher redemption or admin cancellation repeats
either one; the scheduling race is lower-severity and can follow.
```
