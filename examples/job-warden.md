# job-warden — example

**Trigger:**

> here's our SQS consumer for `order.paid` — on message it calls the carrier
> API to create a shipment and decrements `inventory.reserved` for the SKU.
> runs as a small pool of long-lived workers on ECS. deploying today, want a
> sanity check first.

**Response shape:**

Claude reads the handler and goes through the six questions in order instead
of eyeballing it for "looks fine" — starting with the one that at-least-once
delivery makes non-optional:

```
1. Idempotency: FAIL on both side effects.
   - carrier.create_shipment(order.id, address) has no idempotency key. SQS
     is at-least-once: if the worker crashes or the visibility timeout
     expires after the shipment is created but before the message is
     deleted, this message is redelivered and a second shipment gets
     created for the same order.
   - `UPDATE inventory SET reserved = reserved - 1` is a bare decrement, not
     a dedup'd write. A replay decrements twice, so reserved stock drifts
     down from a single order — this is the "balance += x" case called out
     as unsafe, not the "SET status='sent'" case that's safe by construction.
```

It doesn't stop at naming the problem — it ties the fix to what each API
actually supports, rather than prescribing one generic pattern for both:

```
Fixes, one per side effect:
  - carrier.create_shipment: pass order.id as the idempotency key if the
    carrier API supports one (most shipping APIs do — check their docs
    before assuming); if it doesn't, record "shipment_created" for this
    order.id in the same transaction as the DB write below, and check it
    before calling the carrier at all.
  - inventory.reserved: add a processed_messages(order_id) table, checked
    and inserted in the same transaction as the UPDATE. Second delivery of
    the same order_id finds the row, skips the decrement, still acks.
```

Question 2 gets scoped to what actually applies to a queue consumer (not a
cron job) — concurrent workers pulling the same message, not a run
outliving its interval:

```
2. Overlap: RISK, not FAIL — a pool of workers means the same message can
   be picked up twice if SQS's visibility timeout expires mid-processing
   (e.g. the carrier API is slow that day) before the first worker acks.
   This collapses into question 1: the fix above (idempotency key +
   processed-message check) covers it, so there's no separate lock needed
   here — but the visibility timeout should also be set comfortably above
   the carrier call's p99, or this happens on every slow response instead
   of only on crashes.
```

Questions 3 and 5 get honest short answers instead of forced findings —
the skill's instruction to skip ceremony where it doesn't apply, not skip
the question itself:

```
3. Schedule: N/A — event-driven consumer, no cron schedule to misfire.
5. Batch: N/A — this handler processes one message at a time, not a batch;
   nothing to decide about partial-batch failure.
```

Question 4 catches the gap between "has retries" and "has retries that
terminate":

```
4. Poison messages: FAIL — SQS redelivery is configured but there's no
   maxReceiveCount / dead-letter queue. An order with a malformed address
   that makes the carrier API 400 forever will retry indefinitely, node
   the visibility timeout each time, and never surface to a human.
   Fix: set maxReceiveCount (5, with backoff) and a DLQ; alert on any
   message landing in it, since "order paid but never shipped" is exactly
   the silent failure this queue exists to prevent.
```

And question 6 — the one that applies no matter how small the job is —
catches that failures are covered but the silent case isn't:

```
6. Liveness: FAIL — CloudWatch alarms fire on Lambda/ECS errors, but if
   the ECS service itself is scaled to zero (bad deploy, IAM role
   revoked) the queue just backs up with no alerting on queue depth or
   oldest-message-age. Add a "max message age in queue" alarm — that
   catches the consumer being dead, not just the consumer erroring.
```

Final report matches the skill's standard format, verdict per question:

```
## job: order-paid-consumer
1. Idempotency: FAIL — no idempotency key on shipment creation or
   inventory decrement; SQS redelivery double-ships and drains stock.
2. Overlap: RISK — covered by #1's fix; also widen visibility timeout
   above carrier-call p99.
3. Schedule: N/A — event-driven, no cron.
4. Poison messages: FAIL — no maxReceiveCount/DLQ; malformed orders
   retry forever.
5. Batch: N/A — single-message handler.
6. Liveness: FAIL — no alarm on queue depth/age; a dead consumer is silent.

Don't ship as-is: #1 and #4 are the two that cause customer-visible harm
(double shipments, orders that silently never ship). #6 is cheap to add
now and is the only thing that will tell you if today's deploy itself
breaks the consumer.
```
