---
name: tombstone
description: Prove — with production evidence, not just a repo-wide grep — that an externally-reachable API endpoint, database column/table, exported package function, or infrequent scheduled job is actually unused before deleting it. Use when the user asks "can I delete this endpoint/column/table", "is this still used", "nobody calls this anymore, right?", or is about to remove code reachable from outside this repo (other services, mobile clients on old app versions, third-party webhooks, BI tools querying the DB directly, quarterly/monthly batch jobs). Static dead-code tools (knip, ts-prune, vulture, depcheck, plain grep) only prove "no reference inside this repo" — this skill covers the gap between that and "actually unused," and is not a static-analysis tool itself.
---

# tombstone

`knip`, `ts-prune`, `vulture`, and a careful grep all answer the same question well: does anything *in this repository* still reference this code? That's a real answer, and it's sufficient for private helpers only ever called from within the repo. It is not sufficient the moment the surface is reachable from outside the repo's own source: a public or internal API endpoint another team's service still calls, a mobile client on an app version from eight months ago that nobody updates, a DB column another service reads directly (not through your ORM), a webhook a third party fires, or a batch job that only runs quarterly. Static analysis is blind to all of these — it can only see what's in front of it — and deleting on that confidence alone is how "obviously dead" code turns into a production incident from a caller nobody thought to check.

The fix is not more grep, it's a different kind of evidence: proof that the surface wasn't *invoked*, gathered from wherever invocations actually get recorded, over a window long enough to catch its real calling frequency.

## Step 1 — classify reachability before doing anything else

- **Intra-repo only**: a private function, unexported type, or internal module with no external HTTP/DB/queue/package surface, called only from files in this same repo. Static tools already answered this — this skill has nothing to add, don't slow the deletion down with log-hunting it doesn't need.
- **Externally reachable**: anything callable by something outside this repo's own deploy — a route, an RPC method, a DB table/column, a published package export, a message-queue topic, a scheduled job. This is where the rest of this skill applies.

When in doubt, reachability is the union of everything that isn't provably private: if you can't name every caller from reading this repo, treat it as externally reachable.

## Step 2 — gather evidence matched to the surface type

Each surface type records its calls somewhere different; use the source that would actually catch a real caller, not the one that's easiest to query:

- **HTTP/RPC endpoints**: gateway/access logs (nginx, ALB, API gateway, service mesh) filtered by path and method, or an app-level request counter (a Prometheus counter per route) — over a window that covers the endpoint's real traffic pattern, not just "since deploy." Check the `User-Agent` / client-id on any hits found — that's usually the fastest way to identify the actual caller and go ask them directly instead of only reasoning from logs.
- **DB columns/tables**: `pg_stat_statements` (or the equivalent query log) for `SELECT`/`INSERT`/`UPDATE` touching the column, plus a check for services that read the database directly and wouldn't show up in this repo's ORM usage — a BI tool, an analytics pipeline, another microservice with its own connection string.
- **Scheduled/batch jobs with irregular cadence**: the evidence window must cover at least one full cycle. A week of clean logs proves nothing about a monthly job; a monthly job needs a month of "not invoked," a quarterly one needs a quarter. Check the scheduler config itself (cron entry, k8s CronJob, Airflow DAG) for the actual cadence before picking a window — don't assume from the code comment, which is often stale.
- **Exported package functions / published APIs**: repo-internal grep can't see other repos that import the package. Check package-registry download/version-adoption stats if the package is published, or search across other repos you have access to for the import — and if neither is possible, say plainly that reachability outside this org's visible code can't be ruled out, rather than implying it was checked.

## Step 3 — when the evidence isn't there yet, instrument instead of guessing

If no existing log/metric answers step 2 cleanly, don't extrapolate from what's available — add a cheap tombstone: a log line or counter increment at the call site ("this route/column/job was hit"), ship it, and let it soak for the same window step 2 calls for before touching deletion. A few weeks of real silence from an instrumented tombstone is worth more than any amount of confident reasoning about what "probably" still calls something.

## Step 4 — delete reversibly, and keep the evidence

Even with evidence in hand, match the rollback cost to the blast radius: a high-traffic-adjacent endpoint is safer retired in two steps (return `410 Gone` for one deploy cycle before removing the handler entirely) than hard-deleted in one commit; a low-risk internal table can usually go straight to a normal, easily-revertible delete. Either way, put the evidence in the PR/commit description — the log query used, the window covered, the counter's final value — so the person who gets paged when it turns out someone still hit it can see exactly what was checked and when, instead of re-deriving it from scratch under pressure.

## Report

State the evidence and its limits, not just a verdict:

```
POST /v1/legacy-export
  reachability: external (public API)
  evidence: ALB access logs, path=/v1/legacy-export, 90-day window: 0 hits
  caller check: no User-Agent pattern found in the (empty) hit set
  verdict: safe to retire — 410 Gone for one deploy, then delete handler

orders.legacy_discount_code (column)
  reachability: external (BI tool has direct DB access, outside this repo)
  evidence: pg_stat_statements, 30-day window: 0 reads/writes from app;
    BI team confirmed (Slack, 2026-07-28) their dashboards don't reference it
  verdict: safe to drop after one release with the column nullable+unused

reconcile_quarterly() cron job
  reachability: external (quarterly batch, k8s CronJob schedule: 0 3 1 */3 *)
  evidence: only 6 weeks of tombstone-counter data collected so far
  verdict: NOT YET PROVEN — needs a full quarter before deletion; re-check 2026-10-01
```

## Boundaries

- This is not a static dead-code tool and doesn't replace one — run knip/ts-prune/vulture/grep first for the "does anything in this repo reference it" pass; this skill starts where that pass leaves off, at surfaces reachable from *outside* the repo.
- Feature-flag cleanup (a flag that's fully rolled out, removing both the on and off branches) is a different problem with its own tooling and workflow — out of scope here, don't fold it in.
- Don't demand log analysis or a soak period for code that's provably intra-repo-only — that just slows down a deletion static analysis already proved safe.
- A finite evidence window is proof of "not observed," not proof of "cannot happen" — say what confidence the window actually bought (covers the known cadence vs. still short of it) rather than declaring something definitely safe when the window hasn't covered a full cycle yet.
