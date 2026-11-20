# mention-guard — example

**Trigger:**

> a user reported that they got an email saying "alex mentioned you in
> 'Q4 Comp Planning'" with the actual comment text quoted in the email body
> — but they're not on that document's share list and get an access-denied
> page when they click through. separately, our Slack-style "unfurl" of a
> pasted doc link shows a cached title+snippet preview, and someone asked
> whether that still shows content after they're removed from a channel.
> here's the relevant code:
>
> ```python
> # mentions.py
> def notify_mention(mentioned_user, document, comment_text):
>     send_email(
>         to=mentioned_user.email,
>         subject=f"{comment_text.author} mentioned you in '{document.title}'",
>         body=comment_text.body,  # full comment text embedded
>     )
>
> # unfurl.py
> preview_cache = {}  # keyed by document_id only
>
> def get_link_preview(document_id, viewer):
>     if document_id in preview_cache:
>         return preview_cache[document_id]
>     preview = render_preview(document_id)  # rendered once, no viewer check
>     preview_cache[document_id] = preview
>     return preview
> ```

**Response shape:**

Step 1 inventories every path that shows content outside the normal view route:

```
Step 1: content paths outside the view route
Two found. `notify_mention` embeds the full `comment_text.body` in the
email it sends — not a bare "someone mentioned you" link. `get_link_preview`
returns a rendered title+snippet for any viewer who requests it, served
from `preview_cache` for anyone after the first render.
```

Step 2 checks when (if ever) either path checks the recipient's access:

```
Step 2: timing of the permission check
`notify_mention` has no permission check at all — it's called from the
comment-creation handler purely because `@alex` appeared in the text, with
no lookup of whether `mentioned_user` can see `document`. This is the
Confluence CVE-2017-9505 / Flarum CVE-2023-22488 shape exactly: the
notification fires off the event, not off a check that the recipient and
the subject's access actually line up.

`get_link_preview`'s cache is keyed by `document_id` alone, not by
`document_id + viewer`. The first person who ever previews a given
document's link renders and caches it once; every later caller — including
someone later removed from the document's share list or the channel it
lives in — gets that same cached render with no re-check. This is the
Mattermost CVE-2026-1629 shape: a cached preview outliving the viewer's
access, with nothing to invalidate it when access changes.
```

Step 3 checks exposure severity and how long it persists:

```
Step 3: what's exposed, and for how long
The mention email leaks the full comment body, not just the fact that a
mention happened — high severity, since the reporting user received
confidential comp-planning text they have zero access to view in the app.
Nothing in the access-removal or document-sharing code touches
`preview_cache` — there's no invalidation hook at all, so the cached
preview is exposed indefinitely, bounded only by the process restarting
and clearing the in-memory dict, not by any access change.
```

Report:

```
## mention-guard review: mentions.py, unfurl.py

1. `notify_mention` embeds the full comment body in the notification email
   with zero permission check on `mentioned_user` against `document` —
   this is exactly the reported incident: a user with no document access
   received its content by being @-mentioned (BLOCK, Step 1–2).

2. `get_link_preview`'s cache is keyed by document only, not by viewer,
   so a cached render silently becomes shared across every future viewer
   regardless of their own current access, with no invalidation when
   access is revoked (BLOCK, Step 2 — this is the live risk behind the
   second question, even though nobody's reported it being hit yet).

## Verdict: BLOCK
Both paths route around the document's own access check entirely. Fix, in
order of leverage: make `notify_mention` check `mentioned_user`'s current
access to `document` before sending, and if they can't see it, send a
content-free "someone mentioned you in a document you don't have access
to" notice (or nothing) instead of the comment body; and key
`preview_cache` by `(document_id, viewer_id)` with the same access check
`render_preview` would need to run for a direct view, or drop the cache
entirely and re-render per viewer, with an invalidation hook wired into
whatever code already removes a user's document/channel access.
```
