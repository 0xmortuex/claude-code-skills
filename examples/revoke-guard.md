# revoke-guard — example

**Trigger:**

> we just removed a contractor from a project doc, but they said they could
> still see people typing in real time for like 10 minutes after we removed
> them. here's our collab socket code:
>
> ```js
> // server: collab.js
> io.on('connection', async (socket) => {
>   const userId = socket.handshake.auth.userId;
>   const docId = socket.handshake.query.docId;
>   const access = await Access.find({ userId, docId });
>   if (!access) return socket.disconnect();
>
>   socket.role = access.role; // cached for the life of the connection
>   socket.join(`doc:${docId}`);
>
>   socket.on('edit', (delta) => {
>     if (socket.role === 'viewer') return; // viewers can't write
>     io.to(`doc:${docId}`).emit('edit', delta);
>     applyDelta(docId, delta);
>   });
> });
>
> // route: removing a collaborator
> router.delete('/docs/:docId/access/:userId', requireOwner, async (req, res) => {
>   await Access.deleteOne({ userId: req.params.userId, docId: req.params.docId });
>   res.json({ ok: true });
> });
> ```

**Response shape:**

Step 1 traces where the socket learns the user's role, and whether anything re-checks it:

```
Step 1: where authorization enters the realtime layer
`io.on('connection', ...)` reads the Access row once at handshake and
caches the role on `socket.role`. Every later `edit` handler trusts
that cached value — there is no code anywhere in the message handlers
that re-queries `Access`. This is the connect-once, never-again shape:
once a socket exists, nothing it does from that point forward touches
the database for authorization again.
```

Step 2 traces the revocation path forward to see if it reaches the open socket:

```
Step 2: what revocation actually does
DELETE /docs/:docId/access/:userId removes the Access row — correct
for the REST layer, since any *new* connection attempt will now get
rejected by step 1's `if (!access)` check. But it does nothing to
sockets that are already connected: it doesn't look up the removed
user's live socket, doesn't call `.disconnect()` on it, and doesn't
emit anything that would make the client-side code re-check access.
The contractor's existing socket still has `socket.role` cached from
before the delete ran, and keeps it until the connection drops for an
unrelated reason (tab close, network blip, idle timeout) — this
matches the reported ~10 minutes, which is just how long their tab
happened to stay open and connected.
```

Step 3 checks what the still-open socket can actually do, not just see:

```
Step 3: exposure through the open socket
The contractor's role was 'editor', not 'viewer' — `socket.role ===
'viewer'` is the only gate on the `edit` handler, so the stale cached
role still passes it. For the full exposure window, the removed
contractor could not only watch live edits (presence/content
exposure) but submit edits of their own that `applyDelta` persists to
the document — this is write access surviving the revocation, not
just a read-only leak.
```

Report:

```
## revoke-guard review: collab.js

1. The realtime layer has no re-authorization path at all past the
   initial handshake — `socket.role` is read once in the `connection`
   handler and never re-checked by any later message handler (BLOCK —
   confirmed root cause).

2. DELETE /docs/:docId/access/:userId only removes the Access row; it
   never looks up or disconnects the removed user's existing socket(s)
   for that doc (BLOCK, same finding as #1 but names the missing fix):
   revocation is REST-correct and realtime-silent.

3. The exposed access is write, not just read — the cached role was
   'editor', so the removed contractor could submit edits that
   `applyDelta` persists for as long as the socket stays open, with no
   bound shorter than "until the connection happens to drop" (BLOCK,
   raises severity: this is a removed collaborator still modifying the
   document, not just watching it).

## Verdict: BLOCK
Revocation only ever reached the database, never the live connection,
and the role it left cached was write-capable. Fix: on every access
removal/downgrade, look up that user's open socket(s) for the affected
doc and either disconnect them or push a forced role re-fetch that the
`edit` handler actually honors — and make every message handler read
current access (or a short-TTL cache of it) instead of the one-time
value captured at connect.
```
