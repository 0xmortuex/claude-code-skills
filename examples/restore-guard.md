# restore-guard — example

**Trigger:**

> we added a 30-day trash for workspaces a while back and it's been fine, but
> someone just restored one and their teammates say search still shows it as
> deleted. here's the delete and restore code — can you check restore
> actually undoes everything delete does?
>
> ```python
> # workspaces/deletion.py
> def soft_delete_workspace(workspace_id):
>     workspace = Workspace.objects.get(id=workspace_id)
>     workspace.deleted_at = now()
>     workspace.save()
>     for doc in workspace.documents.all():
>         doc.deleted_at = now()
>         doc.save()
>     search_client.delete(index="workspaces", id=workspace_id)
>     cache.set(f"workspace:{workspace_id}", "GONE", ttl=3600)
>     purge_queue.enqueue_at(now() + timedelta(days=30), hard_delete_workspace, workspace_id)
>
> # workspaces/restoration.py
> def restore_workspace(workspace_id):
>     workspace = Workspace.objects.get(id=workspace_id)
>     workspace.deleted_at = None
>     workspace.save()
> ```

**Response shape:**

Claude starts from the delete function's actual fan-out, not from reading
`restore_workspace` and asking whether it "looks right" in isolation:

```
Step 1: everything soft_delete_workspace sets in motion
- parent record: workspace.deleted_at set
- child records: every document under the workspace gets its own deleted_at set
- search index: explicit search_client.delete() call — the doc is removed,
  not just filtered
- cache: an explicit GONE tombstone written with a 1-hour TTL (not a plain
  cache miss — this is a negative cache specifically to avoid repeated
  lookups hitting the DB for a deleted workspace)
- purge job: a hard-delete enqueued for exactly 30 days later, keyed only on
  workspace_id and a fixed fire time — no re-check of current state baked
  into the payload shown
```

Step 2 traces `restore_workspace` against each of those five, and the gap
matches exactly what was reported:

```
Step 2: does restore reverse each?
- parent deleted_at: yes, cleared.
- child documents' deleted_at: NO. restore_workspace never touches
  workspace.documents — every document soft-deleted alongside the workspace
  stays soft-deleted after the workspace itself is restored.
- search index: NO re-index call anywhere in restoration.py. The workspace
  was explicitly removed from the index on delete; nothing adds it back on
  restore. This is the bug matching the report — search still shows it as
  deleted because, from the index's point of view, it still is.
- cache tombstone: NO. The GONE key written on delete has a 1-hour TTL and
  nothing in restore clears it early — for up to an hour after a successful
  restore, any read path that checks this cache key first will still get
  GONE.
- purge job: enqueued for +30 days, fixed fire time, no re-check found in
  hard_delete_workspace's own body (not shown above, flagged to inspect) —
  if it doesn't re-query deleted_at before deleting, this workspace is
  scheduled to be permanently destroyed in 30 days regardless of the restore
  that just happened.
```

Step 3 separates what must come back from what's a timing bug needing a
different kind of fix, rather than treating all four gaps the same:

```
Step 3: classification
- child documents, search index, cache tombstone: must-reverse bucket — a
  user checking "is it really back" via search or a doc list would see it as
  still gone. Real, user-visible bugs.
- purge job: different bucket entirely — not a missing data-reversal step
  but a race. The fix is control flow (cancel the enqueued job on restore,
  or make hard_delete_workspace re-check deleted_at at execution time), not
  "restore more things."
```

Step 4 calls for verifying each fix against the live store rather than
re-reading the code and calling it done:

```
Step 4: verify
- after adding the documents.update(deleted_at=None) call, confirm by
  querying for soft-deleted documents under this workspace_id directly —
  zero should remain.
- after adding search_client.index(...) back on restore, confirm by
  querying the search index for this ID, not by assuming the call succeeded.
- after adding cache.delete(f"workspace:{workspace_id}") to restore, confirm
  the key is actually gone — don't rely on the 1-hour TTL "fixing itself."
- for the purge job: inspect hard_delete_workspace's body directly. If it
  re-queries deleted_at before deleting, cancelling isn't strictly required
  but is still the safer fix; if it doesn't, cancelling or re-checking is
  mandatory, not optional — confirm whichever fix lands actually prevents
  the job from firing by testing past the fire time in staging, not just by
  reading the new code.
```

Report leads with the reported bug, surfaces the two gaps nobody reported
yet, and keeps the purge-job race in its own severity bucket:

```
## restore-guard audit: restore_workspace completeness

1. Search index: FAIL — no re-index call on restore. Matches the reported
   bug exactly; a restored workspace stays invisible to search until an
   unrelated edit happens to re-trigger indexing. Fix: call
   search_client.index(...) in restore_workspace.
2. Child documents: FAIL — cascading soft-delete has no cascading restore.
   Every document under the workspace stays soft-deleted (and so invisible
   in any doc-list view) after the parent workspace is restored. Fix:
   clear deleted_at on workspace.documents in the same transaction.
3. Cache tombstone: FAIL — the 1-hour GONE negative-cache key isn't cleared
   on restore. Lower urgency than 1-2 (self-heals in ≤1h) but still a real
   gap users can hit. Fix: explicit cache.delete on restore.
4. Purge job race (separate bucket — control flow, not data reversal):
   NEEDS VERIFICATION — hard_delete_workspace's re-check behavior wasn't
   shown. If it doesn't re-query deleted_at at execution time, this
   workspace is still scheduled for permanent deletion in 30 days despite
   being restored today. Fix: cancel the enqueued job on restore, or add a
   live re-check inside hard_delete_workspace — verify by testing past the
   original fire time, not by code review alone.

## Verdict: BLOCK
Two must-reverse gaps (search, child documents) are live and match the
reported symptom; a third (cache) is lower-severity but real. The purge-job
race is the one to treat as most urgent despite looking like an edge case —
it can pass every test today and still permanently destroy a restored
workspace on day 30. Ship all three data-reversal fixes together, resolve
the purge-job question before calling this done, and verify each against
the live index/cache/job queue rather than trusting the new code.
```
