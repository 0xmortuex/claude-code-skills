# resync-guard — example

**Trigger:**

> support agents keep saying tickets "disappear" — a new one gets assigned
> to them but doesn't show up in the queue until they manually refresh the
> page. happens most on flaky office wifi. here's the queue code:
>
> ```js
> // client: TicketQueue.jsx
> useEffect(() => {
>   fetch('/api/tickets?assignee=me').then(r => r.json()).then(setTickets);
>
>   function connect() {
>     const ws = new WebSocket(WS_URL);
>     ws.onmessage = (event) => {
>       const msg = JSON.parse(event.data);
>       if (msg.type === 'ticket_assigned') {
>         setTickets((prev) => [...prev, msg.ticket]);
>       }
>     };
>     ws.onclose = () => {
>       setTimeout(connect, 1000 + Math.random() * 2000);
>     };
>     return ws;
>   }
>   const ws = connect();
>   return () => ws.close();
> }, []);
> ```
>
> ```js
> // server: broadcastTicketAssigned.js
> function assignTicket(ticket, agentId) {
>   db.tickets.update(ticket.id, { assignee: agentId });
>   const socket = liveConnections.get(agentId);
>   if (socket) socket.send(JSON.stringify({ type: 'ticket_assigned', ticket }));
>   // fire-and-forget: no queue, no log, nothing kept if the agent isn't connected
> }
> ```

**Response shape:**

Step 1 finds the queue is fed by the stream alone, with no self-healing refresh:

```
Step 1: what's stream-only
The initial `fetch('/api/tickets?assignee=me')` runs once on mount and
populates `tickets`. After that, the *only* code path that ever adds a
ticket to state is the `onmessage` handler for `ticket_assigned`. There's
no polling, no re-fetch on window focus, no periodic refresh — an agent
who stays on the page for their whole shift never gets another full
resync unless they manually reload. This is exactly the state class
where a missed push is a standing bug, not a transient delay.
```

Step 2 checks the reconnect handler itself:

```
Step 2: reconnect handling
`onclose` schedules a plain `connect()` retry with jittered backoff —
correct transport behavior. But `connect()` only re-opens the socket and
re-attaches `onmessage`; nothing in the reconnect path re-fetches
`/api/tickets` or asks the server for anything assigned during the gap.
Reconnect resumes the live stream and treats existing `tickets` state as
still complete.
```

Step 3 checks whether any resume mechanism exists to close the gap:

```
Step 3: resume mechanism
There isn't one, on either side. The client sends no cursor, sequence
number, or Last-Event-ID-equivalent on reconnect. The server's
`assignTicket` only sends if `liveConnections.get(agentId)` finds a
currently-open socket — if the agent was mid-reconnect (or their old
socket hadn't been pruned yet) when the assignment happened, the event
is sent nowhere, kept nowhere, and gone. There's no queue or log behind
the send, so even a resume request from the client would have nothing
to replay from — this needs a server-side fix (persist or queue
undelivered assignment events per agent), not just a client-side one.
```

Step 4 checks whether the agent gets any signal that something might be missing:

```
Step 4: visibility
No reconnect indicator, no "you may have missed updates" banner, nothing
distinguishing a clean session from one that dropped and silently lost
an assignment. The queue looks exactly as complete after a missed event
as it did before — which matches the bug report exactly: agents don't
know to refresh because nothing tells them they should.
```

Report:

```
## resync-guard review: TicketQueue.jsx / broadcastTicketAssigned.js

1. Ticket state is fed only by the WebSocket stream, with no periodic or
   focus-triggered re-fetch (BLOCK — confirmed root cause combined with
   #2 and #3): a missed `ticket_assigned` event has no other path to
   ever reach this agent's queue.

2. Reconnect only re-opens the socket; it never re-syncs ticket state
   (BLOCK, same root cause): `connect()` treats "socket reopened" as
   "state current," which is exactly backwards during the reconnect
   window this bug happens in.

3. The server sends assignment events fire-and-forget to whatever socket
   is registered at that instant, with no queue or log behind it (BLOCK
   — this is the actual data-loss point): if the agent's socket isn't
   live at the moment of assignment, the event doesn't exist anywhere
   afterward for any resync mechanism to recover, however good the
   client gets.

4. No UI signal on reconnect (CAUTION, compounds the above): even once
   1–3 are fixed for new events, there's nothing today telling an agent
   a gap might have happened, so a partial fix that narrows but doesn't
   eliminate the window would still fail silently.

## Verdict: BLOCK
The queue is fed exclusively by a live stream with no resync step on
reconnect, and the server-side send is fire-and-forget with nothing kept
for a client that reconnects moments too late — so a ticket assigned
during any connection gap is lost, not delayed, with no signal to the
agent that it happened. Fix needs both ends: persist or queue
per-agent assignment events server-side (even a short-TTL outbox closes
most real-world blips), and have the client's reconnect path explicitly
resync (re-fetch `/api/tickets` or drain the queued events) before
trusting the live stream again.
```
