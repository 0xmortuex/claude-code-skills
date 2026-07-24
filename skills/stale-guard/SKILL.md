---
name: stale-guard
description: Review caches and derived data for CORRECTNESS — completeness of invalidation, key scoping, and drift between a source of truth and its copies (Redis/memcached entries, memoization, denormalized columns, materialized views, search indexes, CDN caches). Use when the user reports staleness symptoms ("users see old data", "it shows the wrong user's data", "search doesn't match the database", "works after a refresh/logout"), adds or modifies caching, or asks "is this caching correct". Performance skills add caches; this one proves the existing ones can't serve wrong data.
---

# stale-guard

Every cache is a bet that a copy will be kept consistent with its source by *discipline* — there's no referential integrity for Redis. The bet is lost quietly: a new write path skips the invalidation the original author wired up, a key forgets one dimension, and now users see stale data — or worse, *each other's* data. These bugs feel "random" (they depend on cache state) and get closed as unreproducible. The review is systematic instead: enumerate the copies, then prove two invariants for each.

## Step 1: enumerate every copy of the truth

More than the obvious Redis calls: in-process memoization and `@lru_cache`, HTTP/CDN caching headers, denormalized columns (`post.comment_count`), materialized views, search indexes (Elastic mirroring the DB), precomputed aggregates, edge/session caches, client-side stores fed by the API. For each: what is the **source of truth**, and what is the copy's **staleness budget** — the maximum age at which serving it is still *correct* (not just tolerable)? "Whatever the TTL happens to be" is not a budget, it's an accident.

## Step 2: invariant A — every write path invalidates

This is where caching correctness actually dies. For each copy, list **every** write path that mutates its source — not just the service's main update endpoint: admin panels, bulk imports, migrations and backfills, *other services* writing the same table, DB triggers, manual ops SQL. Then check each one updates or invalidates the copy.

- The classic failure is temporal: invalidation was complete when the cache was added, then a new write path landed six months later. Grep for writes to the source (ORM model saves, table name in SQL) and cross-reference against invalidation call sites — the asymmetry is the bug list.
- Write paths that *can't* invalidate (another team's service, raw SQL ops) mean the design is wrong for event-driven invalidation: the honest options are a TTL matching the staleness budget, or moving invalidation to where the write actually happens (CDC, triggers, an outbox).
- Check the race, too: read-miss → DB read → *concurrent write+invalidate* → stale value cached after the invalidation. Fixes: short TTL as backstop always, or versioned/check-and-set writes for hot keys. Invalidate-then-write vs write-then-invalidate orderings each fail differently; note which one the code does and what that costs.

## Step 3: invariant B — the key contains every dimension that changes the value

Under-scoped keys are the security-adjacent failure: `cache.get(f"dashboard")` computed per-user serves user A's dashboard to user B. For each cache read, ask: **what inputs does the cached computation actually depend on?** — then verify each is in the key: user/account, tenant/org, locale/language, permissions or role (a cached admin view served to non-admins!), API version, feature-flag state, device type if rendering differs. Any dependency not in the key is either a bug today or a bug the next time that dependency starts varying. HTTP layer: same audit as `Vary` headers and CDN cache keys — `Vary: Cookie`-shaped mistakes cache one user's page for everyone.

Over-scoping is the quieter cousin (per-user keys for global data = hit rate ~0, cache theater) — worth one line, not a BLOCK.

## Step 4: operational failure modes

- **Stampede**: a hot key expires and 500 concurrent requests all recompute against the DB. Look for singleflight/lock-and-wait, TTL jitter, or serve-stale-while-revalidate on anything hot.
- **Negative caching**: is a transient error (timeout, 5xx from downstream) being cached as "no data" for the full TTL? Errors get no cache, or seconds at most.
- **Cold start**: can the system survive a full flush in prod (deploy of new key schema, Redis restart) without the DB falling over — and is there a safe way to flush *one* entity when support needs it?
- **Serialization skew**: cached objects outlive deploys; a format change means new code reading old entries — version the payload or bump a key prefix on schema change (skew-check covers the general case).

## Report

Per copy: source, staleness budget, invariant A result (write-path table: path → invalidates? ✔/✘), invariant B result (dependency → in key? ✔/✘), operational notes. Severity by consequence: cross-user leakage from an under-scoped key is a BLOCK regardless of likelihood; a dashboard aggregate lagging 10 minutes inside a 15-minute budget is SAFE — say so and move on.

## Boundaries

- Adding caching for performance, sizing, eviction tuning, hit-rate optimization: out of scope — this skill only proves correctness of what exists (flag missing caching only when the *absence* causes incorrectness, e.g. non-idempotent recomputation).
- If invalidation can't be verified statically (another repo owns a write path), say exactly that and name the verification needed — don't stamp invariant A on faith.
- LLM/API response caching has the same key-scoping rules (user context in the key!) — apply step 3 to it like any other cache.
