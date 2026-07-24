---
name: job-warden
description: Review background jobs, cron tasks, queue consumers, and workers for the correctness properties that only fail in production — non-idempotent handlers under at-least-once delivery, overlapping runs, DST-unsafe schedules, retry storms, poison messages, and jobs that die silently for weeks. Use when the user writes or shows a scheduled job / worker / consumer ("add a cron job", "process this queue", "runs nightly"), debugs one behaving strangely (duplicates, missed runs, pile-ups), or asks "is this job production-ready". Apply it to your OWN output too: any job code you write gets this review before it ships.
---

# job-warden

Request handlers get reviewed, tested, and watched by users who complain when they break. Background jobs get none of that: they run alone at 3am, their failure modes are invisible until the duplicate charges / missing emails / three-week-old data surface, and the platform guarantees (at-least-once delivery, missed-schedule behavior) are exactly where developer intuition is wrong. This review asks the six questions that catch nearly all of it.

## The six questions

**1. What happens if this runs twice with the same input?**
It will. At-least-once delivery is the norm (SQS, Pub/Sub, Sidekiq/Celery retries, k8s job restarts); a worker that crashes after the side effect but before the ack replays the side effect. Every handler needs one of: natural idempotency (`SET status='sent'` is safe; `balance += x` is not), a dedup key checked-and-recorded transactionally with the work, or an idempotency key passed to the downstream API (payments especially). "It won't retry because it succeeded" is not one of the options — say which mechanism holds, per side effect.

**2. What happens when a run outlives its interval?**
The nightly job that starts taking 25 hours, the every-minute poller hitting a slow API — now two instances run concurrently, competing for the same rows. Check for overlap protection: a lease/lock (DB advisory lock, Redis `SET NX PX`, the scheduler's own `concurrencyPolicy: Forbid`) with a TTL longer than the worst run, plus a decision on the follow-up: skip the overlapped run or queue one, and who's told.

**3. Is the schedule itself lying?**
- Cron in a DST zone: `0 2 * * *` runs twice one night a year and zero times another; daily jobs belong in UTC or at DST-immune hours.
- Whose clock? The scheduler's timezone (system TZ, k8s cluster, cloud console setting) vs the one the author assumed.
- Missed runs: machine asleep/redeploying at the scheduled minute — does this scheduler catch up (anacron-style) or silently skip, and does the job's logic tolerate whichever it is? A "daily" report job that skips a day must backfill it or the gap is forever.
- Thundering herd: everything at `0 0 * * *` — stagger or jitter if the jobs share a database.

**4. What happens to the message that always fails?**
A poison message (malformed payload, deleted user, edge case) with naive retry blocks the queue or burns CPU forever. Required: bounded retries with exponential backoff + jitter, then quarantine to a dead-letter queue that a human actually reviews. Distinguish retryable (timeout, 429, 5xx) from permanent (validation, 404) failures — retrying a permanent failure five times with backoff is five times slower to reach the same DLQ.

**5. Is a batch all-or-nothing on purpose?**
Item 372 of 1000 throws: does the whole batch abort (999 items silently unprocessed), or is the failure recorded per-item and the batch continues? Either can be right; unexamined is wrong. Watch the transaction scope: one transaction around the whole batch turns question 5 back into question 1 on retry.

**6. Who notices when it stops running entirely?**
The deadliest failure is silence: the worker OOMed, the cron entry was lost in a migration, the queue binding was deleted — and nothing happened, *including alerts*, because alerting was wired to failures, not absence. Every scheduled job needs a dead-man's-switch: a heartbeat ping (healthchecks.io-style), a "last successful run" timestamp with an alert on staleness, or a metric with an absence alarm. "We'd notice eventually" — how, and after how much silent data loss?

## Report

Verdict per question, evidence-cited, fixes concrete:

```
## job: nightly-invoice-sync
1. Idempotency: FAIL — `stripe.charges.create` has no idempotency_key;
   a retry after network timeout double-charges. Pass the invoice id.
2. Overlap: OK — pg advisory lock 41, TTL n/a (lock released on close).
3. Schedule: RISK — '0 2 * * *' in Europe/Istanbul; runs 0x/2x on DST
   nights. Move to UTC.
...
6. Liveness: FAIL — no heartbeat; if the container stops, nothing alerts.
```

Skip ceremony for tiny jobs honestly: a cache-warmer that's harmlessly rerunnable and harmlessly skippable can pass 1–5 in a sentence — but question 6 applies to *every* job, including that one.

## Boundaries

- One-off production data operations (the big backfill script) → backfill-pilot; this skill owns *recurring* jobs and consumers.
- Schedule/timezone findings that extend into general datetime handling in the job's business logic → clock-sweep for the full audit.
- Don't demand distributed-locks-and-DLQs from a single-user hobby script cron'd on a laptop — scale the ceremony to the blast radius, and say that's what you're doing. Questions 1 and 6 still get answered.
