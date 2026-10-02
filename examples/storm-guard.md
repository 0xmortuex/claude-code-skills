# storm-guard — example

**Trigger:**

> we're doing a rolling deploy of the realtime service tonight — about 50k
> clients connected. someone asked "what happens when they all reconnect at
> once" and I don't actually know. here's the client and server code:
>
> ```js
> // client: realtimeClient.js
> ws.onclose = () => {
>   setTimeout(() => connect(), 3000); // reconnect after 3s
> };
> ```
>
> ```js
> // server: wsServer.js
> wss.on('connection', async (ws, req) => {
>   const token = getTokenFromRequest(req);
>   const session = await db.query(
>     'SELECT * FROM sessions WHERE token = $1', [token]
>   );
>   const user = await authService.validate(session.user_id);
>   const state = await hydrateFullState(user.id); // builds the initial payload
>   ws.send(JSON.stringify(state));
> });
> ```

**Response shape:**

Step 1 finds the reconnect trigger and confirms disconnects are already synchronized:

```
Step 1: reconnect trigger and synchronization
The client reconnects via `ws.onclose`. The disconnect side is the rolling
deploy itself: cycling the realtime service's pods closes every socket a
replaced pod was holding within the deploy window, which for 50k clients
across however many pods is not a scattered, independent set of
disconnects — it's a batch, on a timetable you control tonight.
```

Step 2 checks whether the reconnect delay decorrelates the fleet:

```
Step 2: jitter
`setTimeout(() => connect(), 3000)` is a fixed constant — every client that
disconnects in the same deploy wave reconnects at the same instant, 3
seconds later, with zero randomization. This is the textbook unjittered
case: the deploy doesn't just risk a reconnect storm, the code guarantees
one by re-synchronizing everyone to the same retry moment.
```

Step 3 checks the per-connection cost and whether anything shields the backend:

```
Step 3: backend cost at fleet scale
Every accepted connection does three sequential round trips before the
client gets its first message: a `sessions` table lookup, an external
`authService.validate` call, and a `hydrateFullState` query. None of these
are cached or rate-limited anywhere in this file or its imports. At 50k
clients reconnecting inside the same post-3s window, that's ~50k
simultaneous session-table queries, ~50k simultaneous calls to the auth
service, and ~50k full-state hydration queries — a multiplier on every one
of three dependencies at once, not spread out at all.
```

Step 4 checks whether this has actually been tested:

```
Step 4: tested or assumed
No load test, game-day exercise, or deploy runbook mentioning auth/DB
monitoring during rollout was found in the repo or linked docs. The only
mitigation that exists is the 3-second `setTimeout` — which step 2 already
showed doesn't mitigate anything.
```

Report:

```
## storm-guard review: realtimeClient.js / wsServer.js — tonight's rolling deploy

1. Reconnect delay is a fixed 3000ms constant with no jitter (BLOCK): every
   client disconnected by a cycling pod reconnects in lockstep 3 seconds
   later. Fix before tonight: full jitter — `Math.random() * CAP_MS` (or
   standard exponential-backoff-with-jitter) recomputed on every attempt,
   not a shared constant.

2. The connection handler does three uncached, unshielded round trips
   (session-table query, auth-service call, full-state hydration) before
   sending the first message (BLOCK, compounds #1): with #1 unfixed, this
   is ~50k simultaneous hits to all three dependencies in the same
   sub-second window. Even with #1 fixed, this is still the thing that
   decides whether a *spread-out* jitter window is actually wide enough —
   it isn't shielded by anything today.

3. No evidence this path has been load-tested or watched during a prior
   deploy (CAUTION, separate from the two BLOCKs above): "we have backoff"
   was the operator's only basis for confidence before this review, and
   step 2 shows that basis doesn't hold.

## Verdict: BLOCK
Two independent, compounding problems — reconnects are synchronized by
design (no jitter) and the per-connection cost is real and unshielded —
describe exactly the thundering-herd mechanism behind Discord's March 2026
voice outage and the reason Slack built Flannel rather than letting
reconnects hit its databases directly. Do not run tonight's deploy as
planned. Minimum fix before deploying: add full jitter to the reconnect
delay, and either cache the session/auth lookup or rate-limit the
connection-accept path so 50k near-simultaneous reconnects don't become
50k near-simultaneous queries against the same three dependencies. If
tonight's deploy can't wait for the backend fix, consider cycling pods in
smaller batches over a longer window instead of all at once, so the
client-side disconnect — and therefore the reconnect wave — is spread out
even with today's code.
```
