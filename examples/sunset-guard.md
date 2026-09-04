# sunset-guard — example

**Trigger:**

> we announced the /v1/payments sunset back in July with a 90-day notice per
> our API policy, and the `Sunset` header's been live since then. removal
> date is October 1, that's next week. can you check we're actually clear to
> flip the switch and start returning errors for v1 calls? here's the
> relevant code:
>
> ```python
> # api/v1/payments.py
> SUNSET_DATE = "2026-10-01"
>
> @app.route("/v1/payments", methods=["POST"])
> def create_payment_v1():
>     resp = _create_payment(request.json)
>     resp.headers["Sunset"] = SUNSET_DATE
>     resp.headers["Deprecation"] = "true"
>     return resp
>
> @app.route("/v1/payments/bulk", methods=["POST"])
> def create_payment_bulk_v1():
>     # legacy partner batch endpoint, same v1 schema
>     return _create_payments_bulk(request.json)
>
> # webhooks/retry_worker.py
> def replay_failed_webhook(event):
>     # replays in whatever API version the event was originally recorded in
>     if event.api_version == "v1":
>         return _create_payment(event.payload)  # calls the same internal
>                                                  # function, bypassing the
>                                                  # route entirely
>
> # ops/sunset_v1.py — the script that'll run next week
> def remove_v1():
>     if date.today() >= date.fromisoformat(SUNSET_DATE):
>         app.url_map.remove_rule("/v1/payments")
>         app.url_map.remove_rule("/v1/payments/bulk")
> ```

**Response shape:**

Step 1 walks every path that reaches the deprecated version, not just the
one carrying the header:

```
Step 1: serving paths for v1

- POST /v1/payments (create_payment_v1) — carries Sunset + Deprecation
  headers. Covered.
- POST /v1/payments/bulk (create_payment_bulk_v1) — same v1 payment schema,
  used by the partner SDK's batch mode, but the handler calls
  _create_payments_bulk directly and sets no headers at all. A partner
  polling this route for a Sunset header (which is the documented way to
  discover the cutover) sees nothing and has no signal anything is changing.
- webhooks/retry_worker.py::replay_failed_webhook — calls the internal
  _create_payment() function directly for v1 events, bypassing the route
  (and its headers) entirely. Not caller-facing in the same way, but still
  a live v1 code path the removal script doesn't account for.

Two of three paths that serve v1 behavior carry no notice at all.
```

Step 2 checks whether the enforced window actually matches the 90-day
policy the trigger message claims:

```
Step 2: notice window vs. promised policy

`git log -p api/v1/payments.py` for the Deprecation/Sunset header lines:
they were added in a commit from August 28, not July — six weeks before the
October 1 removal date, not the 90 days (~13 weeks) the announcement and
stated policy promise. The public blog post and changelog entry are dated
July 2, but the code enforcing the actual signal (the header a client
library would check) only started six weeks ago. Anyone relying on the
header rather than the blog post got roughly a third of the promised
notice. FAIL — the enforced window doesn't match the promised one.
```

Step 3 checks whether removal is gated on real usage or purely the
calendar:

```
Step 3: usage gate

ops/sunset_v1.py::remove_v1 has exactly one condition: today's date. No
query against request logs, metrics, or an allowlist of already-migrated
callers before removing the routes. Pulled the last 7 days of access logs
for both v1 routes to check what removal would actually break:

- POST /v1/payments: ~40 req/day, trending toward zero — mostly retries
  from a couple of stragglers.
- POST /v1/payments/bulk: ~18,000 req/day, flat, no downward trend. This
  is the same route step 1 found with no headers at all. A partner
  integration is still sending real production volume here and, per step
  1, has never been told to stop.

Removal as written on October 1 would cut off a partner still doing
18k requests/day with zero warning, because the traffic is real, the
notice never reached them, and the removal script doesn't check traffic
before acting either way.
```

Step 4 traces what a still-calling client experiences after the routes are
removed, since `remove_v1()` doesn't add a replacement handler:

```
Step 4: post-cutover behavior

`app.url_map.remove_rule(...)` deletes the route entirely with no
replacement registered at the same path. A request to either URL after
removal falls through to Flask's default 404 handler — no `Sunset`
correlation, no `Link` header to the v2 migration guide, indistinguishable
from a typo'd URL or a route that never existed. The retry worker's direct
function call in webhooks/retry_worker.py doesn't go through the route at
all, so it wouldn't even 404 — it would keep calling `_create_payment`
successfully forever, since removing a Flask route doesn't touch the
underlying function. Worst of the four failure modes checked isn't in
play here (no silent behavior change), but neither is the best one: this
is a bare 404, not a 410 with a migration `Link`, and one call path
(the retry worker) doesn't get cut off at all.
```

Report matches the skill's worst-first ordering:

```
## sunset-guard review: /v1/payments sunset (target: 2026-10-01)

1. Bulk route has no notice and real traffic (BLOCK): /v1/payments/bulk
   carries no Sunset/Deprecation header and is doing ~18k req/day with no
   downward trend — a partner integration that's never been told this is
   going away. Removing it on schedule breaks a live integration with zero
   warning. Add the same headers this week and do not remove until traffic
   drops or the partner confirms migration.

2. Enforced notice window is ~6 weeks, not the promised 90 days (BLOCK):
   the header only started shipping August 28, six weeks before the
   October 1 date, despite the July 2 public announcement. Either push the
   removal date out to honor the full 90 days from when the header
   actually went live, or explicitly accept and document that the header
   is not the source of truth for this window (risky, since it's the one
   signal a client library can check programmatically).

3. No usage gate on removal (CAUTION, compounds finding 1): remove_v1()
   only checks the date. Add a traffic check (e.g. block removal if
   requests in the last 7 days exceed a threshold) so a date arriving
   can't silently remove a route still under active load — this is what
   would have caught finding 1 even without a manual audit.

4. Post-cutover response is a bare 404, not a 410 + migration Link
   (CAUTION): a client hitting either route after removal gets nothing
   distinguishing "sunset on purpose" from "URL typo." Register a
   catch-all handler at both paths that returns 410 with a `Link` header
   to the v2 migration doc before removing the real routes.

5. Retry worker bypasses the route entirely (CAUTION): replay_failed_webhook
   calls `_create_payment` directly for v1 events and isn't touched by
   removing the Flask routes — it will keep running v1 logic indefinitely
   unless it's updated separately to reject or convert v1 events.

## Verdict: BLOCK
Do not run remove_v1() on October 1 as written. Finding 1 alone is
disqualifying — a partner doing real production volume through
/v1/payments/bulk has never received any signal this is being removed.
Fix findings 1 and 2 first (header coverage and an honest notice window),
then land findings 3 and 4 so the next sunset doesn't repeat this — the
usage gate in particular would have caught the traffic gap automatically
instead of needing a manual audit to surface it.
```
