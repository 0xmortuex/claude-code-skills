---
name: quote-guard
description: Audits whether the amount a customer saw and agreed to is the exact amount actually captured, across every gap between quote and charge — a catalog price edit, a promo window closing, a coupon re-validated differently, or a tax/inventory recompute landing inside a deferred-capture flow (pre-order, backorder, buy-now-pay-later, trial-to-paid) where the gap is hours or months, not seconds. Checks whether a drift gets silently re-priced with no fresh confirmation, silently undercharged with nobody deciding that on purpose, or thrown as a processor rejection nobody handles (most processors cap a capture at the originally authorized amount). Use when adding or reviewing checkout/cart/payment-capture code or a deferred/multi-step billing flow, or when asked "does the price we show match what we actually charge", "why was this customer charged a different amount than their cart showed", "is our checkout price locked or live", or "audit price integrity between cart and capture".
---

# quote-guard

A cart total is a promise, not a live read of the catalog, and the code that honors it is usually written once, for the case where "quote" and "charge" happen seconds apart in the same request. That assumption breaks the moment anything sits between them — a backorder waiting on restock, a pre-order waiting on a ship date, a buy-now-pay-later installment, a free trial converting to paid weeks later — because everything that can change the "true" price gets a window to do it before the money actually moves. Two real constraints make this more than a UX nit. Legally: in *Kahn v. Walmart* (7th Cir. No. 23-1751, 2024), the Seventh Circuit reversed a dismissal and held that a receipt showing the price actually charged does not, as a matter of law, cure the deception caused by a different price shown earlier — "the receipt fixes it" is not a defense a court has to accept. Technically: Stripe's own `PaymentIntents` capture API rejects an `amount_to_capture` greater than the amount originally authorized — code that quietly recomputes "today's real price" at capture time and tries to charge more than was authorized doesn't silently overcharge, it gets an API error, and plenty of capture code has no idea that's a scenario it needs to handle.

## Step 1: map every point where a price gets pinned, and where it's actually charged

Walk the flow and list each point in time an amount gets fixed or read: the cart line-item snapshot, the checkout-page total render, the payment authorization, and the actual capture/settlement — which for `capture_method: 'manual'`, a deferred-billing flow, or a scheduled re-charge can be hours, days, or months after authorization, not the same request. Note every deferred/multi-step charge specifically: a pre-order waiting on a release date, a backorder waiting on restock, a buy-now-pay-later installment schedule, a free-trial-to-paid conversion using a price last looked at on signup day, a subscription renewal. For each one, write down the real-world size of the gap — the longer it is, the more of Step 2's drift sources get a real chance to land inside it before the charge fires.

## Step 2: for each gap, what can actually move the "true" price underneath the frozen quote?

- A catalog price edit on the SKU between quote and capture.
- A sale/promo window closing (or a new one opening) inside the gap.
- A coupon or discount code re-validated at capture time instead of trusted from the cart snapshot — minimum-spend thresholds, stacking rules, and per-customer usage caps can all evaluate differently the second time.
- Inventory-driven dynamic pricing keyed to live stock level (surge or clearance tiers).
- A tax-rate or jurisdiction recompute landing inside the gap (an address correction, a rate change's effective date).

Currency/FX rate-lock timing is deliberately excluded here — see Boundaries — this step assumes a single currency and asks only whether the *base* price itself drifted.

## Step 3: trace what the code actually does when the live price at capture time disagrees with the frozen quote

For every gap Step 1 found, follow the code to the line that decides what amount actually gets charged, and sort it into one of three outcomes — only one of which is usually the right call on purpose:

- **Charges the originally quoted amount regardless of current truth.** Safe for the customer, but means the merchant silently eats every price increase that lands in the gap. Only worth flagging if the gap is routinely long enough (pre-order, backorder) that this has become a standing, undecided revenue leak rather than a deliberate price-lock promise.
- **Silently recomputes and captures "today's" amount instead, with no fresh disclosure or re-confirmation.** This is the *Kahn v. Walmart* shape transplanted into code: the amount charged differs from the amount the customer actually saw and agreed to, and a later receipt or confirmation email showing the real total is not a fix — it's the same defense the Seventh Circuit already rejected, just automated.
- **Tries to capture an amount the processor won't accept against the original authorization, and mishandles the rejection.** Check whether this is a deliberate re-authorization flow (re-prompt the customer, obtain a fresh authorization for the new amount before capturing) or an unhandled error/bare retry loop that leaves the order stuck half-captured with no signal to anyone, customer or ops, that it happened.

## Step 4: for every deferred/multi-step flow, confirm there's a real re-confirmation gate before the final charge

A pre-order, backorder, BNPL installment, or trial-to-paid conversion is a second (or third) sale happening on a timer, with no person present reconfirming it the way an ordinary instant checkout does just by existing. Find the exact code path that fires the deferred charge and check two things: whether it captures an amount that's been re-validated as still matching what the customer was last shown, rather than a number nobody has looked at since quote time; and whether, if that amount has moved since the original quote, the customer gets a real, dated notice before the money moves — not just a webhook log entry only engineering can read after the fact.

## Report

BLOCK for: a capture path that silently charges a different amount than the customer was shown, with no fresh confirmation (Step 3's second outcome); or a capture-vs-authorization mismatch handled as a bare unhandled error or retry loop instead of a deliberate re-authorization flow (Step 3's third outcome). CAUTION for: a quoted-price lock on a routinely long gap (pre-order/backorder/trial) that's functioning as an undecided standing revenue leak; or a deferred-charge path with no customer-facing notice before the money moves, even when the amount itself turns out correct. Name the exact function and line where the captured amount is read, which of Step 2's drift sources can reach it, and the real size of the gap — "price integrity looks fine" is not a finding; either the charged amount is provably the one the customer saw, or it isn't.

## Boundaries

- Not an FX/currency-conversion review — multi-currency rate-lock timing is `proration-guard`'s already-noted adjacent, separately-covered failure class; this skill assumes a single currency throughout and audits whether the base price itself drifted between quote and capture.
- Not `proration-guard`'s territory — that skill audits subscription plan-change proration math against a plan's documented policy; this skill audits a single transaction's amount integrity between when it was quoted and when it was actually captured, subscription billing included but not its special case.
- Not a payment-callback/webhook trust review (signature verification, replay, an attacker-forged success notification) — that's a security/trust-boundary problem on the *inbound* side; this skill assumes the payment provider's own responses are trustworthy and asks only whether the application's *own* logic ever tries to charge something other than what it showed.
- Not a business-logic pentest for client-side price tampering (editing a hidden price field, replaying a cheaper price token) — that's an attacker deliberately manipulating input, already covered by dedicated business-logic/API-abuse security skills; this skill is about the system's own legitimate flow silently drifting with no attacker involved.
- Can't confirm an actual historical overcharge or undercharge from source alone — it identifies which code paths are capable of charging something other than what was shown, and says plainly when confirming a real past incident needs transaction logs (the quoted amount vs. the captured amount for a specific order), not a code read.
