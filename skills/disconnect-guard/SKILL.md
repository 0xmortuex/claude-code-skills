---
name: disconnect-guard
description: Audits whether a user-facing "disconnect this integration" / "revoke this app's access" action actually invalidates the OAuth tokens already issued to that integration (access + refresh) and tears down its registered webhook(s), rather than only flipping a DB/UI flag that the token-validation middleware, refresh-token exchange, and webhook-signature-verification path never check. Use when adding or reviewing a third-party integration's disconnect/revoke-access flow, an OAuth connected-apps manager, or webhook registration teardown, or when asked "does disconnecting an integration actually revoke its tokens", "can a disconnected app keep working", "does our webhook stop after we revoke access", or "audit our integration disconnect flow".
---

# disconnect-guard

A "Disconnect" button is the one control a user trusts to be a kill switch — they click it specifically because they want the access gone, now, completely. What it usually does is write one row: flip `connected` to `false`, mark the `Integration` record `revoked_at`, maybe delete it outright from a connected-apps list UI. That's a correct and complete fix only if every other code path that grants access on behalf of that integration was built to consult that same row. It rarely is, because the token validator, the refresh-token exchange, and the webhook-delivery/signature-verification path are usually written once, independently, against "is this token well-formed and unexpired" — not "does the integration this token belongs to still have a `connected` row." The disconnect UI update and the thing that actually lets the integration keep talking to the account are two different code paths that nobody wired together, so the button lies: the user believes they revoked access, and the access-token-plus-refresh-token pair (or the webhook subscription) they issued keeps working until it happens to expire on its own.

This is a real, dated gap, not a hypothetical: Rocket.Chat's CVE-2026-49277 (GHSA-39hg-492f-3c4f, CWE-613) — deactivating a user never revoked their already-issued OAuth access and refresh tokens, so the deactivated account could keep using the live access token, and mint fresh ones from the refresh token, right up until the tokens' own unrelated expiry (fixed in 8.5.0/8.4.2/8.3.4/8.2.4/8.1.5/8.0.6/7.13.8/7.10.12). And OpenClaw's CVE-2026-53830 (GHSA-275c-xpvc-jgfw) — the same shape one layer over: a `secrets.reload` operation wrote a new Slack/Zalo webhook secret to the secret store, but the webhook-signature-verification path kept accepting requests signed with the old secret, because invalidating the old value and wiring verification to actually require the new one are two different things that only the first one happened to.

## Step 1: find exactly what the disconnect/revoke action writes

Locate the handler behind the user-facing "disconnect"/"revoke access" control and trace precisely what state it touches — not what it's supposed to mean, what it actually does:

- Does it delete or mark-dead the stored access and refresh tokens themselves (a row in a tokens table, a Redis key, a provider-side revocation API call), or does it only flip a `connected`/`active` boolean on the integration record while the tokens live on untouched wherever they're stored?
- Does it de-register the integration's webhook(s) — remove the subscription, invalidate the signing secret with the provider, stop forwarding incoming deliveries — or only hide the webhook row from the connected-apps UI the user is looking at?
- If this calls out to an external OAuth provider's own revocation endpoint (RFC 7009 `/oauth/revoke` or equivalent), confirm the call actually happens and its response is checked — a revocation request that's fired and never confirmed is indistinguishable, from the code, from one that silently failed.

## Step 2: find whether token validation and refresh actually consult that state

This is the step that decides whether step 1's write does anything: trace forward from whatever disconnect touched to the code that validates an access token on each request and the code that exchanges a refresh token for a new access token.

- Does the access-token validator check anything beyond signature and expiry — a live lookup against the revoked/connected flag, a denylist, a short-TTL cache of revocation state — or does a structurally valid, unexpired JWT or opaque token keep passing regardless of what the integration record now says?
- Does the refresh-token exchange endpoint check the *refresh* token's own revocation status before minting a new access token? This is the sharper version of the gap: even a validator that does check revocation on access tokens is defeated if the disconnected integration can just mint a brand-new, fully-valid access token from a refresh token nobody invalidated — exactly the Rocket.Chat CVE-2026-49277 shape.
- If tokens are self-contained JWTs with no server-side state at all, is there any revocation mechanism (a `jti` denylist, a `revoked_at` timestamp the validator actually queries) — or is "revoke" structurally impossible until the token's own expiry, which the disconnect UI never discloses to the user clicking the button?

## Step 3: find whether webhook delivery and secret verification actually consult it

Same question, for the push side instead of the pull side:

- Does the webhook-signature-verification path look up the current, live secret for that integration on every incoming delivery, or does it hold a cached/previously-fetched secret that a disconnect or secret-rotation operation updated in the store without ever reaching the verifier — the OpenClaw CVE-2026-53830 shape exactly: the store has the new value, the code path that checks signatures doesn't know that.
- Does disconnecting the integration actually stop the provider from attempting deliveries at all (an unsubscribe/deregistration call to the provider), or does it only make this app's own handler reject them — leaving the provider still sending, and the rejection itself an unauthenticated log line rather than a real boundary if the verification check has the same staleness bug as above?

## Report

Lead with which layer actually failed: BLOCK for a disconnected/revoked integration whose previously-issued access token still validates, whose refresh token can still mint new access tokens, or whose webhook deliveries still pass signature verification — name the specific validator/exchange/verification code and what it checks instead of live revocation state. CAUTION when disconnect correctly kills new activity but doesn't call the provider's own revocation endpoint (so the provider-side token technically survives even though this app now rejects it) or when revocation exists but was never confirmed to actually reach the token store under load. SAFE only with evidence: the disconnect handler revokes the access token, the refresh token, and the webhook secret/subscription in the same operation, and the validator/exchange/verification paths were confirmed (by reading the code, not inferring from the disconnect handler's intent) to perform a live check against that revoked state rather than signature-and-expiry alone.

## Boundaries

- Not `revoke-guard`'s territory — that skill assumes the REST/token-revocation path already works correctly and audits whether a long-lived, already-open WebSocket collaboration session re-checks authorization while it stays connected. This skill audits the thing `revoke-guard` takes for granted: whether the token/webhook revocation itself is wired to anything at all.
- Not `rotation-guard`'s territory — that skill audits propagating a credential to a *new* value across consumers with a safe overlap window (your own DB passwords, API keys, Vault leases). This skill audits a *permanent*, user-initiated revocation of a third-party grant with no new value and no overlap window to design — the only question is whether the kill switch is connected to anything.
- Doesn't audit the OAuth consent/grant screen itself (scope correctness, over-broad permission requests) — that's a different flow than disconnecting an already-granted integration.
- Can't confirm a provider-side revocation API call actually succeeded against the real provider from source alone — say plainly when confirming that needs a live test or the provider's own token-introspection endpoint rather than a code read.
- Doesn't design an OAuth token-revocation or webhook-subscription system from scratch — reviews whether an existing disconnect flow actually reaches the validation, refresh, and delivery code paths it needs to.
