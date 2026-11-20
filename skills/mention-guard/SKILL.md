---
name: mention-guard
description: Audits whether a notification pipeline — @-mention alerts, "someone commented" emails, activity digests, or a cached link/permalink preview — checks that the recipient can actually see the subject before showing it to them, instead of trusting whatever permission applied when the notification was triggered or the preview was first cached. Use when adding or reviewing @-mention notifications, comment/activity alerts, or link-unfurling/permalink previews, right after a "someone saw content they shouldn't have" report, or when asked "does our notification check the recipient's permission", "can a permalink preview leak private content after access is revoked", "does @-mentioning someone expose a restricted page to them", or "audit our mention/notification authorization".
---

# mention-guard

A notification pipeline and the resource it's about usually live in different code paths, built at different times, by people solving different problems. Whoever wrote "send an email when someone mentions you" was solving a delivery problem — fan out an event to the right inbox — and reasonably assumed the authorization question was already handled upstream, by whatever gates viewing the page itself. It usually isn't. The notification-sender fires because an event happened, not because it re-ran the permission check the page's own view route runs; a link-preview/permalink-unfurl feature renders a cached snapshot because re-fetching on every view would be slow, not because anyone decided the cache should outlive the viewer's access. Both are correctness bugs that look, from inside the code that has them, like unrelated features working exactly as designed.

This is a recurring, independently-discovered gap, not a one-off: Confluence's CVE-2017-9505 sent watch/comment notification content for a page the recipient could no longer view, because a user who started watching while they still had access kept getting notified after it was revoked — the notification path never re-checked. Flarum's CVE-2023-22488 had the same root cause in a different product: "the notification-sending component does not check that the subject of the notification can be seen by the receiver" before dispatching it through any channel. Mattermost hit the *preview* side of this twice: CVE-2023-2792 let a crafted ephemeral-message error leak private-channel content back through a permalink preview, and CVE-2026-1629 (MMSA-2026-00580) let a cached permalink preview keep showing private-channel content to a viewer who had since lost access to that channel, until the cache expired or was reset. Four products, two different mechanisms (notification-send and preview-cache), the same shape: a second code path to the same content, built without wiring in the first path's permission check.

## Step 1: find every code path that shows resource content outside its normal view route

List every place content from a gated resource reaches a user *other than* them opening it through the page/API route that actually checks their access:

- @-mention and "someone commented/replied" notifications (push, email, in-app) — do they embed a snippet, title, or preview of the subject, or just a bare link the recipient has to click through (which re-checks access naturally)?
- Activity feeds and digests that surface "recent activity on things you follow" — same question: snippet embedded, or link-only?
- Link/permalink previews (unfurling a pasted or shared URL into a title/snippet/thumbnail) — rendered fresh on each view, or served from a cache keyed only by the resource, not by who's asking?
- Search-result snippets and autocomplete suggestions that surface a title or excerpt before the user opens the actual item.

Anywhere content is embedded rather than linked, the embedding code is a second authorization surface. If it was written without calling the same permission check the view route calls, it's a gap whether or not anyone's exploited it yet.

## Step 2: for each path found, check *when* the permission check runs relative to *when* the content is shown

Two distinct failure timings, both worth naming separately because they need different fixes:

- **Send-time or notify-time:** does the code that triggers a mention/comment notification check whether *this specific recipient* can currently see *this specific subject*, or does it fire purely off the event (someone typed `@user`, someone commented) with no permission check at all? The Confluence/Flarum shape: a user who had access when they started watching, or who still has a stale subscription row, keeps getting notified with content after that access is gone — because nothing re-checks at send time, only once, implicitly, whenever the subscription was created.
- **Cache-time vs. view-time:** for a preview/unfurl feature, is the cached snapshot keyed by resource *and viewer*, or by resource alone? A cache keyed only by resource serves the same rendered content to everyone who requests a preview of that URL, regardless of their own current access — meaning the first viewer's permission (at cache-write time) silently becomes every later viewer's permission (at cache-read time), including a viewer who's since been removed from the channel/doc entirely. That's the Mattermost CVE-2026-1629 shape exactly: the cache doesn't know access changed, because nothing invalidates it when a permission grant is revoked.

## Step 3: check what's actually exposed, and how it survives revocation

Severity here turns on two things: how much content leaks per notification, and how long the exposure lasts.

- A bare existence leak ("someone mentioned you in a page" with no title or snippet) is far less severe than an embedded snippet, full comment body, or thumbnail — call out which one a given gap actually sends.
- For the cache-time failure specifically: does revoking access anywhere invalidate or bust previews/caches already keyed to that resource, or does the stale preview keep serving until a TTL expires on its own (and if so, how long is that TTL — the Mattermost advisory's fix was explicit cache invalidation, not a shorter TTL, because a TTL alone still leaves a window)?
- For the send-time failure: does an unsubscribe, access-removal, or role-downgrade action clean up pending/queued notifications already generated for that resource, or only block *future* ones — leaving anything already in a queue or outbox to deliver on the old (now-revoked) permission?

## Report

Lead with the specific path and failure mode found, naming the exact notification type or preview feature, not a general "notifications might leak data" claim. BLOCK for an embedded snippet/body/thumbnail reaching a recipient with no permission check at send time, or a cross-viewer preview cache with no invalidation on access revocation and no bounded TTL. CAUTION for a bare existence-only notification with no content embedded, or a cache that does bust on revocation but only after a TTL long enough to matter. SAFE only with evidence: the notification-send or preview-render path calls the same permission check the resource's own view route calls, keyed to the actual current recipient/viewer, not a value captured when the subscription, cache entry, or queued job was created.

## Boundaries

- Not `revoke-guard`'s territory — that skill audits whether revoking access closes an already-open, continuous WebSocket/Socket.IO session. This skill audits a one-shot send (a notification) or a cached artifact (a preview), not a live connection.
- Not `digest-guard`'s territory — that skill audits a *recurring, scheduled* report or dashboard subscription re-checking access on every fire. This skill covers ad-hoc, event-triggered notifications (a single mention, a single comment) and permalink previews, not a schedule.
- Not `pref-guard`'s territory — that skill audits whether a user's own opt-out/preference choice is honored (should this send have gone out at all, by their own wishes). This skill audits a different question: given that a notification should fire, does it check whether *this* recipient is authorized to see the *content* it's about to show them.
- Not `subscription-guard`'s territory — that skill audits GraphQL subscriptions bypassing the HTTP-path authorization for the same transport split. This skill isn't transport-specific; a plain HTTP email-sending job with no permission check has the same gap as a WebSocket one.
- Doesn't design a notification or link-preview system from scratch — it audits whether an existing (or proposed) one wires the resource's actual permission check into the send/cache path, not which notification framework or unfurl library to adopt.
- Can't observe a real production cache's actual invalidation behavior or a real queue's in-flight job state from source alone — say plainly when confirming an exposure window needs inspecting live cache keys or queued-job data rather than a code read.
