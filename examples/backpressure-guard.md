# backpressure-guard — example

**Trigger:**

> the ops dashboard freezes for everyone whenever one admin's laptop goes to
> sleep with the tab open, and last week the server OOM-crashed after being
> up for four days with a couple of stale tabs left open. here's the
> broadcast code:
>
> ```js
> // server: broadcastMetrics.js
> const subscribers = new Set(); // one WebSocket per connected dashboard
>
> function broadcastMetrics(snapshot) {
>   const payload = JSON.stringify(snapshot);
>   for (const ws of subscribers) {
>     ws.send(payload);
>   }
> }
>
> setInterval(() => broadcastMetrics(collectSnapshot()), 1000);
>
> wss.on('connection', (ws) => {
>   subscribers.add(ws);
>   ws.on('close', () => subscribers.delete(ws));
> });
> ```
>
> ```js
> // server: ackTracking.js — used for admin actions that need confirmation
> const pendingAcks = new Map(); // ackId -> { ws, sentAt }
>
> function sendWithAck(ws, event) {
>   const ackId = uuid();
>   pendingAcks.set(ackId, { ws, sentAt: Date.now() });
>   ws.send(JSON.stringify({ ackId, event }));
> }
>
> wss.on('message', (ws, raw) => {
>   const { ackReceiptFor } = JSON.parse(raw);
>   if (ackReceiptFor) pendingAcks.delete(ackReceiptFor);
> });
> ```

**Response shape:**

Step 1 finds the two fan-out paths:

```
Step 1: fan-out loops
`broadcastMetrics` runs every second and does `for (const ws of
subscribers) ws.send(payload)` — the main dashboard fan-out, feeding every
connected admin's live metrics view. `sendWithAck` is a second, narrower
fan-out used for admin actions that need per-client confirmation, called
once per targeted admin rather than in a loop over all subscribers.
```

Step 2 checks whether one connection can stall the others:

```
Step 2: isolation between connections
`broadcastMetrics`'s loop is a plain synchronous `for` with no
per-connection isolation — `ws.send()` for one subscriber is called, then
the next, then the next, in iteration order. If one socket's underlying
write can't complete immediately (the classic case: a laptop asleep with
the TCP connection still technically open, not yet timed out), that
`send()` call queues into the socket's internal buffer and the loop moves
to the next iteration — but with no `bufferedAmount` check anywhere, nothing
distinguishes "queued because momentarily busy" from "queued because this
socket is never going to drain." Under Node's event loop, enough backed-up
writes across enough stalled sockets is consistent with the reported
freeze: not every send blocks synchronously, but nothing here prevents one
non-draining socket's buffer from growing on every single tick.
```

Step 3 checks whether the per-connection outbound state is bounded:

```
Step 3: bounded or not
`broadcastMetrics` never checks `ws.bufferedAmount` before calling `.send()`
— there is no cap on how much can queue for one socket. Worse is
`pendingAcks`: it's a plain `Map`, and grepping the codebase for
`pendingAcks.delete` finds exactly one call site — inside the `message`
handler that fires when a client sends back `ackReceiptFor`. If a client
never sends that message (the same asleep-laptop scenario, or any admin who
just closes their laptop lid without the socket cleanly closing first),
nothing ever deletes that entry. `subscribers` at least gets pruned on
`ws.on('close', ...)` — but `pendingAcks` has no equivalent, and a `close`
event isn't even guaranteed to fire promptly for a socket that's merely
stalled rather than explicitly closed.
```

Step 4 checks for any other reclaim path:

```
Step 4: reclaim path
There isn't one for `pendingAcks`. No timeout is set when an entry is
created, no interval sweeps stale entries by `sentAt` age, and the only
delete path requires a message from the same client that's already failed
to respond. Every admin action sent to a stalled dashboard adds one
permanent entry. Four days of uptime with "a couple of stale tabs" is
exactly enough admin-action volume to reach the kind of unbounded growth
that matches socket.io's own measured case (500 stalled acks climbing to
1.5GB over 3 hours before their fix) — the same shape, smaller fleet,
longer runway, same ending.
```

Report:

```
## backpressure-guard review: broadcastMetrics.js / ackTracking.js

1. `pendingAcks` grows by one entry per admin action sent to a client that
   never acks, with no timeout or disconnect-triggered cleanup reachable
   from anywhere but a response that may never come (BLOCK — this is the
   OOM crash's most likely direct cause): a handful of stale tabs left open
   across days of uptime is sufficient to exhaust memory, matching the
   observed crash after four days up.

2. `broadcastMetrics`'s fan-out loop has no per-connection isolation and no
   `bufferedAmount` check before queuing a send (BLOCK, separate from #1):
   a stalled subscriber's socket can accumulate unbounded queued writes,
   and nothing in the loop treats "not draining" differently from
   "momentarily busy" — consistent with the reported freeze whenever one
   admin's laptop sleeps.

3. `subscribers` is correctly pruned on `close` (SAFE, noted so the fix
   doesn't also touch what already works) — but a stalled-not-closed socket
   never reaches that handler, so it doesn't protect against either finding
   above.

## Verdict: BLOCK
Two independent unbounded-growth paths share one root cause: nothing on
either the metrics broadcast or the ack-tracking path distinguishes a
client that's merely busy from one that has stopped draining entirely, and
neither ever times out or gets forcibly disconnected. Fix: add a
`ws.bufferedAmount` (or platform equivalent) check before each broadcast
send, and drop-or-disconnect any socket over a stated threshold instead of
queuing indefinitely; set a timeout on each `pendingAcks` entry that
deletes it (and closes the offending connection) if no ack arrives within a
bounded window, mirroring the fix socket.io shipped for the identical
shape in socket.io@4.8.4.
```
