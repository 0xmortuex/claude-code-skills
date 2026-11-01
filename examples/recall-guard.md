# recall-guard — example

**Trigger:**

> we just shipped "unsend" for direct messages (5-minute window, shows a
> toast if you try after that) and I want a sanity check before this goes
> wide. here's the message send and unsend code:
>
> ```js
> // send
> async function sendMessage(channelId, senderId, text) {
>   const message = await Message.create({ channelId, senderId, text, createdAt: Date.now() });
>   await esClient.index({ index: 'messages', id: message.id, body: { text, channelId } });
>   await webhooks.fire(channelId, { event: 'message.created', messageId: message.id, text });
>   for (const device of await devicesInChannel(channelId)) {
>     await apns.send({
>       token: device.token,
>       payload: { aps: { alert: { body: text }, sound: 'default' } },
>     });
>   }
>   return message;
> }
>
> // client: unsend button
> function canUnsend(message) {
>   return Date.now() - message.createdAt < 5 * 60 * 1000; // hide button after 5 min
> }
>
> // server: unsend
> router.delete('/api/messages/:id', requireAuth, async (req, res) => {
>   const message = await Message.findById(req.params.id);
>   if (message.channelId !== req.user.currentChannelId) {
>     return res.status(403).json({ error: 'not in this channel' });
>   }
>   await Message.findByIdAndUpdate(message.id, { text: '', unsent: true });
>   res.json({ ok: true });
> });
> ```

**Response shape:**

Step 1 enumerates everywhere the original text already landed at send time:

```
Step 1: where the content went
- Primary row: Message document (channelId, senderId, text).
- Search index: indexed into Elasticsearch immediately on send.
- Webhook: fired to an integration ("message.created") carrying the full text.
- Push: APNs alert body carries the literal message text, to every device
  in the channel, at send time — before any unsend window has even started.
```

Step 2 checks whether the unsend handler touches any of them:

```
Step 2: what unsend actually updates
`findByIdAndUpdate` blanks `text` and sets `unsent: true` on the primary
row only.
- Search index: never touched. Elasticsearch still returns the original
  text for this message id — "can't be recalled, should be" bucket, this
  one's a real fixable gap (call esClient.delete or reindex on unsend).
- Webhook: never fires a corresponding "message.deleted"/"message.unsent"
  event. Whatever consumed the first webhook already has the full text in
  its own store permanently — "already left your infrastructure" bucket
  from step 4, not fixable from this side at all, only avoidable by not
  sending the raw text in the webhook payload to begin with.
- Push: the APNs alert already carried the full text at send time, before
  the 5-minute window even began. Unsend can't recall a notification
  already shown on a lock screen — this is the CVE-2026-28950 shape
  exactly: the real content left through a channel the unsend code doesn't
  touch and can't reach after the fact.
```

Step 3 checks authorization and the time window against the actual server code, not the UI:

```
Step 3: who can unsend, and when
The server checks `message.channelId !== req.user.currentChannelId` —
that's a *membership* check, not an *authorship* check. Any member of the
channel can unsend any other member's message, not just their own. Also:
no comparison against `message.createdAt` at all — `canUnsend()` only
exists in the client. A direct call to `DELETE /api/messages/:id` ten days
later, or from a completely different user in the same channel, is honored
exactly the same as a same-author call inside the 5-minute window. The
toast that appears after 5 minutes is purely cosmetic; the server enforces
neither the window nor the authorship the UI implies.
```

Step 4 names the hard boundary explicitly:

```
Step 4: what can't be recalled at all
The webhook-fed integration and the push payload both already received
the full text outside this system's control before unsend was ever
called. Nothing server-side can reach either one after the fact. If any
product copy or help text implies unsend removes the message "everywhere,"
that's inaccurate for both.
```

Report:

```
## recall-guard review: messages.js

1. Unsend is authorized by channel membership, not message authorship
   (BLOCK — confirmed root cause): any member of the channel can unsend
   any other member's message via a direct API call. Fix: check
   `message.senderId === req.user.id` (or an explicit moderator role),
   not just channel membership.

2. The 5-minute window exists only in the client (BLOCK, same endpoint):
   `canUnsend()` gates the button, but the server never compares against
   `message.createdAt`. A direct call unsends a 10-day-old message from
   any channel member. Fix: enforce the window server-side against the
   stored timestamp, and return the same error the client's toast implies.

3. The push notification already delivered the full message text to every
   device in the channel at send time, before any unsend window started
   (BLOCK): this is the exact CVE-2026-28950 shape — content that left
   through a channel unsend can't reach, confirmed already shown on a
   lock screen. Fix: don't put message text in the APNs alert body at all
   for channels where unsend is offered; use a generic alert and let the
   client fetch content only when opened, or accept and disclose that
   already-delivered pushes are out of unsend's reach.

4. The search index and the fired webhook both still hold the original
   text after unsend (CAUTION for the index — fixable; same BLOCK-class
   boundary as #3 for the webhook once already consumed by a third party):
   the Elasticsearch document is never deleted or reindexed, so search
   still surfaces "unsent" text. The webhook has no corresponding delete
   event at all, so any integration that stored the first payload keeps
   it indefinitely — not fixable from this side, only avoidable by never
   sending raw text in that payload.

## Verdict: BLOCK
Unsend currently authorizes the wrong thing (channel membership, not
authorship) and enforces no window at all server-side — either bug alone
lets anyone recall anyone else's message anytime. Fix both before this
ships. Independently, the push payload and the webhook already deliver
the full text through channels unsend cannot reach after the fact; those
need a design change (don't put recallable content there) rather than a
server-side patch, and any product copy claiming unsend removes a message
everywhere should be corrected to match what's actually true.
```
