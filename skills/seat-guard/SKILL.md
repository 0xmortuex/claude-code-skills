---
name: seat-guard
description: Audits whether a seat/license-limited SaaS app's enforcement actually holds — a concurrent invite/activation race where two requests both read the seat count before either write lands, so both pass validation and the org ends up over its paid limit; a deactivated/suspended/removed user who keeps silently occupying a seat because deactivation never decrements the count that invite-time validation reads; and a SCIM/SSO just-in-time provisioning path that creates accounts without ever calling the seat-limit check that only lives in the manual "invite user" handler. Use when adding or reviewing seat-based license enforcement, right after a customer was over their seat count despite the UI blocking new invites, or when asked "can two invites both pass the seat check at once", "why does this org have more active users than seats they paid for", "does deactivating a user actually free their seat", or "does SCIM provisioning respect our seat limit".
---

# seat-guard

A seat limit looks like one check — "does active user count exceed the plan's seat count?" — but it's actually three separate claims, each with its own way to go wrong, and each independently able to let an org exceed what it paid for while every individual code path looks correct in isolation. The common thread: the enforcement logic only runs where someone remembered to put it, and a seat count is a shared, mutable resource with more ways to change it than the one "invite user" button suggests.

## Step 1: the concurrent-read race

Find the actual check-then-act shape: does invite/activation code read the current seat count, compare it to the plan limit, and only *then* write the new user row — as two separate steps with no lock or atomic constraint between them? If so, two simultaneous invite requests (two admins inviting at once, a double-click, a retried request) both read the same "3 of 5 seats used" count, both see room, and both write — the org ends up at 7 active users on a 5-seat plan, and neither individual request did anything wrong on its own. Check specifically:

- Is the read-then-write wrapped in a transaction with actual row locking (`SELECT ... FOR UPDATE`, a unique constraint on an atomic counter, a conditional `UPDATE ... WHERE used_seats < limit`), or is it two independent queries with application code deciding in between?
- If seats are tracked as a count column rather than derived from counting active-user rows live, is that column ever allowed to drift from reality, and is incrementing it itself atomic (`UPDATE seats SET used = used + 1 WHERE used < limit`, checked by rows-affected) rather than read-modify-write in the application layer?

A fix that moves the check earlier (validate in the UI, validate in a middleware) doesn't close this gap — the race is about the gap between the *last* read and the write, however many checks ran before it.

## Step 2: does deactivation actually free the seat it claims to?

A seat limit is enforced by comparing *something* against the plan's count — find exactly what that something is, and whether deactivating, suspending, or soft-deleting a user actually changes it. The common bug: invite-time validation counts rows with `status = 'active'` (or similar), but a dedicated `used_seats` counter that invite-time validation actually reads is only decremented by a *hard delete*, never by deactivation — so a deactivated user shows up correctly as "inactive" everywhere in the UI while still occupying a seat that the enforcement check cannot see as free. This is a well-documented, recurring SaaS complaint (Jira, Pipedrive, Docketwise, Kayako, and GitLab have all tracked exactly this discrepancy under different names) — verify it isn't present here by tracing: what query or counter does the seat-limit check actually run, and does the deactivation code path write to that same source, not just to a `status`/`is_active` flag that nothing else reads?

Also check the reverse direction doesn't quietly break: if seats are freed on deactivation, does *reactivating* a previously-deactivated user re-run the same seat check a brand-new invite would — or can reactivation silently bypass the limit because it's treated as "this user already existed" rather than "this consumes a seat"?

## Step 3: does every provisioning path run the same check?

List every way a new active user can be created, not just the admin "invite" button: SCIM auto-provisioning from an identity provider, SSO just-in-time (JIT) provisioning on first login, a bulk-CSV invite, a public signup link for an org, an API endpoint, an admin console "add user" action separate from the regular invite flow. Seat-limit validation is usually written once, in the code behind the invite button — then an SSO/SCIM integration gets added later, by people focused on making authentication work, who have no reason to know a seat check exists elsewhere, and SCIM's provisioning protocol has no seat-limit concept of its own to prompt them (confirmed directly in identity-provider vendor guidance on seat-limit enforcement, which treats this as something the *application* has to add on top of SCIM, not something SCIM provides). The result: an identity provider can push users past the plan limit indefinitely, since nothing in the provisioning path ever asks whether there's room.

For each provisioning path found, confirm it calls the *same* check (or counter-increment) as Step 1 and Step 2's enforcement, not a separate reimplementation that can drift out of sync with it. A SCIM handler that checks seat count with its own separate, non-atomic read is still vulnerable to Step 1's race even if the manual invite path was already fixed.

## Report

BLOCK for: a check-then-write seat validation with no atomic guarantee between the read and the write (Step 1); a seat counter that invite-time enforcement reads but that deactivation never updates, so deactivated users permanently occupy seats (Step 2); or any provisioning path (SCIM, JIT, bulk import, a second API) that creates active users without running the same enforcement the primary invite path uses (Step 3). CAUTION for a fix that's correct in shape but unverified against real concurrency (an atomic `UPDATE` exists but was never tested under simultaneous requests) or a provisioning path that *looks* like it calls the shared check but through an older/forked copy of the logic that could drift. Name the exact query, counter, or handler for each finding — "seat enforcement looks fine" is not a finding; either the read-write is atomic, the counter source matches across every path, and every provisioning path shares one check, or it doesn't.

## Boundaries

- Not `proration-guard`'s territory — that skill audits billing *math* on plan changes (proration credit, invoice correctness). This skill audits whether the seat *count* itself stays correct and enforced; a plan with perfectly correct proration can still silently let an org run over its seat limit, and that's this skill's bug, not proration-guard's.
- Not an SSO/SAML authentication-security review — whether SCIM/JIT provisioning correctly authenticates and authorizes who a user *is* is a separate concern from whether provisioning respects a seat *count*, which is what this skill checks.
- Doesn't design a billing/metering system from scratch — it audits whether an existing (or proposed) seat-enforcement mechanism actually closes the three gaps above, not which pricing model or metering vendor to adopt.
- Can't observe live concurrent traffic or confirm an org's actual current seat usage from source alone — it can identify whether the code's own read-write pattern is capable of a race or a missed decrement, and say plainly when confirming an actual overage needs a database query against production data rather than a code read.
- Doesn't cover usage-based or metered-consumption limits (API call quotas, storage caps) — those are enforced and reconciled differently from a discrete per-user seat count, which is this skill's scope.
