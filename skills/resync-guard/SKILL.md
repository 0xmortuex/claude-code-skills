---
name: resync-guard
description: Audits whether a real-time client (WebSocket, SSE, or long-polling) that disconnects and reconnects actually resyncs the state it missed, instead of silently resuming the live stream as if nothing happened — a chat message that never arrives because the receiver was offline for the send, a live dashboard or presence indicator stuck on stale data until a manual refresh, a resume mechanism (Last-Event-ID, a sequence cursor, an SDK's missed-message hook) that exists in the client but was never wired to a server that actually keeps a replayable backlog. Use when reviewing or adding WebSocket/SSE/long-polling client code, or when asked "why did this update never show up", "does reconnect actually catch up on what we missed", "the live feed is stuck until I refresh", "users say messages go missing when their connection blips", or "audit our reconnection/resync logic".
---

# resync-guard

A real-time connection drops constantly — a phone loses signal in an elevator, a laptop sleeps, a proxy kills an idle socket — and every reconnect library handles the *transport* half of that correctly: back off, retry, re-open. What almost nothing handles automatically is the *data* half: everything the server pushed while the client was gone. Reopening the socket puts you back on the live stream starting from whatever the server sends next; it does not, by itself, tell you what you missed in between. A codebase can have flawless exponential-backoff reconnect logic and still lose data on every network blip, because "reconnected" and "caught up" are different guarantees and only the first one is usually tested.

The two transports don't even start from the same place. WebSocket (RFC 6455) has no session-resumption concept at all — a reconnect is a brand-new connection with zero relationship to the one before it; any continuity is entirely on the application to build. Server-Sent Events, by contrast, has resumption built into the spec: the browser's `EventSource` automatically remembers the last event's `id:` field and resends it as a `Last-Event-ID` header on reconnect, specifically so the server can replay what was missed. That built-in mechanism only closes the gap if the server actually reads that header and actually has something to replay it from — a server that ignores `Last-Event-ID` and just starts streaming fresh gets none of the benefit despite the client doing everything right.

This is a real, repeatedly reported bug class, not a hypothetical. Mattermost issue #16505 documents it cleanly: sender A sends a message while receiver B's client is mid-reconnect; the message never appears in B's stream — not on reconnect, not after switching channels away and back — and the sender gets no indication anything failed. The send path worked, the storage worked, and the bug was purely "reconnect resumed the live stream instead of resyncing the gap." Mattermost's own issue #30388 shows the other half of the same failure: the client SDK actually ships a `missedMessageListener` hook specifically to let integrators recover missed messages on reconnect — but it's opt-in and the issue itself is that it's undocumented, so most integrations built against the SDK never wire it up and get silent gaps despite the resync mechanism existing in the library the whole time.

## Step 1: find every place client state is *only* as current as the last message received

Grep for the WebSocket/SSE/long-poll connection setup and trace what state it feeds: chat/message streams, live counters or badges, presence/online indicators, collaborative-editing content, a live dashboard or ticker, a "processing" progress stream. For each one, ask whether that state is *also* refreshed by an independent, periodic full-fetch (a poll, a page navigation, a cache TTL) that would eventually paper over a missed push — or whether the stream is the *only* path that ever updates it, so a missed message is missed forever until something else forces a full reload. The second category is where a gap is a real, standing bug rather than a transient cosmetic delay.

## Step 2: check what the reconnect handler actually does, not just whether it reconnects

Find the reconnect logic (the `onclose`/`onerror` handler, the SDK's retry wrapper, the `EventSource` auto-reconnect) and trace what happens the instant the new connection opens:

- Does it just resume listening to the live stream and trust that existing client state is still correct?
- Or does it explicitly resync — replay from a cursor/`Last-Event-ID`/sequence number, or fall back to a full re-fetch of the affected state — before (or immediately after) rejoining the live stream?

A reconnect handler that only logs "reconnected" and re-subscribes to the same channel, with no resync step, is the exact shape of Mattermost #16505: transport-correct, data-silent.

## Step 3: if a resume mechanism exists, check it's real end-to-end, not just present in the client

A `Last-Event-ID` header, a `since`/cursor parameter, a sequence-number ack, or an SDK hook like `missedMessageListener` only helps if the server side actually honors it:

- Does the server read the resume token and replay from it, or does it accept the header/param and silently ignore it (indistinguishable from working, until you check)?
- What backs the replay — a bounded in-memory ring buffer, a durable log (Kafka/Redis Streams), or nothing? What happens when the gap exceeds however much history is kept: a full-state resync fallback, or a permanent, un-recoverable hole in exactly the range that was dropped?
- Is the resume mechanism wired into the actual reconnect path (step 2), or does it exist in the SDK/codebase unused — the exact `missedMessageListener` shape from #30388, where the capability exists but nothing calls it?

## Step 4: check whether a gap is visible to the user, or looks identical to "nothing happened"

Where steps 1–3 find a real gap (no resync, or a resync path that silently no-ops past its history window), check whether the UI shows any signal — a "reconnecting…", "you may have missed updates, refresh to catch up", or a visible stale-data indicator — versus rendering exactly as if the connection never dropped. A visible signal turns a silent data-loss bug into a recoverable UX annoyance; its absence is what makes the sender in #16505 have no idea their message never landed.

## Report

Lead with whichever applies: (a) a confirmed missed-update path — state that's stream-only-fed (step 1), a reconnect handler with no resync step (step 2), citing the exact handler and what it does instead; or (b) a resume mechanism that exists but doesn't actually close the gap — ignored server-side, unbacked by real history, or simply never called from the reconnect path (step 3). BLOCK for a confirmed gap on state with no independent refresh path and no user-visible signal — data is silently and permanently lost with nothing telling anyone. CAUTION for a gap that's bounded (a short backlog window covers most real blips) or where a periodic refresh elsewhere eventually self-heals it, or where the gap is real but the UI at least signals something was missed. SAFE only with evidence: an explicit resync step on reconnect, backed by a replay mechanism confirmed to work server-side, with a stated (and reasonable) bound on how long a gap it can recover from.

## Boundaries

- Not `job-warden`'s territory — that skill reviews server-side queue/cron correctness (a worker double-processing or dropping a job). This skill reviews whether a *client* that reconnects after a network gap gets the updates it missed, a delivery problem, not a processing one.
- Not `stale-guard`'s territory — `stale-guard` proves a cache can't serve wrong data on an ordinary request (every write path invalidates it). This skill is about a client that was disconnected during a push and never received it at all, independent of whether any cache is involved.
- Not `push-guard`'s or `pref-guard`'s territory — those cover push-notification token lifecycle and opt-out/preference correctness for out-of-app delivery. This skill covers in-app real-time streams (WebSocket/SSE/long-poll) a connected client is actively subscribed to.
- Doesn't cover the initial connection's authentication/authorization, or picking a transport (WebSocket vs. SSE vs. long-polling) from scratch — reviews whether an existing stream's reconnect behavior actually resyncs state, not how the stream was designed.
- Can't measure real-world disconnect frequency or typical gap duration from source alone — say so plainly when severity genuinely depends on it, rather than guessing how often the gap actually bites in production.
