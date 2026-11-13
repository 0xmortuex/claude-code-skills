# email-guard — example

**Trigger:**

> adding a "change email" option to account settings, can you check this is
> safe before I ship it? user just has to be logged in and type the new
> address.
>
> ```js
> // routes/account.js
> router.post('/account/email', requireSession, async (req, res) => {
>   const { newEmail } = req.body;
>   await db.users.update(req.user.id, { email: newEmail });
>   await mailer.send(newEmail, 'welcome-to-your-new-email');
>   res.json({ ok: true });
> });
> ```

**Response shape:**

Step 1 checks whether the action requires proving identity beyond the session:

```
Step 1: re-authentication
requireSession only checks for a valid session cookie — the same thing a
stolen cookie or an XSS payload already has. No password, no MFA step-up,
nothing that distinguishes the real account owner from anyone currently
holding this session. This is the whole value of a hijacked-session
attack: the attacker never needed the password, and this endpoint doesn't
ask for it either.
```

Step 2 checks notification and confirmation-before-apply:

```
Step 2: notification and confirmation
db.users.update writes the new email immediately — the account is on the
new address before anything confirms it's reachable by anyone but whoever
typed it. The only email sent goes to the NEW address ('welcome-to-your-
new-email'); the old address — the one channel the real owner could still
read if an attacker already controls the new one — gets nothing. This is
the exact CVE-2018-19580 shape (GitLab, old address never notified) plus
the Flowise shape (GHSA-x39m-3393-3qp4, unverified new address goes live
immediately) at the same time.
```

Step 3 checks session/log fallout:

```
Step 3: sessions and audit trail
No session invalidation after the update — any other active session
(including the real owner's, on a different device) stays logged in with
no forced re-auth. No activity-log entry either, just the row update — an
owner checking "recent account activity" later would see nothing.
```

Report:

```
## email-guard review: POST /account/email

1. No re-authentication required — `requireSession` accepts an existing
   session as sufficient proof; a hijacked session can change the email
   with no password or MFA check (BLOCK — require current password, or
   MFA step-up if enrolled, before accepting `newEmail`).

2. The old address is never notified and the new address goes live before
   confirming it's reachable — the update applies synchronously in the
   same request that received `newEmail` (BLOCK — hold the account on the
   old address until a confirmation link sent to the new address is
   clicked, and send a separate "your email was changed" notice to the old
   address at the same time the change is first requested).

3. No session invalidation and no audit-log entry on change (CAUTION — add
   both once 1 and 2 are fixed; they reduce blast radius but aren't the
   primary gap here).

## Verdict: BLOCK
This is a full account-takeover path for anyone with a live session,
not just a missing nice-to-have. Add a password/MFA re-auth check, switch
to confirm-then-apply with the account staying on the old address until
the new one confirms, and send the old address a notice the moment a
change is requested — not just the new address a welcome mail.
```
