# erasure-guard — example

**Trigger:**

> we're adding a "delete my account" button to settings. here's the deletion
> code — can you check it actually deletes everything before we ship it?
>
> ```python
> # accounts/deletion.py
> def delete_account(user_id):
>     user = User.objects.get(id=user_id)
>     user.delete()  # ON DELETE CASCADE covers orders, addresses, sessions
>     cache.delete(f"user:{user_id}:profile")
>
> # search/indexing.py (unrelated file, written 6 months after deletion.py)
> def index_user_profile(user):
>     es_client.index(index="profiles", id=user.id, body=user.to_search_doc())
>
> # integrations/esp.py (unrelated file, written a year ago)
> def sync_contact(user):
>     esp_client.upsert_contact(email=user.email, traits=user.traits())
> ```

**Response shape:**

Claude starts from the data, not the deletion function — the two other files
above are found by grepping for `user.id`/`user.email` usage across the repo,
not by reading `delete_account` and assuming it's complete:

```
Step 1: every place this user's identifiable data materializes
- primary tables: User, Order, Address, Session — all FK-linked, CASCADE covers them
- cache: `user:{id}:profile` key — explicitly deleted in delete_account
- search index: Elasticsearch `profiles` index, written by search/indexing.py
  on every profile save — no corresponding delete call found anywhere
- ESP (marketing email provider): integrations/esp.py upserts a contact on
  signup and on profile edit — no corresponding remove/suppress call found
- backups: nightly full DB snapshot, standard retention, not app-code's concern
  directly but still a destination to classify
```

Step 2 traces the actual deletion code path against that map, and the gap is
exactly what the skill's step 2 predicts — new stores added after the
original delete function was written were never wired into it:

```
Step 2: does the deletion path reach each destination?
- CASCADE tables: yes, `user.delete()` reaches all four FK-linked tables.
- cache key: yes, explicit `cache.delete(...)` call present.
- search index: NO. Grepped for `es_client.delete` anywhere in the codebase —
  zero results. indexing.py has an index/upsert path with no delete
  counterpart. The document written on the user's last profile save is
  never removed.
- ESP: NO. Grepped for any call to esp_client's remove/suppress/unsubscribe
  method — none exists. sync_contact is one-directional (push only); nothing
  in delete_account or anywhere else calls it to remove or suppress the
  contact.
- backups: not code-reachable by definition — classify separately, don't
  treat "not reached by delete_account" as a bug the way the two above are.
```

Step 3 classifies each destination instead of treating all five the same —
this is what keeps the backup finding from diluting the two real gaps:

```
Step 3: classification
- User/Order/Address/Session, cache, search index, ESP contact: all
  must-hard-delete — an ordinary support agent or a search query could
  surface this user's data post-deletion through any of them.
- Orders specifically: flagged for a second look — if there's a tax/
  financial retention requirement on order records, CASCADE-deleting them
  outright may itself be wrong (should be anonymize, not delete) — but
  that's a separate question from this audit's scope; noted, not resolved,
  since no retention policy was referenced in what was shared.
- backup snapshot: acceptable-beyond-use bucket, conditional on two things
  neither confirmed nor denied by the code shown: (a) restoring this backup
  doesn't re-populate a deleted user without an exclusion/re-delete step,
  and (b) it expires on the normal retention schedule rather than being
  held specifically because of this user. Flagged as "needs confirmation,"
  not as a finding — it's not a bug the way the search index and ESP gaps are.
```

Step 4 verifies rather than trusting that the fix, once written, actually
worked:

```
Step 4: verify, don't just review
- Once a delete call is added for the search index, confirm by querying
  Elasticsearch directly for the deleted user's ID post-delete — and note
  Lucene's real segment-merge behavior: absence from query results is
  confirmable immediately, absence from the on-disk segment is not, and
  that distinction should be stated rather than glossed if this ever needs
  to be defended as a compliance answer.
- Once an ESP removal call is added, confirm by checking the API response
  for success rather than firing-and-forgetting it the way sync_contact
  currently does — and if the ESP's own internal replication delay means
  the contact might still receive one in-flight campaign send, say that
  limit honestly rather than certifying instant removal.
```

Report leads with the two live gaps, keeps the backup note separate and
clearly lower-severity, and doesn't flatten them together:

```
## erasure-guard audit: delete_account completeness

1. Search index (Elasticsearch `profiles`): FAIL — no delete call exists.
   A deleted user's last-saved profile remains searchable indefinitely.
   Must-hard-delete bucket. Fix: call `es_client.delete(index="profiles",
   id=user_id)` in delete_account before or alongside the ORM delete.
2. ESP contact: FAIL — no suppression/removal call exists. A deleted user
   keeps receiving marketing email from a contact record delete_account
   never touches. Must-hard-delete bucket. Fix: call the ESP's contact-
   removal or suppression endpoint and check its response.
3. Primary tables + cache: OK — CASCADE and the explicit cache.delete both
   verified reachable from the code shown.
4. Backup snapshot: needs confirmation, not a finding — beyond-use bucket
   is acceptable *if* restore-time exclusion and normal expiry both hold;
   neither was shown in what was shared, so ask rather than assume.
5. Orders retention: flagged out of scope — if a financial retention rule
   applies, CASCADE-deleting orders outright may need to become anonymize
   instead; a separate question from this audit, surfaced for follow-up.

## Verdict: BLOCK
Two must-hard-delete destinations (search index, ESP) are completely
unreached by the deletion path — this is not a partial-coverage nuance,
it's the erasure request silently not being honored for anything a search
query or a marketing send can surface. Ship both fixes together, verify
each directly (query the index, check the ESP delete response) rather than
re-reading the code and calling it done, and get an answer on backup
restore-exclusion and order retention before treating those two as settled.
```
