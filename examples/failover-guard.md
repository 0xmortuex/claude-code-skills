# failover-guard — example

**Trigger:**

> we had a network blip between AZs last night and Orchestrator promoted
> our replica in us-west to primary. everything reconnected fine and
> nobody noticed until this morning, when a customer said an order they
> placed last night is gone. our setup: Postgres streaming replication,
> one primary + one replica, `synchronous_commit = off` (default), and
> Orchestrator configured to promote automatically on primary-unreachable
> with no explicit fencing step — it just updates the proxy's routing and
> moves on. the old primary in us-east came back up on its own 90 seconds
> later and we just... let it rejoin as a replica. can you audit whether
> our failover setup can actually lose writes like this?

**Response shape:**

Step 2 names the replication-mode gap:

```
Step 2: fully async replication, no bound on what's in flight
`synchronous_commit = off` means the primary acknowledges a write the
instant it's durable locally — before the replica has it at all. Normal
steady-state replication lag (not a spike, just ordinary lag) is the
exact-sized window of writes that are gone if promotion happens right
then. The missing order is consistent with this: it committed on the old
primary, was never replicated before the blip, and the promoted replica
was simply never going to have it.
```

Step 3 names the fencing gap, which made it worse:

```
Step 3: no fencing — the old primary wasn't stopped, it came back on its
own
Orchestrator promoted the replica but never fenced us-east — no STONITH,
no VIP reclaim, nothing preventing it from continuing to accept writes
during the 90 seconds it was unreachable to Orchestrator but still alive
to anything that could still route to it (app instances with a cached
connection, a direct client). It rejoining as a plain replica afterward
means any writes it took during that window were silently discarded by
replication setup, not reconciled — which is a second, independent way
the order could be gone even if it had nothing to do with lag.
```

Step 4 names the blind spot that let this go unnoticed until a customer complained:

```
Step 4: no signal that a loss window existed
Nothing flagged "promotion happened, writes in the preceding lag window
and the old primary's isolation window are unverified" — the system
just started serving us-west as primary. The only reason this surfaced
at all is a customer noticing a missing order; an affected write that
nobody happens to check for would stay silently lost.
```

Report:

```
## failover-guard review: Postgres primary/replica, Orchestrator auto-promote

1. `synchronous_commit = off` gives failover no floor on how much can be
   lost — every write inside normal replication lag at the instant of
   promotion is a candidate, and this incident is consistent with
   exactly that (BLOCK, Step 2).

2. Orchestrator's auto-promote has no fencing step — the old primary
   wasn't stopped, just out-routed, and it kept accepting connections
   (and possibly writes) for 90 seconds before rejoining as a replica,
   discarding whatever it took during that window with no reconciliation
   (BLOCK, Step 3).

3. No mechanism surfaces a post-failover loss/divergence window to
   anyone — this was found by a customer complaint, not by the system
   (CAUTION, Step 4).

4. Fix, in order of leverage: turn on at least semi-sync replication
   (`synchronous_commit = remote_write` or stronger) to a quorum so an
   acknowledged write isn't lost to lag; add an explicit fencing step to
   the promotion runbook (reclaim the VIP, or have Orchestrator
   kill/isolate the old primary before promotion is considered
   complete) so a reachable-but-partitioned old primary can't keep
   writing; and alert on every promotion event so the writes in the
   affected window get a reconciliation pass instead of surfacing as a
   support ticket.

## Verdict: BLOCK
Async replication with no fencing step means both the lag-loss and the
split-brain failure modes were live simultaneously, and this incident is
explained by at least one of them. Add synchronous (or semi-sync)
replication and an explicit fencing step before the next automatic
promotion.
```
