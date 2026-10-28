# throttle-guard — example

**Trigger:**

> we rate-limit password reset requests to 10/minute per IP to stop
> enumeration, but someone just hammered it with way more than 10/minute
> and we don't know how. we run 5 instances behind our load balancer. here's
> the limiter:
>
> ```js
> // rateLimiter.js
> const buckets = new Map(); // ip -> { count, resetAt }
>
> function checkLimit(ip) {
>   const now = Date.now();
>   const bucket = buckets.get(ip);
>   if (!bucket || now > bucket.resetAt) {
>     buckets.set(ip, { count: 1, resetAt: now + 60_000 });
>     return true;
>   }
>   if (bucket.count >= 10) return false;
>   bucket.count++;
>   return true;
> }
>
> app.post('/password-reset', (req, res) => {
>   if (!checkLimit(req.ip)) return res.status(429).end();
>   return sendResetEmail(req.body.email);
> });
> ```
>
> ```js
> // workers/bulkResend.js — added last quarter for the "resend to all
> // pending resets" admin tool
> async function resendPendingResets() {
>   const pending = await db.passwordResets.findPending();
>   for (const reset of pending) {
>     await sendResetEmail(reset.email); // bypasses rateLimiter.js entirely
>   }
> }
> ```

**Response shape:**

Step 1 finds the actual bug immediately — `buckets` is a plain in-process `Map`:

```
Step 1: per-instance state
`buckets` is a module-level Map — in-process memory, not a shared store.
With 5 instances behind the load balancer, each one independently allows
10/minute from a given IP against whatever slice of that IP's requests it
personally receives. The real aggregate limit an attacker experiences is
up to 50/minute (5 instances × 10), not 10 — and it varies run to run
depending on the load balancer's routing and which instances happen to be
healthy. This fully explains "way more than 10/minute got through" without
needing any other bug.
```

Step 2 is moot given Step 1's finding (no shared store exists yet to check
for atomicity), noted as the next thing to get right once Step 1 is fixed —
flags that a naive migration straight to Redis via `GET` + `SET` would
reopen the same race one layer out.

Step 3 finds a second, independent bypass:

```
Step 3: paths that skip the limiter
`resendPendingResets` in workers/bulkResend.js calls `sendResetEmail`
directly and never calls `checkLimit` at all — it isn't reimplementing the
limit with a drifted copy, it simply doesn't rate-limit. This path runs
outside the HTTP request cycle entirely (a background job), so even a
correctly-fixed Step 1/2 limiter sitting in the Express route wouldn't
cover it. Any email-enumeration or email-bombing concern the 10/minute
limit exists for is fully exposed through this admin tool.
```

Report:

```
## throttle-guard review: password-reset rate limit, 5-instance deploy

1. `checkLimit`'s `buckets` Map is per-process. Across 5 instances the
   configured "10/minute per IP" is actually "up to 50/minute per IP,
   nondeterministically" — this is the incident (BLOCK — move the counter
   to a shared store).

2. Moving to Redis needs an atomic op from day one: a bare `GET` then
   `SET` would just relocate Step 1's race rather than closing it. Use
   `INCR` + `EXPIRE NX` (set the TTL only on the first increment in the
   window) or a Lua script, not read-compare-write in application code
   (BLOCK as part of the same fix — don't ship a shared counter that's
   still non-atomic).

3. `workers/bulkResend.js` sends reset emails with zero rate limiting —
   a separate, legitimate code path that was simply never wired to
   `checkLimit` (BLOCK — same root cause as #1: nothing told the author of
   this background job a limit existed to call).

## Verdict: BLOCK
Replace the in-process `Map` with an atomic Redis `INCR`/`EXPIRE` keyed on
IP, decide and document fail-open vs. fail-closed behavior if Redis is
unreachable, and call the same shared check from `bulkResend.js` before
sending. Until all three land, the 10/minute password-reset limit is
enforced in name only.
```
