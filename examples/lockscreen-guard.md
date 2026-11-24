# lockscreen-guard — example

**Trigger:**

> we just added "someone liked your post" notifications. here's the
> notification code for that and for the existing DM notifications, which
> have always worked fine:
>
> ```kotlin
> // existing: direct-message notifications
> fun sendDmNotification(context: Context, senderName: String, messageBody: String) {
>     val publicVersion = NotificationCompat.Builder(context, CHANNEL_DM)
>         .setContentTitle("New message")
>         .setContentText("Someone sent you a message")
>         .build()
>
>     val notification = NotificationCompat.Builder(context, CHANNEL_DM)
>         .setContentTitle(senderName)
>         .setContentText(messageBody)
>         .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
>         .setPublicVersion(publicVersion)
>         .build()
>
>     NotificationManagerCompat.from(context).notify(DM_ID, notification)
> }
>
> // new: like notifications
> fun sendLikeNotification(context: Context, likerName: String, postSnippet: String) {
>     val notification = NotificationCompat.Builder(context, CHANNEL_LIKES)
>         .setContentTitle("$likerName liked your post")
>         .setContentText(postSnippet)
>         .build()
>
>     NotificationManagerCompat.from(context).notify(LIKE_ID, notification)
> }
>
> // channel setup
> val dmChannel = NotificationChannel(CHANNEL_DM, "Messages", IMPORTANCE_HIGH)
> val likesChannel = NotificationChannel(CHANNEL_LIKES, "Likes", IMPORTANCE_DEFAULT)
> ```

**Response shape:**

Step 1 enumerates both notification types and their call sites:

```
Step 1: notification types and call sites
Two call sites found: sendDmNotification (CHANNEL_DM) and
sendLikeNotification (CHANNEL_LIKES, the new one). They don't share a
builder or wrapper — sendLikeNotification constructs its own
NotificationCompat.Builder from scratch rather than reusing whatever
sendDmNotification uses.
```

Step 2 checks each one's redaction fields individually:

```
Step 2: redaction fields, per type
- DM notifications: sets VISIBILITY_PRIVATE and a genuinely redacted
  setPublicVersion() ("Someone sent you a message", no sender name or
  body). Correct.
- Like notifications: sets neither setVisibility nor setPublicVersion.
  No explicit visibility on this builder and no explicit visibility on
  CHANNEL_LIKES either, so it falls through to the platform default —
  VISIBILITY_PUBLIC. The liker's name and the post snippet will display
  in full on a locked device regardless of the user's "hide sensitive
  notifications" setting.
```

Step 3 traces why the gap exists:

```
Step 3: wired once, not carried forward
DM notifications were clearly built with the redaction API in mind —
the builder deliberately constructs a separate public-safe version.
Like notifications were added later as a new, independent call site
that doesn't reuse sendDmNotification's builder or its redaction
pattern; whoever wrote it most likely used NotificationCompat.Builder's
basic example rather than the existing DM code as a template. This is
the exact shape behind the in-pack grounding: one call site in the
same codebase handles redaction correctly, a newer one bypasses it
entirely, not through a deliberate decision.
```

Report:

```
## lockscreen-guard review: notifications.kt

| Type  | Channel       | Visibility set? | Public version? | Verdict |
|-------|---------------|------------------|------------------|---------|
| DM    | CHANNEL_DM    | VISIBILITY_PRIVATE | yes, redacted  | correct |
| Like  | CHANNEL_LIKES | none (defaults to PUBLIC) | none  | gap     |

1. sendLikeNotification sets no visibility and no public version, and
   CHANNEL_LIKES itself has no explicit default — the liker's name and
   the post snippet show in full on a locked device regardless of the
   user's lock-screen privacy setting (BLOCK — real sensitive content,
   the post snippet can include arbitrary user-written text).

2. sendDmNotification is correctly redacted and can serve as the
   template the like-notification code should have reused.

## Verdict: BLOCK
Fix sendLikeNotification to set VISIBILITY_PRIVATE and a redacted
setPublicVersion() ("Someone liked your post", no name or snippet),
matching the pattern sendDmNotification already establishes. Longer
term: route every notification-sending call site through one shared
builder/wrapper that sets redaction fields by default, so the next new
notification type doesn't have to remember to opt in — and audit
CHANNEL_LIKES and any other channel with no explicit visibility for
the same implicit-public default.
```
