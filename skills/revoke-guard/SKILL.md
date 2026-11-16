---
name: revoke-guard
description: Audits whether revoking a user's access to a document/room/resource actually closes or demotes their already-open WebSocket/Socket.IO real-time collaboration session, instead of leaving it to keep delivering live edits and data because the realtime layer only checked authorization once, at connect time. Use when adding or reviewing real-time collaborative editing, a live document/room feature, or socket-level authorization, or when asked "does revoking access close the live connection", "can a removed collaborator keep editing", "does our websocket re-check permissions after connect", or "audit our realtime authorization revocation".
---

# revoke-guard

A permission check that only runs once, at connect time, is a permission check with an expiration date nobody set. HTTP/REST endpoints re-run authorization on every request, so revoking access there takes effect on the very next call. A long-lived WebSocket or Socket.IO connection doesn't get that for free: if the server reads the user's role into the connection's in-memory context once at handshake and never looks it up again, revoking that role in the database changes nothing the socket can see — the live collaboration session keeps delivering edits, presence, and data for as long as the connection (and its heartbeats) stay up, completely independent of whatever the REST API now says.

This isn't hypothetical — it's the same root cause (CWE-613, insufficient session expiration) showing up independently across three different real-time collaboration products within the same window. A Docs product's CVE-2026-92800 (<5.4.1, CVSS 7.6): revoking access to a parent document didn't close the already-open WebSocket connections serving its sub-documents, so a removed collaborator kept receiving live edits through the child-doc sockets after their access to the parent was gone. Open WebUI's GHSA-45m8-cpm2-3v65 / CVE-2026-44553: the Yjs-based collaborative-document handlers checked a role cached inside the Socket.IO session pool instead of querying the database, so de-adminning a user left them with admin-level collaboration rights over the live socket for as long as its heartbeats kept it alive. Outline's CVE-2025-68663 (<1.1.0): suspending a user didn't terminate or block their existing WebSocket connections, so a suspended account could keep an existing connection open — or in some cases even establish a new one — and kept receiving document updates. Three different codebases, three different frameworks, the same gap: authorization checked at connect, never again.

## Step 1: find where the realtime layer learns who's allowed to do what

Locate the WebSocket/Socket.IO connection handler and trace exactly where authorization enters it:

- Is a role, permission set, or access grant read once at handshake/`connect` and stored in the connection's session object, in-memory context, or a per-socket cache — with every subsequent message handler trusting that stored value instead of re-checking it?
- Is there a *separate* authorization code path for the realtime transport from the one HTTP/REST requests go through — different middleware, a different guard, or (worst case) none at all on the socket layer because "the handshake already checked it once"? A check that's correct and current for REST but never wired into the socket path is still a gap, even if nobody wrote a bug in it — it's simply not there.
- For room/document-scoped access specifically (the CVE-2026-92800 shape): does joining a sub-resource's socket room re-validate access to that specific resource, or does it inherit whatever the parent resource's connection already established, so revoking the parent doesn't touch sockets already subscribed to children?

## Step 2: find what actually happens when access is revoked while a session is live

This is the step the connect-time check hides — trace the revocation code path (access removed, role downgraded, user suspended/deactivated) forward to see whether it reaches an already-open connection at all:

- Does revocation look up and forcibly close or downgrade the affected user's live socket(s), or does it only write the new state to the database and stop there, trusting that *something* will notice eventually?
- If there's a mechanism that's supposed to catch it eventually — a heartbeat/ping interval that re-validates on each beat, a periodic re-auth sweep, a TTL on the cached permission — check that it's actually wired to re-fetch current state (not just confirm the connection is alive) and that its interval is short enough to matter. A heartbeat that only checks "is this socket still connected" and never "is this socket still *authorized*" provides zero protection here, however reassuring it looks in the code.
- Is there a code path that re-establishes a cached stale role instead of tearing it down — e.g., a reconnect or resume handler that restores session state from a snapshot taken before the revocation, silently undoing it?

## Step 3: check what a still-open socket can actually do or see

Where step 1-2 found a real gap, determine what's actually exposed through it — this decides severity more than the plumbing bug does:

- Read access only (presence, cursor position, viewing live edits) vs. write access (the removed collaborator can still submit edits that land) are different severities — call out which one a given gap allows.
- For a removed *admin* or elevated role specifically (the Open WebUI shape): does the stale cached role let them perform privileged actions through the socket — not just see content, but moderate, delete, or grant access to others — that the system believes they no longer have?
- Does the exposure window have a hard ceiling (the connection drops on its own within some bounded time for an unrelated reason) or is it effectively unbounded (clients that auto-reconnect and keep heartbeats alive can hold a revoked session open indefinitely)?

## Report

Lead with whichever applies: (a) the realtime layer has no authorization re-check at all past the initial handshake — cite the specific handler and the cached value every subsequent message trusts; or (b) a re-check mechanism exists but doesn't actually look at current permissions (a liveness heartbeat mistaken for an authorization one, a reconnect path that restores a stale snapshot). BLOCK for a confirmed gap that lets a revoked or suspended user retain write access or admin-level actions through an already-open socket, with no bound on how long that can persist. CAUTION for a read-only exposure, or a gap bounded by a short, verified connection lifetime. SAFE only with evidence: a specific code path that looks up current access on revocation and forcibly closes or downgrades every open connection for that user, or a heartbeat/re-auth interval confirmed to re-fetch live permission state (not just liveness) at a bounded cadence.

## Boundaries

- Not `storm-guard`'s territory — that skill audits whether a fleet of clients reconnecting *at once* overwhelms auth/DB. This skill audits a single connection's authorization staying current while it stays open; it doesn't need a mass-reconnect event to matter.
- Not `backpressure-guard`'s or `resync-guard`'s territory — those audit delivery health (slow consumers, missed-message replay) for connections everyone agrees are authorized. This skill audits whether the connection should still be receiving anything at all.
- Not `overwrite-guard`'s territory — that skill audits concurrent-edit version/conflict checks between two *authorized* editors. This skill audits whether an editor is still authorized in the first place.
- Doesn't cover HTTP/REST session or token revocation — if the realtime layer re-validates via the same session/token store the REST API uses on every message (not just at connect), that's the fix, not a separate gap; this skill exists for the case where it doesn't.
- Can't verify actual production heartbeat intervals, connection-pool TTLs, or how long real clients keep auto-reconnecting from source alone — say plainly when confirming the exposure window needs a live trace or the infrastructure config rather than a code read.
- Doesn't design a realtime authorization architecture from scratch — reviews whether existing connect-time and revocation code actually keeps a live session's authorization current.
