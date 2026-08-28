# pref-guard — example

**Trigger:**

> a user filed a support ticket: they turned off "Product updates" in their
> notification settings three weeks ago but just got a "New AI Search
> Launched" email. can you check why? here's the relevant code:
>
> ```python
> # preferences/models.py
> class UserPreference(models.Model):
>     user = models.OneToOneField(User, on_delete=models.CASCADE)
>     email_security = models.BooleanField(default=True)   # can't fully disable
>     email_product_updates = models.BooleanField(default=True)
>     email_newsletter = models.BooleanField(default=True)
>     push_marketing = models.BooleanField(default=True)
>
> # campaigns/announce_feature.py
> def send_feature_announcement(feature_name):
>     users = User.objects.filter(marketing_opt_out=False)
>     for user in users:
>         mailer.send(user.email, template="feature_launch", context={"feature": feature_name})
> ```

**Response shape:**

Claude enumerates send paths before touching the bug report — the ticket
names one email, but the audit is of the standing system, not that one send:

```
Step 1: send paths and preference dimensions found in this codebase
- transactional: password reset, order confirmation (mailer.transactional_send)
- campaigns/announce_feature.py — feature-launch emails (the one in the ticket)
- campaigns/weekly_digest.py — cron-triggered digest
- push/marketing_push.py — push notification variant of campaign sends
- preference dimensions: UserPreference has per-category booleans
  (email_security, email_product_updates, email_newsletter) plus a
  separate legacy User.marketing_opt_out boolean on the User model itself.
  Two competing sources of truth already, before checking which one any
  given send path reads.
```

Step 2 (invariant A — live preference state) is where the ticket's bug
actually lives, and it's found by reading the send path's own query, not by
trusting that a preference table exists somewhere in the codebase:

```
Step 2: invariant A — does each send path check live preference state?

- announce_feature.py: `User.objects.filter(marketing_opt_out=False)`
  FAIL. Queries the legacy `User.marketing_opt_out` field, not
  `UserPreference.email_product_updates`. Grepped for writes to
  `marketing_opt_out`: the preference-center UI (`settings/views.py`)
  stopped writing to it eight months ago when the per-category
  `UserPreference` model shipped — it only writes the new table now.
  `marketing_opt_out` is frozen at whatever value each user had at
  migration time. The reported user opted out of "Product updates" in the
  new UI three weeks ago; that write landed in
  `UserPreference.email_product_updates`, which this send path never reads.

- weekly_digest.py: joins `UserPreference` and filters
  `email_newsletter=True`. OK — reads the current table.

- marketing_push.py: filters `UserPreference.objects.filter(push_marketing=True)`
  but does not exclude users whose `email_security` incident escalated them
  to a temporary global suppression flag (`SuppressionList` model, checked
  by the transactional sender but not here). Sampled 10 rows: 1 of 10 is
  present in `SuppressionList` with reason "spam_complaint" and would still
  receive this push. FAIL.

- Provider sync: SendGrid webhook handler
  (`webhooks/sendgrid_events.py::handle_unsubscribe`) exists and writes to
  `SuppressionList`. Confirmed it's wired to campaign sends via the
  newsletter path, but `announce_feature.py` and `marketing_push.py` don't
  query `SuppressionList` at all — a provider-side unsubscribe or bounce
  wouldn't stop either of those two sends either.
```

Step 3 (invariant B — granularity and fail-open direction) checks which way
an absent check fails, since that's what turns a bug into an incident:

```
Step 3: invariant B — granularity and fail-open direction

announce_feature.py's `marketing_opt_out=False` filter is a single global
boolean standing in for what the UI presents as three separate categories
(security/product-updates/newsletter). A user who only wanted to keep
security alerts has no way to express that through this send path — it
either sends to them or it doesn't, per-category intent is discarded.

Failure direction: the stale field defaults new/reactivated accounts to
`marketing_opt_out=False` (i.e. subscribed) since that was the pre-migration
default. Combined with the fact that the current UI never updates this
field, any account whose *only* interaction with preferences has been
through the new UI is invisible to the old check and always reads as
opted in. Fail-open. Flag as BLOCK per the skill's report rule, independent
of how rare a fresh account is in the affected set.
```

Step 4 covers the operational angle the ticket alone wouldn't surface:

```
Step 4: operational failure modes

- No shared frequency cap found on any of the three campaign paths — each
  send loop is independent with no durable "already sent today" counter.
  Not this ticket's bug, but flagged since a second campaign firing the
  same day would double-send with no coordination.
- Preference-center save: `settings/views.py` returns 200 optimistically
  before the DB write is confirmed inside a try/except that swallows
  `IntegrityError` on a rare constraint violation (duplicate
  `UserPreference` row from a race on first-time creation) — the UI would
  show "saved" while the row never wrote. Noted as a secondary risk, not
  confirmed as the cause of this specific ticket.
```

Report matches the skill's per-send-path format:

```
## pref-guard audit: notification preference correctness

1. announce_feature.py: FAIL — reads legacy `User.marketing_opt_out`
   (frozen, no longer written by the current UI) instead of
   `UserPreference.email_product_updates`. This is the ticket's root
   cause: the reported user's opt-out three weeks ago never reached this
   send path. Also collapses three UI-presented categories into one
   boolean (invariant B fail).
2. weekly_digest.py: OK — reads current `UserPreference.email_newsletter`.
3. marketing_push.py: FAIL — reads `UserPreference.push_marketing` but
   never joins `SuppressionList`; a spam-complaint or bounce suppression
   doesn't stop this send path.
4. Provider sync: PARTIAL — SendGrid unsubscribe webhook writes to
   `SuppressionList` correctly, but only `weekly_digest.py` actually
   queries it. Two of three campaign paths ignore provider-side
   suppression entirely.

## Verdict: BLOCK
Root cause confirmed for the ticket: point `announce_feature.py` at
`UserPreference.email_product_updates` (not the frozen legacy field), and
give `marketing_push.py` the same `SuppressionList` join `weekly_digest.py`
already has. Both are independent fail-open gaps — fix both, not just the
one the ticket happened to surface, since the next new send path is as
likely to copy `announce_feature.py`'s pattern as the correct one. Delete
or stop writing anywhere as read-authoritative on `marketing_opt_out` once
the fix lands, so a future send path can't accidentally copy the stale
field again.
```
