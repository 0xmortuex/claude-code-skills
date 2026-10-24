---
name: selectall-guard
description: Audit an admin UI's "select all N matching filter" bulk action (delete/export/reassign/tag across every row a filter matches, not just the visible page) for the two backend questions the checkbox-and-toolbar UI never answers — does execution re-resolve the filter (open to scope creep from rows that start matching after selection) or snapshot the matched ID set at selection time (open to acting on rows that stopped matching before execution), and is there any row-count bound a user can actually see when it's hit. Use when adding/reviewing a "select all across pages" bulk action, especially a queued/async one, or when asked "does select-all re-run the filter or use the list I saw", "what happens if a row changes while this bulk job is running", or "is there a limit on how many rows select-all can touch".
---

# selectall-guard

An admin table with checkboxes and a "select all 1,247 matching this filter" link looks like a UI feature, and the UI side genuinely is one — PatternFly, shadcn, and most admin-table components ship the pagination-aware select-all toggle for free. What they don't ship, and what nothing enforces by looking at the frontend, is the backend contract that toggle implies: the user saw a count, authorized an action against that count, and the server has to decide *when* it figures out which rows that actually means.

There are exactly two ways to implement that, and each has a failure mode the other doesn't:

- **Snapshot at selection time**: the client (or a first server round-trip) resolves the filter once, captures the matching ID set, and the action executes against that fixed list. This is safe from scope creep but can act on stale data — a row that stopped matching between selection and execution (its status changed, it was deleted, it moved out of the filtered date range) still gets the action applied, because the ID list doesn't know that.
- **Re-resolve at execution time**: the action re-runs the filter query when it actually executes, rather than trusting a captured list. This is safe from acting on stale rows but open to scope creep — any row that *starts* matching the filter between selection and execution (created, edited into matching, or simply matching a filter with no fixed bound like "all unread" or "all with status=pending") gets swept in, even though the user never saw it in the count they approved. For a synchronous action this window is milliseconds; for a queued job that runs minutes or hours later — common for anything touching more than a page of rows — the window is exactly as long as the queue backlog, and "reassign all 40 unassigned tickets" silently becomes "reassign whatever's unassigned by the time a worker gets to it."

Neither approach is wrong by default. The bug is not knowing which one the code does, or having a UI that implies one (showing a frozen count, "40 selected") while the backend actually does the other.

## Step 1: find which contract the code implements

Trace the actual request the "select all" action sends, not the per-row checkbox path (that one's almost always a plain ID list and isn't the question here). Look for one of two shapes:

- The request carries the filter itself (query params, a saved filter ID, a search DSL fragment) and the handler runs that filter query at execution time → **re-resolve**.
- The request carries an ID list — either collected client-side by paging through every result, or server-resolved once in a separate "resolve selection" call before the action request → **snapshot**.

A third shape exists and is worth flagging on its own: the request carries *both* a filter and a client-reported count ("1,247 matching"), and the handler trusts the filter without checking that re-running it still produces approximately that count. That's a re-resolve implementation wearing a snapshot's UI — the user approved a number that the execution path never actually re-confirms.

## Step 2: check the failure mode that contract implies

- **If re-resolve**: find whether the filter has a fixed scope (a date range, a specific set of IDs) or an open one (status flags, "all unread", anything that can keep matching new rows indefinitely). For an open filter feeding an async/queued action, trace the actual gap between enqueue and execution — a job-queue dashboard, a cron interval, a batch size over a large table — and ask whether a row created or edited into matching during that gap should really be included. If the answer is no, the fix is resolving the ID set once at enqueue time (switching to snapshot for this action) or re-checking the pre-enqueue timestamp as part of the execution filter, not just living with the drift.
- **If snapshot**: find how long the ID list lives before execution (held in a request body and executed inline is low-risk; serialized into a background job that runs later is the risk window) and whether execution re-validates each ID's current state before acting, or blindly applies the action to IDs that may no longer match, may have been deleted, or may belong to a record whose permissions changed. A delete-all-matching that fires on an ID the user's later edit pulled out of scope is a real, reportable gap — flag it with the specific action and the specific state change that escapes it.
- **Either way — the row-count bound**: check whether "select all" has any ceiling on how many rows one action can touch, and whether crossing it produces an explicit error/confirmation rather than either silently truncating (the user believes all 50,000 rows got the action; only the first 500 did) or silently running unbounded (one click triggers a full-table operation with no circuit breaker). A bound with no user-visible signal when it's hit is as bad as no bound — check both that it exists and that hitting it is observable.

## Step 3: check the number the user actually approved

Whatever the count shown in the confirmation dialog or toolbar was computed from — client-side pagination metadata, a separate count query, the same filter the action itself uses — confirm it's computed close enough in time and from the same filter logic that it won't diverge from what execution actually touches. A confirmation that says "1,247" from a count query with a different `WHERE` clause than the action's own query (common when the count comes from a cached aggregate or a slightly different endpoint) can be wrong independently of the snapshot/re-resolve question above.

## Report

State which contract the code implements (snapshot or re-resolve, or the hybrid-trusting-a-stale-count shape) with the file/line of the deciding query or ID-capture point. Then report, concretely: what happens to a row that changes state between selection and execution under that contract, whether that's the behavior a user would expect from the confirmation they saw, and whether a row-count bound exists and is observable when hit. Don't flag the contract choice itself as a bug — flag the specific gap it leaves open, named against this codebase's actual filters and queue delay, not a hypothetical one.

## Boundaries

- Not `job-warden` — that skill audits whether a queued action processes each item correctly once scope is fixed (idempotency, poison messages, overlap). This skill audits how that scope gets fixed in the first place, before `job-warden`'s questions are even relevant.
- Not `backfill-pilot` — that's an engineer-run, one-off data migration over a known table, built with resumability and dry-runs in mind from the start. This is a user-triggered admin feature over a filter the user chose, usually with no dry-run step at all.
- Not `blast-guard` — that skill is about irreversible sends to a real audience (email/push/SMS) where the audience-correctness check is the whole skill. This skill covers any bulk admin action (delete, export, reassign, tag, archive), reversible or not, where the specific bug is scope drift between selection and execution rather than audience targeting.
- Not `overwrite-guard` — concurrent edits to one record by two editors, no bulk selection involved.
- Can't evaluate a "select all" feature that doesn't exist yet from a design doc alone — needs the actual request/response shape (or a concrete proposed one) to say which contract it implements, not a description of intended behavior.
