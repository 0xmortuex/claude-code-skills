# disconnect-guard — example

**Trigger:**

> a user says they disconnected our Slack integration three days ago but
> they're still getting message notifications from it. here's the relevant
> code:
>
> ```js
> // route: disconnect an integration
> router.post('/integrations/:id/disconnect', requireOwner, async (req, res) => {
>   await Integration.update(req.params.id, { connected: false });
>   res.json({ ok: true });
> });
>
> // middleware: validate the integration's access token on each API call
> async function validateIntegrationToken(token) {
>   const payload = jwt.verify(token, SIGNING_SECRET); // throws if expired/invalid signature
>   return payload; // no other check
> }
>
> // refresh-token exchange
> router.post('/oauth/token', async (req, res) => {
>   const { refresh_token, grant_type } = req.body;
>   if (grant_type !== 'refresh_token') return res.status(400).end();
>   const stored = await RefreshToken.findByValue(refresh_token);
>   if (!stored || stored.expiresAt < Date.now()) return res.status(401).end();
>   const accessToken = issueAccessToken(stored.integrationId);
>   res.json({ access_token: accessToken });
> });
>
> // webhook delivery handler
> router.post('/webhooks/slack/:integrationId', async (req, res) => {
>   const integration = await Integration.findById(req.params.integrationId);
>   const expected = computeSignature(req.body, integration.webhookSecret);
>   if (expected !== req.headers['x-slack-signature']) return res.status(401).end();
>   await processSlackEvent(integration, req.body);
>   res.json({ ok: true });
> });
> ```

**Response shape:**

Step 1 traces what the disconnect handler actually writes:

```
Step 1: what disconnect actually touches
POST /integrations/:id/disconnect writes exactly one field —
Integration.connected = false. It never touches a tokens table, never
calls a provider-side revocation endpoint, and never changes or clears
`integration.webhookSecret`. The access token and refresh token issued
when the user originally authorized Slack are left exactly as they
were before the click.
```

Step 2 traces whether token validation and refresh actually consult that flag:

```
Step 2: token validation and refresh
`validateIntegrationToken` only calls `jwt.verify` — signature and
expiry, nothing else. It never looks up `Integration.connected` or any
revocation state, so the access token issued before disconnect keeps
validating on every API call until its own unrelated expiry.
The refresh-token exchange is worse: it checks only that the stored
refresh token exists and hasn't hit its own `expiresAt` — never whether
the integration it belongs to is still connected. A disconnected
integration can keep calling /oauth/token and minting brand-new,
fully-valid access tokens indefinitely, which is the sharper version of
the gap — revoking the access token alone wouldn't have been enough
even if someone had remembered to.
```

Step 3 traces whether webhook delivery consults it:

```
Step 3: webhook delivery
The webhook handler looks up `integration.webhookSecret` fresh on every
request and verifies the signature against it — but disconnect never
cleared or rotated that secret, and never told Slack to stop sending.
So Slack keeps delivering events, the signature still matches the
secret that's still sitting on the row, and `processSlackEvent` keeps
running — which is exactly the reported symptom: notifications three
days after "disconnecting."
```

Report:

```
## disconnect-guard review: integrations.js

1. Disconnect only flips `Integration.connected = false`; it never
   revokes the access token, the refresh token, or the webhook secret,
   and never calls Slack's own revocation/unsubscribe endpoint (BLOCK —
   confirmed root cause, every downstream check in #2 and #3 traces
   back to this one write being incomplete).

2. `validateIntegrationToken` checks signature and expiry only — no
   lookup against `connected` or any revocation state, so the
   pre-disconnect access token keeps validating until it happens to
   expire on its own (BLOCK).

3. `/oauth/token`'s refresh-token exchange checks only the stored
   refresh token's own expiry, never the integration's connected state
   — a disconnected integration can keep minting new, fully-valid
   access tokens indefinitely, making the access-token gap in #2 moot
   even if it were fixed alone (BLOCK, the sharper of the two token
   gaps).

4. The webhook handler verifies against `integration.webhookSecret`
   fresh on every request, but disconnect never rotates or clears that
   secret and never unsubscribes with Slack, so deliveries keep
   arriving and keep passing verification — this is the reported
   symptom (BLOCK).

## Verdict: BLOCK
"Disconnect" is a UI-visible promise with nothing behind it: none of
the three places that actually grant access on this integration's
behalf — access-token validation, refresh-token exchange, or webhook
signature verification — consult the `connected` flag disconnect sets.
Fix: on disconnect, revoke the stored access and refresh tokens (or
record a `revoked_at` the validator and the exchange endpoint both
query), rotate or clear the webhook secret, and call Slack's own
app-uninstall/token-revocation API so the provider stops sending
altogether rather than relying on this app's own rejection of events it
can still be sent.
```
