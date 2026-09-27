---
name: push-guard
description: Audits a push-notification device-token lifecycle for the failure that looks like success — a token that keeps receiving pushes after the account that registered it has logged out or switched (a shared/handed-down device leaking one user's notifications to the next), an OS-issued token refresh/rotation that never replaces the old token server-side (duplicate live tokens per install), and a provider-reported dead token (FCM's UNREGISTERED response, APNs' 410 Unregistered / 400 BadDeviceToken) that gets silently retried instead of deleted. Use when adding or reviewing push registration/logout/token-refresh code, or when asked "does logout actually stop push notifications", "why did this device get someone else's notification", "are we handling invalid or expired push tokens", or "audit our push token lifecycle".
---

# push-guard

A push token gets provisioned once and then treated like a permanent fact — "this token means this device belongs to this account" — but neither half of that holds for the life of an install. The OS reissues tokens (reinstall, restore, routine rotation); the provider unilaterally declares a token dead and says so in the send response; and a logout or "switch account" flow only breaks the token-to-account link if something explicit goes and breaks it. A real, publicly reported bug shows exactly how this fails without looking wrong from inside the notification-sending code at all: a noticeboard app's logout handler tried to delete the device's push-token record from the server, but the delete call passed the literal string `"token"` instead of the actual stored token value, so it never matched a row — the device kept receiving the logged-out user's notifications indefinitely (`IMGIITRoorkee/noticeboard-mobile-app` issue #58). The send path was never at fault; the plumbing around it was.

The provider side has the same shape. Firebase's own documented best practice for FCM is to detect an invalid-token response and delete that registration — a token inactive long enough is deliberately expired and rejected with a not-found-style error precisely so servers stop wasting sends on it. Apple's APNs equivalent is a `410 Unregistered` or `400 BadDeviceToken` response, both documented as final: retrying against them is documented to be pointless, and the fix is to remove the token. A codebase that has no code path reacting to either signal doesn't fail loudly — it just accumulates dead tokens forever, burns send quota, and eventually looks like an unrelated "our delivery rate is dropping" mystery.

## Step 1: find every place a token is registered, and check what happens to it on logout or account switch

Locate the registration handler (`onNewToken` / `didRegisterForRemoteNotificationsWithDeviceToken` / the SDK equivalent) and trace where it writes the device-token-to-account mapping. Then check the logout path specifically:

- Does logout call a server endpoint (or enqueue a durable, guaranteed-delivery request) that removes or dissociates the token from the account — not just clear client-side UI state or an in-memory flag that has no effect on what the server will still send to?
- Is the value used in that delete/unregister call the actual token read back from where it's stored, or a placeholder, a stale closure variable, or a value captured before an async registration finished? This is the exact noticeboard-app#58 shape — read the literal call site, don't assume the variable name means the right value is in it.
- On a shared or handed-down device (a family tablet, a kiosk, a "sign in as someone else" flow, a phone sold or given away without a factory reset): is the outgoing account's token guaranteed removed *before* the incoming account's session can start, or is there a window where a push could route to either?

## Step 2: check what happens when the OS reissues a token

Device tokens rotate — reinstalls, OS restores, and routine SDK-driven refresh all mint a new token for the same physical device. Check the refresh callback: does it *replace* the stored token for that account/install, or does it insert an additional row alongside the old one with nothing ever cleaning the old one up? An install that accumulates tokens without retiring old ones can end up sending duplicate notifications to one physical device, or — worse — still targeting a token that's already dead while the install's actual current token was captured and never used.

## Step 3: check whether the send path acts on a provider's own "this token is dead" signal

For each provider in use, confirm the send/response-handling code distinguishes a final, non-retryable dead-token response from a transient failure, and deletes the token on the former:

- **FCM**: an invalid/unregistered-token response (Firebase's documented recommendation: detect it and delete that registration from your system) should remove the row, not get treated the same as a retryable 5xx.
- **APNs**: `410 Unregistered` and `400 BadDeviceToken` are documented as final — Apple's own guidance is not to retry these — and should trigger a delete, not a backoff-and-retry loop.
- If there's no code path reacting to either signal at all — every non-success response falls into one generic "retry later" branch — say so as the primary finding rather than listing individual stale tokens; the token store can only grow, and the send path is quietly wasting quota (or, if the provider eventually rate-limits or drops based on error ratio, quietly losing real deliverability) with no mechanism to ever find out.

## Step 4: check what a misrouted token can actually expose

Where steps 1–2 found a real gap (a token that outlives the account it was bound to), check what the notification payload itself contains. A generic "you have a new message" ping reaching the wrong device is a trust/UX bug. A payload carrying message content, an order total, a person's name, or a deep link embedding another user's resource ID turns the identical plumbing gap into a data-exposure incident — call out this distinction explicitly rather than treating every misrouted-token finding as the same severity.

## Report

Lead with whichever applies: (a) logout or account-switch doesn't actually remove or reassign a device's token, so a shared or passed-along device can keep receiving another account's pushes — cite the exact removal call and why it doesn't work (wrong value, missing call, a race with an async step); or (b) the send path has no handling for either provider's documented dead-token response, so the token store never shrinks. BLOCK for a confirmed logout/account-switch gap where the exposed payload carries real user content, or a concrete reproduction of a non-matching delete call. CAUTION for a logout gap where the payload is low-sensitivity/generic, or for dead-token handling that's simply absent but hasn't yet caused an observed problem. SAFE only with evidence: a server-side delete/dissociate call keyed on the actual stored token value, confirmed to run before (or durably queued ahead of) logout completing, and a send path that acts on both providers' documented invalid-token responses.

## Boundaries

- Not `blast-guard`'s territory — that skill reviews whether one bulk send is safe to fire (audience query, suppression list, a stop mechanism). This skill reviews the token plumbing underneath *any* send: whether it still identifies the right device and account at all, independent of any single campaign.
- Not `pref-guard`'s territory — `pref-guard` audits whether a user's chosen preference (opted in/out, per channel or category) is honored by the send path. This skill sits a layer below that: whether the token the send path is even targeting is still valid and still bound to the right account, a question that matters regardless of what the user preferred.
- Doesn't cover push payload encryption, lock-screen content redaction, or notification-permission-prompt UX — those are client-security or UX concerns, not token-lifecycle ones, though step 4 flags when a lifecycle gap makes payload sensitivity matter more.
- Can't verify actual provider-side behavior — whether a given token is really dead, or the live send-success rate — from source alone. Say plainly when confirming that needs the provider's delivery/error dashboard or a live trace rather than a code read.
- Doesn't design a push architecture from scratch or recommend a provider/SDK — reviews whether existing registration, refresh, and send code handles the lifecycle correctly.
