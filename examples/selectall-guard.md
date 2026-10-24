# selectall-guard — example

**Trigger:**

> admins can filter the tickets table and click "select all 40 matching" to
> bulk-reassign them to another agent. it's a queued job since reassign can
> touch a lot of rows. does this actually do what the confirmation dialog
> says it does?
>
> ```python
> # tickets/views.py
> @require_admin
> def bulk_reassign(request):
>     filters = request.POST["filters"]        # serialized filter state
>     new_agent_id = request.POST["new_agent_id"]
>     matched_count = Ticket.objects.filter(**parse_filters(filters)).count()
>     reassign_job.enqueue(filters=filters, new_agent_id=new_agent_id)
>     return JsonResponse({"queued": matched_count})
>
> # tickets/jobs.py
> def reassign_job(filters, new_agent_id):
>     tickets = Ticket.objects.filter(**parse_filters(filters))
>     tickets.update(assigned_to=new_agent_id)
> ```

**Response shape:**

Claude traces the request shape first, not the per-row reassign path:

```
Step 1: which contract does this implement?
bulk_reassign sends `filters` itself through to the job — not a captured ID
list. reassign_job re-runs `Ticket.objects.filter(**parse_filters(filters))`
when it actually executes. This is the re-resolve contract.

The confirmation response (`matched_count`) comes from a `.count()` call at
enqueue time using the same parse_filters/filter call the job itself later
uses — same query shape, so the number the admin sees isn't computed by a
different path than the one that executes. That part is consistent.
```

Step 2 asks what the open-ended part of the filter does to that contract,
and checks the actual queue delay rather than assuming it's instant:

```
Step 2: failure mode for a re-resolve contract
The filter in question is "status=unassigned, team=billing" — an open
filter with no fixed scope (not a date range or an explicit ID set). Any
ticket that becomes unassigned-and-billing between the admin clicking
"select all 40 matching" and the worker actually picking up the job gets
swept into the reassignment, even though it was never part of the 40 the
admin saw and approved.

The queue itself isn't instant: this queue has no priority lane for
bulk-admin jobs and shares a worker pool with regular ticket-update
webhooks; under load, jobs sit for minutes. A ticket that gets unassigned by
an unrelated process in that window — including a *different* admin's bulk
action running concurrently — gets silently pulled into this one's scope.

No row-count bound exists either: parse_filters(filters) has no LIMIT, and
there's no check anywhere that re-running the filter at execution time still
returns ~40 rows before applying .update() to whatever it actually returns.
```

Step 3 checks what number the admin actually approved, confirming the
earlier finding rather than assuming it still holds once the queue delay is
in the picture:

```
Step 3: the approved number vs. the executed number
The `matched_count` shown in the confirmation is accurate *at enqueue time*
— same query, no drift there. But nothing re-confirms it's still accurate
*at execution time*, several minutes later. The UI effectively promises "40
tickets, these ones" and the backend delivers "whatever matches this filter
whenever a worker gets around to it" — a materially different operation
than what was confirmed, even though no single piece of code is wrong in
isolation.
```

Report leads with the concrete scope-creep scenario rather than a generic
"re-resolve is risky" warning:

```
## selectall-guard audit: bulk_reassign / reassign_job

**Contract:** re-resolve (filters serialized through to the job; no ID
snapshot). Confirmation count and execution query use the same filter path
— no divergence there.

1. FAIL — scope creep on an open filter through a real queue delay. The
   filter ("status=unassigned, team=billing") has no fixed bound, the job
   queue has no priority lane and measurably sits for minutes under load,
   and any ticket that becomes unassigned-and-billing in that window —
   including from another admin's concurrent action — gets reassigned
   despite never appearing in the 40 the admin approved. Fix: resolve the
   ID set once at enqueue time (switch this action to snapshot) and have
   reassign_job act on that fixed list, or have the job re-check
   `matched_count` against its own re-run count and abort/flag a large
   divergence instead of blindly applying .update() to whatever it finds.
2. FAIL — no row-count bound. Nothing caps how large a re-resolved match
   can grow to, and nothing fires an error or requires re-confirmation if
   execution-time count diverges materially from the approved count. Fix:
   add a check in reassign_job — if the live count differs from the
   enqueue-time count by more than a small tolerance, stop and surface an
   error rather than silently reassigning a different set of tickets than
   was approved.

## Verdict: BLOCK
The confirmation dialog's count is real at the moment it's shown, but the
contract that executes afterward can silently reassign tickets the admin
never saw, through an ordinary queue delay rather than any edge case. Fix
both — snapshot the ID set (or add an execution-time divergence check) and
add a hard bound — before this ships past a toy ticket count.
```
