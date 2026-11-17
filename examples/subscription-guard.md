# subscription-guard — example

**Trigger:**

> we added a live "ticket updated" subscription for our support app so
> agents see changes without refreshing. a customer reported they can see
> ticket updates for tickets that aren't theirs if they open the subscription
> directly. here's the setup:
>
> ```python
> # schema.py
> @strawberry.type
> class Query:
>     @strawberry.field
>     def ticket(self, info: Info, ticket_id: str) -> Ticket:
>         ticket = db.get_ticket(ticket_id)
>         if ticket.org_id != info.context.user.org_id:
>             raise PermissionError("not your ticket")
>         return ticket
>
> @strawberry.type
> class Subscription:
>     @strawberry.subscription
>     async def ticket_updated(self, info: Info, ticket_id: str) -> AsyncGenerator[Ticket, None]:
>         async for event in pubsub.subscribe(f"ticket:{ticket_id}"):
>             yield event.ticket
>
> # server.py
> schema = strawberry.Schema(query=Query, subscription=Subscription)
> app.mount("/graphql", GraphQLRouter(schema, subscription_protocols=[
>     GRAPHQL_TRANSPORT_WS_PROTOCOL,
>     GRAPHQL_WS_PROTOCOL,  # legacy subprotocol, kept for an older client
> ]))
> ```

**Response shape:**

Step 1 traces whether the subscription transport authenticates at all, and for every subprotocol in use:

```
Step 1: subscription transport authentication
`GraphQLRouter` is configured with no `on_ws_connect` (Strawberry's
connect hook) at all, and it registers both `GRAPHQL_TRANSPORT_WS_PROTOCOL`
and the legacy `GRAPHQL_WS_PROTOCOL`. With no connect hook, `info.context`
for a subscription never gets the authenticated `user` the Query resolver
relies on — this matches CVE-2026-35523's exact shape (legacy subprotocol
skipping the auth hook), except here there's no hook on *either*
subprotocol, not just the legacy one.
```

Step 2 compares the subscription resolver's authorization to the equivalent query's:

```
Step 2: resolver-level authorization parity
`Query.ticket` checks `ticket.org_id != info.context.user.org_id` before
returning the record. `Subscription.ticket_updated` has no equivalent
check anywhere — it subscribes to `pubsub.subscribe(f"ticket:{ticket_id}")`
using only the client-supplied `ticket_id` argument, and yields whatever
the pub/sub channel publishes with zero reference to who's connected. Any
client that knows or guesses a `ticket_id` can open this subscription and
receive every update to that ticket, regardless of `org_id` — the same
field, same underlying record, materially weaker check than the query
sitting right next to it in the same file.
```

Step 3 checks whether a rejected connection would even stop delivery:

```
Step 3: enforcement on failure
Moot here since there's no check to fail — there's no code path that
would reject or disconnect based on authorization at all, so nothing to
verify "logs but doesn't block."
```

Report:

```
## subscription-guard review: schema.py

1. `Subscription.ticket_updated` has no authorization check at all,
   while `Query.ticket` on the same type enforces `org_id` ownership
   (BLOCK — confirmed bypass: a client can receive live updates for any
   ticket by guessing or harvesting a `ticket_id`, with no org check).

2. No `on_ws_connect` hook is registered for either the modern or legacy
   subscription subprotocol, so `info.context` carries no authenticated
   user for subscriptions to check against even if the per-field check
   above were added (BLOCK, root cause: this is why #1 has nothing to
   check against).

## Verdict: BLOCK
The subscription transport authenticates nobody, and the one subscription
field skips the org-ownership check its sibling query enforces — any
client that knows a ticket_id gets a live feed of a ticket that isn't
theirs. Fix: add an `on_ws_connect` hook that authenticates the same way
the HTTP transport does (shared session, or a verified-signature token via
`connectionParams`), thread the authenticated user into `info.context` for
subscriptions the same as for queries, and add the same `org_id` check to
`ticket_updated` that `Query.ticket` already has — re-checked per event if
access can be revoked while the subscription stays open, not just once at
subscribe time.
```
