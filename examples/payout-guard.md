# payout-guard — example

**Trigger:**

> we're adding a "update your direct deposit" page to the employee
> portal so people don't have to email HR a voided check. it's gated by
> the same SSO login as the rest of the portal. here's the handler —
> can you check it over before we ship it?
>
> ```python
> # payroll_settings.py
> @app.route("/portal/payout", methods=["POST"])
> @require_sso_session
> def update_payout(request):
>     employee = request.session.employee
>     employee.bank_account = request.form["account_number"]
>     employee.routing_number = request.form["routing_number"]
>     db.save(employee)
>     send_email(
>         to=employee.sso_email,
>         subject="Your direct deposit details were updated",
>         body="Your payout destination was changed on " + str(now()),
>     )
>     return redirect("/portal/payout?saved=1")
> ```

**Response shape:**

Step 1 checks for re-authentication on this specific action:

```
Step 1: re-authentication
`update_payout` only requires `@require_sso_session` — the same gate every
other page in the portal uses. There's no password or MFA step-up check
inside the handler itself. Anyone holding a live SSO session for this
employee — including one obtained via AiTM phishing, which doesn't need
the real password — can submit this form.
```

Step 2 checks whether the notification channel is actually independent:

```
Step 2: notification-channel independence
The only notice is `send_email` to `employee.sso_email` — the same identity
whose session was just used to make the change. If the attacker's foothold
is a phished SSO session (the realistic path here, not a stolen device),
they are very likely already inside that same mailbox, or can set an inbox
rule to hide this exact message, the way Microsoft's documented
Storm-2657/"Payroll Pirate" campaign did against Workday. This looks like
a safety net in the code but isn't one against the attacker this system
actually faces — there's no SMS to a phone on file, no required callback,
nothing outside the SSO identity perimeter.
```

Step 3 checks for a hold period before the new destination is live:

```
Step 3: hold period
None. `employee.bank_account` and `employee.routing_number` are
overwritten and `db.save` commits immediately in the same request that
sent the (compromised-channel) notification. The next payroll run reads
whatever is in those fields with no delay — there's no window between
"changed" and "money actually moves" for a real owner to notice and react
in, even if the notification had reached them.
```

Report:

```
## payout-guard review: payroll_settings.py

1. `update_payout` requires only an active SSO session, no step-up
   re-authentication for this specific action — a phished session is
   sufficient to redirect someone's paycheck (BLOCK, Step 1).

2. The only notification goes to `employee.sso_email`, the same identity
   perimeter the attacker's session already lives inside — not an
   independent channel, and defeatable the same way the real Storm-2657
   campaign defeated it (an inbox rule under the same compromised
   identity) (BLOCK, Step 2).

3. The new bank details go live immediately, with payroll reading them on
   the very next run — no hold period gives a real owner time to see and
   act on the notice even if it reached them (BLOCK, Step 3).

## Verdict: BLOCK
All three gaps compound: a phished SSO session alone can change the
destination, the only notice lands where that same session could suppress
it, and the change is live before anyone could plausibly react. Fix, in
order of leverage: require a password or MFA step-up inside
`update_payout` itself rather than trusting `@require_sso_session` alone;
hold the change on the old bank details for a cooling-off window (long
enough to span at least the time to the next scheduled payroll run) with a
self-service revert during that window; and add a notification channel
outside the SSO identity — SMS to the phone number already on file in HR
records, or a required callback — rather than relying solely on an email
address the same compromised identity controls.
```
