---
name: residency-guard
description: Audits whether a system that has committed to a data-residency boundary (data must stay in the EU, in-country, out of a specific region) actually enforces it at every *runtime* path — not just wherever the primary database happens to live. Covers cross-region failover/DR targets, CDN/edge caching, cross-region read replicas added later for latency, queue/consumer region pinning, and third-party SDKs (analytics, error tracking, support chat) whose own infrastructure crosses the boundary regardless of where your servers run. Use when asked "is our data actually staying in the EU", "does failover break our residency promise", "audit data residency enforcement", when building or reviewing multi-region infrastructure under a residency requirement, or after a customer/compliance question like "can you prove this never left region X".
---

# residency-guard

A data-residency commitment usually gets enforced exactly once, in exactly one place: the primary database is provisioned in the right region, someone checks that box, and the commitment is considered handled. Everything added afterward — a DR failover target picked for uptime rather than jurisdiction, a CDN whose edge nodes cache and log requests anywhere in the world, a read replica added eighteen months later purely for latency, a background consumer running in a shared multi-region deployment, an analytics or support-chat SDK that ships data straight to its vendor's own global infrastructure — inherits none of that review. The primary DB stays compliant while the actual data footprint quietly grows past the boundary. This is not hypothetical: Austria's data protection authority ruled in January 2022 (on a complaint by noyb.eu) that a site's use of Google Analytics violated GDPR, because visitor data — IP address, unique identifiers — ended up on Google's US infrastructure regardless of the site operator's own EU hosting and privacy policy; French and Italian regulators reached the same conclusion independently the same year. In every case the operator's own servers were exactly where they claimed; the gap was in infrastructure and vendors nobody re-audited after the initial residency decision.

## Step 1: enumerate every path data can cross the committed boundary — not just the primary write path

Start from the commitment itself (which region(s)/jurisdiction the data must stay in) and list every surface that touches the data, not just where it's first written:

- **Failover/DR target.** Is the standby region chosen for the promoted replica or backup restore actually inside the committed boundary, or was it picked purely for uptime/cost? A residency-correct primary with an out-of-boundary DR target is not compliant during an incident — that's exactly when it needs to hold.
- **CDN/edge caching.** Does the CDN restrict which edge locations can serve or cache this traffic, or does it cache and log requests — including anything sensitive riding in the URL, headers, or a cached API response body — at edge nodes anywhere in the world by default? Most CDNs are global-by-default and require an explicit region restriction.
- **Cross-region read replicas.** Was a replica added later for read-scaling or latency by someone who didn't know about the residency commitment, or without re-checking it? Grep for every replica/reader connection string and confirm its region, not just the writer's.
- **Queue/consumer region pinning.** In a shared multi-region deployment, does a worker or consumer group in the wrong region ever pick up a message containing regulated data — materializing it in that region's process memory, logs, and local cache even briefly?
- **Third-party SDKs and vendors.** Does an analytics, error-tracking, support-chat, or email/SMS SDK send data to that vendor's own infrastructure regardless of where your servers run? This is the exact Google Analytics shape — the vendor's SDK, not your own code, is what crosses the boundary.
- **Backups/snapshots and the logging/observability pipeline.** Are cross-region backup copies made for DR without residency being part of that backup policy? Do logs — which often embed request bodies, user IDs, or full payloads — ship to a centralized, single-region logging backend that sits outside the commitment made for the primary data?

## Step 2: check whether each surface is enforced by configuration, or just by convention

For every surface found in Step 1, ask whether staying in-boundary is guaranteed by infrastructure config — an IAM/bucket policy condition, a VPC/networking constraint, a CDN region-restriction setting, a database parameter group tied to one region — or whether it's simply true today because "our servers happen to be in eu-west-1" and would silently break the moment someone adds a replica, a new CDN pop, or a new vendor integration without re-checking. Convention-enforced residency is a standing risk, not a passed check, even when it currently holds.

## Step 3: verify write, read, and failover paths separately

Residency review tends to happen once, against the write path, and then never again. Explicitly re-check:

- The **read path**: does any query load-balancer, read-replica router, or "nearest region" optimization ever route a read to an out-of-boundary node?
- The **failover path**: when the primary is unreachable, does the promoted node/region satisfy the same commitment, or does DR quietly trade residency for availability?
- **Async/background paths**: do scheduled jobs, event consumers, or replayed webhooks run in whichever region happens to have capacity, independent of which region the data they're processing is committed to?

## Step 4: verify with evidence, not architecture diagrams

A privacy policy or an architecture diagram claiming "EU-only" is an assertion, not a fact about the running system. Where the codebase and access allow it, trace an actual outbound destination: a CDN access log's edge-location field, a DB connection string's region, a network capture of what a third-party SDK actually sends and where. The Google Analytics case is exactly a failure of this step — the operator's own documentation said EU-only, and nobody had traced what the vendor's SDK actually did once loaded. Where a third-party vendor's own regional processing can't be confirmed from the codebase, say so plainly rather than inferring compliance from the vendor's marketing claims.

## Report

BLOCK: a runtime path (failover target, CDN edge, replica routing, third-party SDK, log pipeline) can be shown to send or store regulated data outside the committed boundary today — not latent risk, an active gap. CAUTION: the boundary currently holds but only by convention (no config-level guarantee), so a routine infra or vendor change would silently break it with nobody noticing. SAFE: verified via evidence — infra config or a traced network destination — that the path stays inside the boundary. Lead with any BLOCK on the failover/DR path specifically: it's the surface most likely to have been reviewed once, at design time, and never re-checked against what actually gets promoted during a real incident.

## Boundaries

- Not `gdpr-audit`'s territory — that class of skill covers the *initial* decision of where data is collected, the legal basis for any cross-border transfer, and consent/DPA mechanics. This skill assumes a residency commitment already exists and audits whether the *running system's* infrastructure honors it end-to-end, especially the parts nobody re-checks after the primary database is pinned correctly.
- Not a multi-region architecture design skill — doesn't help decide active-active vs. active-passive or which regions to deploy to; only whether the region choices already made actually satisfy an existing residency promise.
- Doesn't substitute for legal/compliance sign-off on whether a given architecture legally satisfies a specific regulation (GDPR, PIPL, sector-specific data-localization law) — flags where enforcement is missing, unverified, or convention-only; whether that's sufficient under a particular law is a legal question this skill doesn't answer.
- Can't verify a third-party vendor's actual infrastructure from the outside — where the codebase only shows a call into vendor X's SDK, say plainly that confirming vendor X's own regional processing needs that vendor's compliance documentation or a network trace, not code inspection alone.
