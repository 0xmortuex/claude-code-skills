---
name: blast-guard
description: Review code that emails, texts, or pushes a real user audience — a campaign send, a notification job, a "notify affected users" script — for mistakes that only surface once messages have landed, because a send has no rollback. Checks the audience query for the join/filter that silently widens or narrows it, requires a dry-run count and sample before anything sends, verifies suppression lists (unsubscribe, hard-bounce, frequency cap) are consulted, confirms which provider/environment the send is bound to, and demands a resumable stop mechanism with per-recipient idempotency. Use when you or the user writes or reviews code that will message more than one real person: "email everyone who...", "notify all users in this segment", "bulk send", "mailing list blast", "push notification to our users", or before any script whose output is "sent N messages". Distinct from job-warden (duplicate-run correctness) and backfill-pilot (data mutation) — this is the gate for the one production mistake with no undo.
---

# blast-guard

A bad migration can be rolled back. A bad backfill can be re-run with a fix. A bad send cannot: the moment the loop starts, messages land in real inboxes, on real phones, in real chat channels, and there is no `UNDO`. The two ways this goes wrong in practice are almost never "the send code has a bug" — it's "the code that decided *who* to send to was wrong" and "there was no way to stop it once it started." A staging push token pointed at a production app has sent a "test" notification to tens of thousands of real users; a birth-announcement congratulations email built from a customer segment that was one filter too wide has gone out to people who'd just had a miscarriage. Neither team had a code bug in the message template. They had no dry-run gate on the audience, and no way to catch it before send.

This review runs *before* the send executes, not after someone screenshots the result.

## Classify the send first

- **Transactional** (one recipient, triggered by that user's own action — a password reset, an order confirmation): normal code review is enough. Skip the ceremony below, but still confirm it can't fire twice for one action (that's job-warden's territory if it's retried).
- **Bulk / campaign / broadcast** (a query decides the recipient list, or the loop's whole job is "message N people"): everything below applies, scaled to N. A `for user in User.objects.filter(...)` that mails each one is bulk, however innocent the loop looks.

If you can't tell which it is, treat it as bulk — the cost of extra ceremony on a small send is minutes; the cost of skipping it on a big one is unrecoverable.

## What to check, in order

**1. Is the audience query provably right?**
Never trust the query by reading it — run it read-only first. Get a `COUNT(*)` and compare it to what the person expected ("about 200 affected users" vs. a query that returns 40,000 is the whole bug, caught before it fires). Pull a sample of 15–20 rows with the identifying fields (email, name, plan) and eyeball them: is this who they meant? The classic ways an audience query lies: a `NOT`/`LEFT JOIN ... IS NULL` that inverts silently when a row is unexpectedly null, soft-deleted or test/internal accounts not excluded, a JOIN fan-out that duplicates recipients, a staging seed script pointed at a database that also holds real users, or a "recently X" filter with no upper bound so it also catches everyone from years ago.

**2. Does the send actually consult suppression state, not just intend to?**
Four checks that need to be live code, not a comment saying they matter: the unsubscribe/opt-out list, the hard-bounce list (mailing a hard-bounced address repeatedly tanks sender reputation for everyone), a per-user frequency cap (don't re-notify someone who got the same message an hour ago because the job restarted), and quiet-hours/timezone if the message isn't urgent (ties into clock-sweep if the zone handling itself looks wrong). "We check that at signup" is not the same as checking it at send time.

**3. Which environment and provider is this send actually bound to?**
Assert it at runtime, don't trust the config file: which API key is live (test/sandbox vs. production), which `from`/reply-to domain, which provider account. The staging-token-in-production failure mode is exactly a send that "looked" configured for staging in the code but was wired to the live key at deploy time — verify the binding the send will actually use, not the one the code intends.

**4. Can this be stopped, and does stopping mean anything?**
Before the loop starts, there must be a hard ceiling that aborts rather than "logs a warning and continues," and the send must be batched with a checkpoint so a stop is resumable from where it left off — not a restart-from-zero that re-sends everyone already messaged. That resumability only works if each recipient's send is idempotent (a dedup key, or a "did we already send this campaign to this user" check) — otherwise "resume" and "duplicate everyone in the first batch" are the same code path. If nobody can answer "how do we stop this at recipient 4,000 of 60,000, and what happens to the 4,000 who already got it," the send isn't ready.

## Report

Verdict per check, evidence-cited, scaled to the send's size:

```
## send: winback-campaign-2026-08
1. Audience query: FAIL — COUNT(*) returned 41,200, author expected ~3,000.
   The `WHERE last_login < NOW() - INTERVAL '90 days'` has no upper bound
   and no `deleted_at IS NULL` filter — catches every stale/deleted account
   since signup. Sample of 20 includes 6 accounts marked deleted.
2. Suppression: FAIL — unsubscribe table exists but query never joins it.
3. Environment: OK — asserted SENDGRID_ENV=production intentionally, this
   campaign is meant to go live.
4. Stop mechanism: FAIL — single unbatched loop, no checkpoint, no cap.
   A crash at recipient 20,000 leaves no record of who was already sent.
```

Skip ceremony honestly for genuinely small sends (a 12-person internal alert) — say that's what you're doing — but the audience-query sanity check (1) and the stop mechanism (4) still apply at any size, because "small" is exactly what a wrong query claims to be until you count it.

## Boundaries

- This is not a legal/compliance review — CAN-SPAM, GDPR consent basis, TCPA for SMS are a separate check this skill doesn't own. Flag if consent tracking looks obviously absent, but don't claim compliance clearance.
- Doesn't replace job-warden: if the send is also a recurring job, job-warden's overlap/schedule/dead-man's-switch questions still apply — run both.
- Doesn't replace backfill-pilot: a send that also mutates a "notified_at" column on millions of rows needs backfill-pilot's batching/throttle discipline on top of this skill's audience/suppression checks.
- If the send already happened before this review runs, this skill can't undo it — say so plainly and shift to incident response (identify who received it, whether a correction/apology send is warranted, and what would have caught it).
