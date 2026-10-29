# quote-guard — example

**Trigger:**

> a customer says their backorder shipped three weeks after they ordered it
> and they got charged $34 more than the total their cart showed at
> checkout. can you check our backorder capture code?
>
> ```js
> // orders/backorder.js
> async function placeBackorder(cartId) {
>   const cart = await Cart.get(cartId);
>   const authorization = await stripe.paymentIntents.create({
>     amount: cart.totalCents,
>     currency: 'usd',
>     capture_method: 'manual',
>     customer: cart.customerId,
>   });
>   await Order.create({
>     cartId, authId: authorization.id,
>     quotedCents: cart.totalCents, status: 'backordered',
>   });
>   return { ok: true };
> }
>
> // fires when the warehouse marks the SKU back in stock, days or weeks later
> async function captureOnRestock(orderId) {
>   const order = await Order.get(orderId);
>   const item = await Catalog.get(order.sku);
>   const liveTotal = item.priceCents * order.quantity + order.shippingCents;
>   await stripe.paymentIntents.capture(order.authId, { amount_to_capture: liveTotal });
>   await order.update({ status: 'fulfilled', capturedCents: liveTotal });
>   return { ok: true };
> }
> ```

**Response shape:**

Step 1 maps the pin-and-charge points and the gap between them:

```
Step 1: quote-to-charge surfaces
One deferred flow: placeBackorder quotes and authorizes `cart.totalCents`
(capture_method: 'manual' — the charge is held, not settled). The actual
charge fires in captureOnRestock, whenever the warehouse restocks the
SKU — "days or weeks later" per the code's own comment. That's the gap:
seconds at authorization, weeks at capture.
```

Step 2 checks what can move the true price inside that gap:

```
Step 2: drift sources reaching the gap
captureOnRestock reads `item.priceCents` live from Catalog at capture
time — a catalog price edit on this SKU at any point during the
multi-week backorder wait lands directly in the captured amount. No
coupon or tax recompute in this path, but the catalog price alone is
enough to explain a $34 drift over three weeks.
```

Step 3 traces what the code does with that live number:

```
Step 3: what actually gets charged
captureOnRestock recomputes `liveTotal` from the current catalog price
and calls `paymentIntents.capture` with that number — not
`order.quotedCents`, the amount the customer actually saw and agreed to
at checkout. That's the silent-recompute outcome: the charged amount
differs from the shown amount with no fresh confirmation, the exact
Kahn v. Walmart shape (7th Cir. No. 23-1751) moved into checkout code —
and a confirmation email with the real total afterward doesn't fix it
any more than a receipt did there.

Second, independent problem: Stripe caps a capture at the amount
originally authorized. If the live catalog price had risen enough that
`liveTotal` exceeded the authorized `cart.totalCents` instead of just
sitting below it, this same call would be rejected by Stripe outright —
and there's no try/catch here, no re-authorization flow, nothing. A
bigger price increase during the backorder wait wouldn't overcharge the
customer; it would throw, leave the order stuck in 'backordered', and
nobody — customer or ops — would be told why.
```

Step 4 checks for a re-confirmation gate before the deferred charge:

```
Step 4: customer notice before the money moves
None. captureOnRestock fires automatically on a restock event with no
step that compares `liveTotal` to `quotedCents` or tells the customer
anything before capturing. `order.update` records `capturedCents` but
never checks it against `quotedCents`, so even a successful-but-drifted
capture leaves no record distinguishing "charged what we quoted" from
"charged something else" — this bug was only found because a customer
complained, not because anything in the system could have caught it.
```

Report:

```
## quote-guard review: orders/backorder.js

1. captureOnRestock charges the live catalog price instead of the
   quoted/authorized amount, with no customer notice or
   re-confirmation (BLOCK — confirmed root cause of the reported $34
   overcharge): `liveTotal` is read fresh from `Catalog.get(order.sku)`
   at capture time and passed straight to `amount_to_capture`,
   discarding `order.quotedCents` entirely. Fix: capture
   `quotedCents` by default; if the live price has moved, require an
   explicit re-confirmation step (a new quote the customer approves)
   before charging anything other than what they originally agreed to.

2. No handling for Stripe rejecting a capture above the original
   authorization (BLOCK — not yet reported, but one price increase
   away from happening): `amount_to_capture` has no ceiling check
   against the PaymentIntent's authorized amount before the call, and
   there's no catch around it. Fix: compare `liveTotal` to the
   authorized amount first; if it's higher, don't attempt the capture —
   trigger a real re-authorization request to the customer instead of
   letting Stripe's rejection surface as an unhandled error.

3. capturedCents is never compared to quotedCents (CAUTION — not
   reported, found in review): even a correct, undrifted capture
   leaves no record proving the two matched, so a future drift like
   this one is only discoverable by customer complaint again. Fix: log
   or assert the two are equal on every capture, and alert when
   they're not.

## Verdict: BLOCK
The reported overcharge traces to a confirmed root cause — the capture
path trusts a live catalog read over the amount the customer actually
quoted and agreed to, with no re-confirmation. The missing
authorization-ceiling handling is the same bug waiting for a bigger
price move; fix both before the next restock cycle runs.
```
