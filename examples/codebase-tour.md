# codebase-tour — example

**Trigger:**

> just inherited this repo, previous dev is gone. it's some kind of order
> processing service. where do I even start, and where would I add a new
> discount code type?

**Response shape:**

Claude doesn't summarize the folder tree — it finds the entry point and
traces one real request through the layers, per the skill's "trace, don't
list" instruction:

```
## What this is
A Node/Express order-processing API backed by Postgres. Takes order
requests from a web frontend, applies pricing/discount rules, writes to
the DB, and emits an event for the fulfillment worker to pick up.

## The lay of the land
routes/        — HTTP layer, one file per resource, thin (just
                  validation + calls into services/)
services/      — business logic: pricing, discounts, order lifecycle
repositories/  — the only layer that talks to Postgres (raw `pg`, no ORM)
events/        — publishes to a Redis stream for the fulfillment worker
workers/       — a separate process, not run by this service in dev
migrations/    — plain SQL, run by `npm run migrate`
```

It traces one representative path end to end, with `file:line` citations,
rather than describing layers in the abstract:

```
## How it flows
POST /orders → routes/orders.js:18 validates the request body against
`schemas/order.js`, then calls `services/orderService.js:createOrder()`.

createOrder() (services/orderService.js:24-61) does three things in order:
  1. services/pricingService.js:9 computes the base total from line items
  2. services/discountService.js:15 applies any discount code — this is
     where a new discount type would plug in (see below)
  3. repositories/orderRepository.js:33 inserts the order + line items in
     a single transaction

After commit, events/orderEvents.js:12 publishes an `order.created` event
to the `orders` Redis stream. routes/orders.js:18 returns 201 with the
order id — it does NOT wait for fulfillment, which is async via
workers/fulfillmentWorker.js (a separate process, started by
`npm run worker`, not by `npm start`).
```

## Where you'd make common changes
For the actual question asked, it lands on the specific files, not a
general "look in services/":

```
To add a new discount code type: services/discountService.js:15-58 is a
switch on `discount.type` ('percent', 'fixed', 'bogo'). Add a case there,
plus:
  - schemas/order.js:40 — the Joi schema whitelists known discount types,
    yours needs adding or validation rejects the request before it
    reaches discountService at all
  - migrations/ — `discounts.type` is a Postgres CHECK constraint
    (migrations/0007_discount_types.sql:3), needs a new migration to
    widen it or the insert in discountRepository.js will fail at the DB,
    not in application code
  - test/services/discountService.test.js has one describe block per
    existing type — follow that pattern for the new one
```

It's honest about the mess rather than smoothing it over, per the skill's
"be honest about mess" principle:

```
## Things to know before you touch it
- Two error-handling styles coexist: routes/orders.js uses Express
  error-handling middleware (throw + next(err)), but
  services/discountService.js:40 still returns `{ error: '...' }` objects
  from an earlier pattern that was never fully migrated. Don't copy the
  old style into new code, but expect to see both.
- repositories/ uses raw parameterized SQL, not an ORM — there's no
  migration-generation tool, so schema changes are hand-written SQL in
  migrations/ and easy to get out of sync with what repositories/ expects.
- The fulfillment worker (workers/fulfillmentWorker.js) is a separate
  process not started by `npm start` — if "the order doesn't fulfill" in
  local dev, this is almost always why; run `npm run worker` alongside
  the API.
```

The tour ends where the skill says it must — at "where do I go" — instead
of stopping at a description of the architecture.
