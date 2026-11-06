# dormancy-guard — example

**Trigger:**

> our nightly "deactivate accounts inactive 90+ days" job ran last night and
> this morning a customer's Zapier integration started failing with 401s.
> nobody touched that account in months but it's been running their order
> sync the whole time. can you check if our dormancy job is going to do
> this again?
>
> ```sql
> -- dormancy_sweep.sql, run nightly by cron
> UPDATE accounts
> SET status = 'deactivated'
> WHERE last_login_at < NOW() - INTERVAL '90 days'
>   AND status = 'active';
> ```
>
> ```js
> // auth/middleware.js
> function requireLogin(req, res, next) {
>   req.user.last_login_at = new Date();
>   req.user.save();
>   next();
> }
>
> // api/middleware.js — separate path for API-key requests
> function requireApiKey(req, res, next) {
>   const account = lookupByKey(req.headers['x-api-key']);
>   if (!account || account.status !== 'active') return res.status(401).end();
>   req.account = account;
>   next(); // no activity timestamp written here
> }
> ```

**Response shape:**

Step 1 traces the signal and finds the exact gap:

```
Step 1: signal vs. access pattern
dormancy_sweep.sql reads only last_login_at, written exclusively by
requireLogin (the interactive session middleware). requireApiKey — the
path Zapier's integration authenticates through on every sync run —
never touches last_login_at or any other activity column. An account
that's been making authenticated API calls every hour for months still
shows a last_login_at from whenever a human last opened the dashboard,
which for an unattended integration account can easily be 90+ days.
The sweep isn't buggy — it's doing exactly what it was told, on a
signal that was never wired up to see this account's real activity.
```

Step 2 checks the blast radius of firing:

```
Step 2: action and recovery
Deactivation is immediate and silent — no notice email, no grace
period, status flips in the same job that detected dormancy. Recovery
requires logging into the dashboard and reactivating, which is exactly
the action this account doesn't take — there's no API-driven or
owner-notification path back in, so a falsely-flagged service-style
account is stuck until a human happens to notice the integration broke
and knows to look here.
```

Step 3 confirms no exception was ever decided:

```
Step 3: policy decision
No `is_service_account` flag, no exclusion list, no separate threshold
for API-key-only accounts anywhere in the sweep or its surrounding
docs — the 90-day interactive-login threshold is applied uniformly
because nothing distinguishes account types, not because someone
decided integration accounts should be held to the same bar.
```

Report:

```
## dormancy-guard review: 90-day inactivity sweep vs. API-key accounts

1. `dormancy_sweep.sql` reads only `last_login_at`, which `requireApiKey`
   never updates — any account driven purely by API-key traffic (like
   the Zapier integration that just broke) will eventually hit the
   90-day threshold no matter how active it actually is (BLOCK — this
   is the live incident, and it will recur for every similar account).

2. Deactivation is immediate with no notice window and no non-login
   reactivation path — an account flagged this way stays broken until
   a human notices and logs in, which an unattended integration has no
   one around to do (BLOCK — add a grace period with an owner
   notification, and a reactivation path that doesn't require login).

3. No account-type exception exists anywhere in the sweep — API-key-only
   accounts are being swept by default, not by decision (CAUTION —
   surface this as a policy question: should they be exempt, held to a
   longer threshold, or genuinely included on purpose).

## Verdict: BLOCK
Update `requireApiKey` to write an activity timestamp on every
authenticated call (or add a parallel `last_api_activity_at` column the
sweep also checks), reactivate the affected account now, and add a
notice/grace step before deactivation fires for any account type the
business hasn't explicitly decided should be swept on login alone.
```
