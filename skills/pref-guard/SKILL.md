---
name: pref-guard
description: Audit whether an ongoing notification system actually honors what a user chose — per-channel opt-outs (email/push/SMS/in-app), category-level preferences ("product updates" off but "security alerts" on), suppression lists, and frequency caps — over time, as new send paths and notification types get added. Distinct from blast-guard, which reviews a single bulk send at send time (audience query, dry run, stop mechanism); this skill reviews the standing system: does every current and future send path check live preference state, does provider-side unsubscribe/bounce data actually reach the app's suppression record, and does opt-out granularity match what the user was shown. Use when a user reports "I unsubscribed but still got an email", when adding a new notification type or channel, when reviewing a preference center or suppression-list implementation, or when asked "do we actually respect opt-outs", "audit our notification preferences", or "frequency cap".
---

# pref-guard

A suppression list is not a fact about the world — it's a copy of one, and copies drift. The bug this skill exists to catch is never "the unsubscribe button is broken" (that fails immediately and gets caught in five minutes of testing). It's the notification that fires eight months later, from a send path nobody was thinking about when the preference center shipped: a new "product update" category launches and its send loop checks `users.marketing_opt_out` instead of the per-category table added since; a provider's own one-click unsubscribe link (required by CAN-SPAM/RFC 8058) suppresses the user *at the provider*, but the webhook that's supposed to sync that back to the app's database silently stopped firing three deploys ago, so the app keeps queuing sends the provider quietly drops — until someone switches providers and the suppression state doesn't come with it. Each of these reads as "the code was correct when written." The system drifted around it.

This is a standing correctness property, not a one-time check — closer in shape to `stale-guard` (does every write path keep a copy in sync) than to `blast-guard` (is this one send safe to fire). Audit it the same way: enumerate every place a notification can originate, then prove two invariants.

## Step 1: enumerate every send path and every preference dimension

List every place code can trigger a notification: transactional (password reset, order confirmation), lifecycle/marketing campaigns, digests and cron summaries, real-time alerts, in-app + push + email + SMS variants of the "same" notification. Don't stop at the primary service — a growth team's separate campaign tool, a support platform's auto-replies, and a data-pipeline-triggered digest often write to the same users through completely different code, each with its own idea of what "opted out" means.

Then list every dimension a preference can vary on: **channel** (email vs. push vs. SMS vs. in-app — a user who turned off marketing email did not necessarily consent to marketing SMS, and TCPA treats SMS consent as its own thing legally, not a rider on email consent), **category** (security/billing alerts a user usually can't fully opt out of, vs. product updates they can), and **global suppression** (hard bounce, spam complaint, unsubscribe-all) which should override every category regardless of what a lower-level preference row says.

## Step 2: invariant A — every send path checks *live* preference state before sending

For each send path from step 1, trace what it actually queries before dispatch — not what the preference center's write side does, a completely different check. The classic gaps:

- A new notification type ships with its own hardcoded "does this user want this" logic instead of reusing the shared preference check — usually because the fastest way to ship a new digest is to copy an old send loop, and the copy paste includes the query but not the invalidation it depends on.
- The check happens at *enqueue* time only, not at *delivery* time — a user unsubscribes while 40,000 queued sends from a job that started an hour ago are still working through a queue with no re-check before the SMTP call.
- Global suppression (hard bounce, spam complaint, provider-side unsubscribe) is stored in a different table than the in-app preference center, and only one of the two is actually joined into the send query. Grep every place that builds a recipient list and confirm both are present, not just the one an engineer remembers.
- The provider's own unsubscribe/suppression state and the app's database are supposed to be the same fact told twice. Confirm the sync direction is real: is there a webhook handler for unsubscribe/bounce/complaint events, does it actually write to the table the send query reads, and what happens if that webhook is down for a day (does it silently drop events, or is there a reconciliation pass against the provider's suppression list)? A webhook endpoint returning 200 to a request it failed to process is invisible until someone audits it from the outside.

## Step 3: invariant B — the opt-out granularity matches what the user was actually shown

If the preference center presents categories ("Product updates", "Security alerts", "Newsletter"), the send code needs a check *per category*, not one global boolean that happens to cover the first category someone built and silently defaults every new one to "send" because the flag check was never added. Inverted defaults are the dangerous direction: a missing check that defaults to *not sending* is a lost notification (annoying); a missing check that defaults to *sending* is the compliance and trust incident. Audit which way an absent or failed preference lookup fails — treat "fail open to sending" as a finding regardless of how unlikely the lookup is to fail.

Also check the resubscribe path: a user who opts back in should have that reflected everywhere the opt-out was, not just in the UI-facing table — a nightly bulk sync job that re-imports "unsubscribed" status from a stale CRM export can silently undo a user's resubscribe if it treats its own data as authoritative instead of merging.

## Step 4: operational failure modes

- **Frequency cap surviving retries and restarts**: a cap ("at most one email per 24h") checked in-process is worthless the moment the job is horizontally scaled or restarts mid-run — it needs a shared, durable counter (same discipline as `job-warden`'s idempotency question), not an in-memory guard.
- **Cross-channel double-delivery of the same event**: an alert that fires push *and* email for the same trigger with no coordination isn't a preference bug exactly, but it's the symptom users report as "you're spamming me" — worth flagging alongside the real opt-out gaps.
- **Silent preference-write failures**: does the UI show "saved" optimistically before the write is confirmed? A preference toggle that appears to save but 400s server-side leaves the user believing they're opted out while every send path still finds them subscribed.

## Report

Per notification type/send path: which preference dimensions it checks (channel/category/global suppression), whether the check is enqueue-time or delivery-time, and evidence for provider-sync correctness (webhook handler exists, writes to the read table, has a reconciliation fallback). Flag fail-open defaults as a BLOCK regardless of how unlikely the failure path is — that's the one that turns into a compliance incident, not an annoyance.

## Boundaries

- Not a one-off send review — if the question is "is this one campaign safe to fire right now," that's `blast-guard`'s audience-query/dry-run/stop-mechanism check, not this skill's standing-system audit. Run both when a diff both adds a new send path *and* is about to fire it.
- Not legal advice — CAN-SPAM's 10-business-day honor window, TCPA consent scope, and GDPR's marketing-consent basis are real constraints this skill's findings feed into, but it doesn't certify compliance. Flag an obviously missing unsubscribe mechanism or fail-open default; don't claim clearance.
- If preference state lives in a third-party ESP/CRM this codebase doesn't own, this skill can verify the app's side of the sync (webhook handler exists, is wired to the send-blocking query) but can't verify the provider's internals — say that's the boundary rather than assuming the provider is correct.
