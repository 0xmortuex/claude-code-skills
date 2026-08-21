# blast-guard — example

**Trigger:**

> we're sending a winback email to users who haven't logged in for 90 days —
> here's the job:
>
> ```python
> def send_winback_campaign():
>     users = User.objects.filter(last_login__lt=now() - timedelta(days=90))
>     for user in users:
>         mailer.send(user.email, template="winback_2026_08")
> ```
>
> marketing expects this to hit about 3,000 people. can you check it before
> we run it?

**Response shape:**

Claude classifies the send first — a query decides the recipient list and
the loop's whole job is "message N people," so this is bulk, full ceremony
applies:

```
Classification: bulk campaign (audience decided by a query, not a
per-user trigger). Not transactional — full four-check review applies.
```

Check 1 doesn't trust the query by reading it — it runs the `COUNT(*)`
first, which is where the real bug shows up before any code-level nitpick
would have caught it:

```
1. Audience query
   SELECT COUNT(*) FROM users WHERE last_login < now() - interval '90 days';
   → 41,200 rows. Marketing expected ~3,000 — 13x over.

   Sample of 20 rows (email, last_login, deleted_at):
   - 6 of 20 have deleted_at set (soft-deleted accounts, still in the
     `users` table, still valid email addresses on file).
   - remaining 14 span from 91 days inactive up to an account whose
     last_login is from 2019 — the filter has no upper bound, so it
     also catches everyone who has *ever* gone quiet, not just users
     who recently crossed the 90-day line.

   FAIL: no `deleted_at IS NULL` filter, no upper bound on the window.
```

Check 2 looks for suppression logic as live code, not intent — and finds
none:

```
2. Suppression
   Codebase has an `unsubscribes` table (checked: populated, used by the
   transactional mailer). This job's query never joins it.
   FAIL: hard-bounce and unsubscribe lists are not consulted — this send
   would re-mail addresses that already opted out or previously bounced.
```

Check 3 confirms which provider/environment the send is actually bound to
at runtime, not what the code implies:

```
3. Environment
   MAILER_API_KEY resolves to the production SendGrid account in this
   deploy's env — confirmed intentional, marketing wants this campaign live.
   OK.
```

Check 4 asks whether a stop mid-send means anything — here it doesn't:

```
4. Stop mechanism
   Single unbatched `for user in users` loop. No checkpoint, no dedup key,
   no cap. A crash or manual kill at recipient 20,000 leaves no record of
   who was already sent — resuming means re-running the whole query and
   re-mailing everyone, including the 20,000 already messaged.
   FAIL.
```

Report matches the skill's standard format — verdict per check, evidence
cited, no ceremony skipped since this is a 41,000-row send however small
marketing believed it was:

```
## send: winback-campaign-2026-08
1. Audience query: FAIL — COUNT(*) returned 41,200, expected ~3,000.
   Missing `deleted_at IS NULL` and an upper bound on `last_login`.
2. Suppression: FAIL — unsubscribes table exists, query never joins it.
3. Environment: OK — production SendGrid, intentional.
4. Stop mechanism: FAIL — unbatched loop, no checkpoint, no idempotency key.

## Verdict: BLOCK
Fix the audience query first (add `deleted_at IS NULL` and
`last_login BETWEEN now()-120d AND now()-90d`, re-run the COUNT and confirm
it lands near 3,000), join the unsubscribes/hard-bounce tables into the
filter, and batch the send with a per-user `sent_at` checkpoint before this
runs again. Don't ship a "just fix the count" patch — suppression and
resumability are independent failures, not follow-on nits.
```
