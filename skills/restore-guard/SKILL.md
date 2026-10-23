---
name: restore-guard
description: Audit whether restoring a soft-deleted record (a trashed project, workspace, document, or customer within its grace period) actually reverses everything the delete triggered, not just flips the deleted_at flag back. Checks cascading soft-delete of child records in this and other services, search-index/cache tombstones the delete set, and whether a scheduled hard-delete/purge job gets cancelled or re-checks live state before it fires anyway. The mirror image of this pack's `erasure-guard` (which proves deletion reaches everywhere) and distinct from `overwrite-guard` (concurrent-edit conflicts, not restore completeness) and `tombstone` (removing unused code, not restoring live data). Use when adding/reviewing a trash/restore feature, when a purge job has a grace-period race with restore, or when asked "does restoring from trash actually bring everything back", "undelete this workspace", or "why does the restored item still look deleted somewhere".
---

# restore-guard

Soft-delete-and-restore looks symmetric in the schema — one `deleted_at` column, set on delete, cleared on restore — but the system around that column almost never is. Delete fans out: it tells a search index to drop the document, tells a CDN or cache layer to stop serving the old URL, cascades its own soft-delete into child records and sometimes into other services entirely, and enqueues a background job to permanently purge the row once the grace period expires. Restore gets built later, under less scrutiny, by someone who tested it by clicking "restore" and confirming the item reappears in the one list they were looking at. The flag flips. The rest of the fan-out — which took real engineering effort to build on the delete side — quietly has no return path, or has one that only covers the happy case where nothing else happened in between.

## Step 1: map everything the delete trigger set in motion

Don't start from the restore code — start from the delete code, the same way `erasure-guard` starts from the data rather than the deletion function. For the entity being restored, find every side effect its soft-delete triggers today: child/dependent records that get their own cascading soft-delete (line items under an order, documents under a workspace, members under a project), a search-index delete or exclusion filter, a CDN purge or cache invalidation, an outbound call to another service that soft-deletes its own mirrored copy, a notification/webhook firing ("this project was deleted"), and — the one that creates a race, not just a gap — a scheduled job enqueued to hard-delete the row once the grace period (often 7, 30, or 90 days) elapses.

## Step 2: trace the restore path against that map

For each side effect from step 1, find where restore reverses it. The recurring gaps:

- **Cascading soft-delete has no cascading restore.** The delete handler walks child records and sets their own `deleted_at`; the restore handler only clears the parent's. Grep for every place that sets `deleted_at` as a side effect of *this* entity's deletion, and confirm restore clears the same set — not just the row the restore endpoint was called on.
- **Search-index removal, but no re-index on restore.** If delete calls an explicit `index.delete(id)` or sets an `is_deleted` filter the query excludes, restore needs the equivalent explicit re-add — relying on "it'll get reindexed on the next normal edit" means the restored item is invisible to search until someone happens to edit it, with no error anywhere to surface that gap.
- **A negative-cache or "gone" tombstone with its own TTL.** Some caches don't just expire on miss — a delete path that writes an explicit `cache.set(key, NOT_FOUND, ttl=1h)` to stop a thundering-herd of lookups for a deleted item needs restore to explicitly clear *that* key, not just stop writing new tombstones; otherwise the item looks deleted to callers for up to the TTL even after a successful restore.
- **The purge job races restore instead of losing to it.** This is the one that isn't just a missing call — it's a timing bug. If the hard-delete job was enqueued with a fixed fire time (a delayed job, a cron sweep over `deleted_at < now() - grace_period`) and restore only clears `deleted_at` without touching the job, two shapes both fail silently: a job that checks nothing but its own payload fires and hard-deletes the just-restored row anyway; a sweep-style job that re-queries `deleted_at` at execution time is safe from that, but only if restore's write actually commits and is visible before the sweep's own read — confirm which shape this codebase uses rather than assuming the safer one.
- **Cross-service soft-delete is one-directional.** If deleting a workspace calls out to billing, notifications, or a separate search service to soft-delete their own copies, restore needs the matching fan-out back to each one — check for it explicitly; it's common for only the delete-side integration to exist because that was the feature that shipped first.

## Step 3: separate what restore should reverse from what it can't

Not every side effect of delete is undoable, and treating all of them as "restore must put this back exactly" produces the wrong fix as often as missing one does:

- **Must reverse for restore to be honest**: anything a user would check to confirm "it's back" — the record itself, its children, its presence in search and in any list view, cache/CDN state that would otherwise show it as gone.
- **Must be cancelled, not raced**: the scheduled hard-delete job. The fix here is control-flow (cancel the job, or make it re-check live state before acting), not a data-reversal step.
- **Can't and shouldn't be silently re-triggered**: one-time side effects that already fired and had their own real-world consequence — a "this project was deleted" email or webhook already sent, a billing credit or refund already issued for the deleted period, a seat already freed and reassigned to someone else. Flag these as "restore does not undo this" rather than building logic to auto-reverse them, since auto-reversing a refund or silently reassigning a seat back can cause a second, worse inconsistency.

## Step 4: verify, don't just click restore and check the one list

Confirm by checking each destination directly, the same discipline `erasure-guard` applies to the delete side: query the search index for the restored ID rather than trusting the re-index call exists in the diff, check that the specific cache/tombstone key is actually gone rather than assuming it expired, and confirm the hard-delete job for this ID is no longer scheduled (or that the job's own query no longer matches it) rather than reasoning from the code that it shouldn't fire. If the grace period is long enough to test directly, do a real restore-then-wait-past-old-fire-time check rather than only a code read.

## Report

Per side effect from step 1: whether restore reverses it, and whether that was verified against the live store/job queue or only read from code. Lead with any gap in the "must reverse" bucket that's still visibly wrong after restore — a restored item missing from search or still cached as gone is the failure a user actually reports. Call out the purge-job race separately and explicitly, since it's a timing bug that can pass every functional test today and still fire on a slower day. List the "can't reverse" bucket separately so a refund/notification that genuinely shouldn't be auto-reversed doesn't get flagged at the same severity as a real gap.

## Boundaries

- Not `erasure-guard` run backwards by assumption — it audits the same delete fan-out that skill maps, but restore completeness has to be checked against what *this* codebase's delete path actually does today, not against a generic list. Use `erasure-guard` to audit whether delete reaches everywhere; use this once a restore path exists and needs the same rigor applied to the way back.
- Not `overwrite-guard` — that skill is about two live editors silently clobbering each other's changes on a record that was never deleted. This skill is about a single record's state after a delete-then-restore cycle, no concurrent editing involved.
- Not `tombstone` — that skill proves an already-unused piece of *code* is safe to remove. This skill is about live, user-facing *data* that a user expects back after clicking restore.
- Not generic undo/redo or document version history (an editor's Ctrl+Z, a wiki's revision log) — this is scoped to a soft-delete-with-grace-period feature and the system-wide fan-out around it, not in-document edit history.
- Can't verify a third-party processor's own internal state any better than `erasure-guard` can on the delete side — it can confirm this codebase issues a restore call to a vendor and checks the response, not that the vendor's side actually reflects it.
