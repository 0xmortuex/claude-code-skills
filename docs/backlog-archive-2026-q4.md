# Backlog archive — 2026 Q4, part 1 (2026-10-01 to 2026-11-02)

Historical narrative moved out of `BACKLOG.md` on 2026-11-04 to keep that file under the
single-`Read` size limit (it had grown past 256KB). This is a cut-and-paste of the original
sections verbatim — no content rewritten or summarized away, so every "REJECTED"/"SHIPPED"
novelty-research claim here is still `grep`-able. See `../BACKLOG.md` for the current rules,
open items, and most recent dated section, and `backlog-archive-2026-q3.md` for 2026-07-24
through 2026-09-30.

---

## Drift audit — round 7 (2026-10-01): the two post-round-6 skills

This session's `mcp__github` access is scoped to this one repo only (same constraint noted in round
6), so a fresh novelty sweep would again be under-verified against this pack's own bar. Picked the
standing fallback instead: drift-audit the two skills shipped since round 6 (2026-09-28) that had
never had a dedicated fact-verification pass — `resync-guard` (2026-09-29) and `backpressure-guard`
(2026-09-30). Read both `SKILL.md` files in full, identified every externally-checkable claim, and
verified each via WebSearch:

- `resync-guard`: re-verified both Mattermost citations against current issue text. #16505
  ("Information Loss: Messages Missing From Message Stream After Connection Issue On Receiver Side")
  still resolves and matches the skill's description exactly — sender's message never reached the
  receiver after a connection blip, not on reconnect, not after switching channels, sender given no
  indication. #30388 (`WebSocketClient requires missedMessageListener for proper reconnection but
  lacks documentation/fallback`) still resolves and matches — the sequence counter is only reset if a
  `missedMessageListener`/`missedEventCallback` is registered, undocumented, causing silent failure
  (search results describe an infinite-reconnect-loop consequence rather than the skill's "silent
  gap" framing, but both stem from the same documented root cause: the opt-in, undocumented hook).
  Also re-verified the two protocol-level framing facts: RFC 6455 WebSocket has no session-resumption
  concept and no equivalent to SSE's `Last-Event-ID` (confirmed — "WebSocket has no equivalent to
  Server-Sent Events' Last-Event-ID for reconnecting... the browser WebSocket API has no built-in
  reconnect, retry, or message replay mechanism"), and the WHATWG HTML living standard's Server-Sent
  Events section confirms `EventSource` automatically tracks and resends `Last-Event-ID` on
  reconnect. No drift.
- `backpressure-guard`: re-verified both grounding citations. `actix/actix-web` issue #1967 still
  resolves and matches the skill's quote ("accepts bytes without bound, such that it will consume
  infinite memory if the rate of bytes in exceeds the rate of bytes out") verbatim. `socketio/socket.io`
  issue #4984 still resolves and matches the mechanism described (`socket.acks` entries orphaned when
  a `broadcastWithAck`/`emitWithAck` timeout fires before the client responds, 500-client/50-room
  reproduction climbing to ~1.5GB over 3 hours) — confirmed fixed by PRs #5452/#5461 ("clean up
  socket.acks on broadcastWithAck timeout"). Specifically re-checked the skill's most falsifiable
  claim — that the fix "shipped in socket.io@4.8.4" — against the actual `socket.io@4.8.4` GitHub
  release notes: confirmed, the release's bug-fix list includes "cleanup pending acks on timeout to
  prevent memory leak," published 2026-09-25, five days before the skill shipped. No drift.

No fixes needed in either skill — both externally-checkable citation sets hold up against current
source text. `python tools/validate.py` still passes (`OK: 32 skills valid and consistent with
README.`) — no skill files changed this run.

Follow-up for the next run: all 32 skills now have at least one dedicated fact-verification pass
since their most recent content change (round 3: the original 18; round 4: next 5; round 5: next 2;
round 6: next 5; this round: the final 2). The next drift-audit pass is only worth running once a
specific cited tool/API/platform doc is known to have changed, or once new skills ship that haven't
been checked yet — there's no fixed schedule. If a future session has real cross-repo GitHub code
search (`mcp__github__search_code` without a repo restriction), the fastest way to find fresh novelty
work is still: `grep -n -i "REJECTED\|already mined\|saturated" BACKLOG.md` first, then try the one
still-open, unresearched angle noted above (WebSocket/SSE connection-storm / reconnect-capacity —
LB accept-queue tuning, jittered reconnect after a mass deploy) before any other fresh sweep.

## `storm-guard` — SHIPPED (2026-10-02, verified novel)

This session's GitHub access (`mcp__github` tools) was scoped to this one repo only, same constraint
noted in rounds 6–7, so cross-repo code search wasn't available. Per the round-7 note, researched the
one still-open, unresearched angle it flagged directly: WebSocket/SSE connection-storm /
reconnect-capacity — does a mass-reconnect event (deploy, LB-enforced connection lifetime, dependency
blip) overwhelm the backend, as distinct from `resync-guard` (data resync correctness) and
`backpressure-guard` (ongoing health of an already-connected client), both of which explicitly carve
this out — `backpressure-guard`'s own Boundaries section says outright: "Not a capacity-planning or
connection-storm review... reconnect-storm mitigation after a deploy (jittered backoff,
load-balancer accept-queue tuning)."

- [x] **Reconnect-storm / mass-reconnect-capacity audit — SHIPPED as `storm-guard` (verified
  novel).** The candidate: does a fleet of real-time clients and the backend they reconnect to
  survive everyone reconnecting at once — synchronized (non-jittered) client backoff, and
  auth/session/DB work with no cache or rate limit protecting it at fleet scale. Verified uncovered
  with `WebSearch` (no `filename:SKILL.md` GitHub code search available this session, so used
  `site:github.com "SKILL.md"` query variants plus direct searches for "reconnect storm" and
  "connection storm" alongside "audit"/"review"): every hit was either general engineering
  advice/blog content about jittered backoff (not a skill), or a **build**-oriented skill — most
  notably `poorvith-mp/skills-developer` → `realtime-systems` ("Build WebSocket, SSE and pub/sub
  features: presence, fan-out, reconnection and backpressure"), fetched and read in full: it mandates
  jittered backoff as a scaffolding requirement and has one checklist line ("Client reconnection
  implements exponential backoff with randomized jitter") but, confirmed by direct read, has no audit
  procedure for load-balancer capacity planning, mass-reconnection stress-testing, or backend
  shielding at fleet scale — a spec for building a new system, not a code-level review of an existing
  one with file:line findings and a verdict, the shape every skill in this pack follows. Also
  in-pack-confirmed distinct from `job-warden` (cron thundering herd is about jobs sharing a *schedule
  trigger*, not clients reconnecting to a live service) and `stale-guard` (cache-stampede on one hot
  key under concurrent request load is a different mechanism than many independent connections
  arriving at once).
  Grounded in two real incidents, both corroborated across multiple independent secondary sources
  since direct access to the primary blogs (`discord.com`, `slack.engineering`) was egress-blocked in
  this session's network — confirmed via `curl` returning a 403 from the proxy, not just a WebFetch
  domain restriction, so cited only with that caveat stated plainly: Discord's own engineering
  postmortem "You've Got (Too Much) Mail: Behind the Scenes of the 3/25/26 Voice Outage" (a
  Kubernetes config change killed 17% of session servers, the survivors' millions of clients
  reconnected at once, and the thundering herd overwhelmed a single Erlang supervisor's mailbox —
  described consistently across five independent secondary write-ups: joshuabellew.com,
  statusfield.com, dev.to, printenqrcode.com, evrimagaci.org); and Slack's Flannel edge-cache service,
  built specifically so 100K simultaneous reconnects after a Gateway Server death hit an edge cache
  instead of the backend databases directly (described consistently across snowan.gitbook.io,
  systemdesign.one, an InfoQ conference talk, and others). Also grounded in a verified platform fact:
  GCP's global external Application Load Balancer force-closes every WebSocket connection at a hard,
  non-configurable 24-hour mark regardless of activity — meaning connections opened during one deploy
  window get disconnected together, a full day later, whether or not anyone remembers the
  correlation (confirmed via GCP's own documented behavior, cited by oneuptime.com and a
  Medium/GCP-timeout writeup). One candidate secondary-source cluster was checked and discarded per
  this pack's own established caution (see the `backpressure-guard` entry's process note on
  AI-audit-bot-filed issues): a WebSearch hit citing "5,312 of 7,312 ticket requests refused, latency
  26s" at 1000 simulated sockets came from `NC1107/slim-m`, a zero-star/zero-fork solo project with no
  independent validation — not used as grounding, in favor of the two verified, well-known incidents
  above. Added `skills/storm-guard/SKILL.md` (steps: find the reconnect trigger and whether
  disconnects are already synchronized by a deploy pattern or LB connection-lifetime limit; check
  whether the reconnect delay is genuinely randomized per-client or just a fixed/deterministic delay
  that still re-synchronizes the fleet; check what one reconnect costs the backend — DB/auth/hydration
  calls — and whether anything shields it at fleet scale; check whether a mass-reconnect has ever
  actually been load-tested or is purely assumed-safe because "the code has backoff"),
  `examples/storm-guard.md` (a pre-deploy review of a 50k-client realtime service with a fixed
  3-second unjittered reconnect delay and three unshielded per-connection backend calls, walked
  through all four steps to a BLOCK verdict citing both grounding incidents and recommending jitter
  plus backend shielding or a staged pod-cycling rollout), README skills-table row + decision-table
  row + intro paragraph (thirty-two → thirty-three, rejected/covered-candidates sentence extended) +
  Examples section + install-tip count, `examples/README.md` link. `python tools/validate.py` passes
  (`OK: 33 skills valid and consistent with README.`).

Follow-up for the next run: no candidates parked from this thread. This session's `mcp__github`
access stayed scoped to this one repo (same as rounds 6–7) and `discord.com`/`slack.engineering` were
both egress-blocked for direct primary-source verification (confirmed via a 403 from the network
proxy itself, not just a WebFetch domain restriction) — if a future session has either broader GitHub
code search or unblocked egress to those two domains, it's worth directly re-confirming the two
citations above against their primary text rather than relying on secondary-source corroboration
indefinitely, though nothing here is flagged as questionable, just unverified against the primary.
Real-time/streaming now has three skills (`resync-guard`, `backpressure-guard`, `storm-guard`)
covering, respectively: data-loss-on-reconnect, ongoing per-connection health while connected, and
backend survival of the mass-arrival event itself — these three boundaries were cross-checked against
each other this round and don't overlap. No further angle in this specific domain was identified as
worth researching next; a fresh novelty sweep should look elsewhere, or (if GitHub code search stays
repo-scoped) default to drift-auditing `storm-guard` itself once it's no longer brand-new.

## Skill improvement (2026-10-03): closed a real cross-file gap in `security-sweep`

This session's `mcp__github` access was again scoped to this one repo only, so ran a fresh novelty
sweep via `WebSearch` instead (same constraint as rounds 6–8). Five candidate categories were
researched and all died — logging below so the next run doesn't re-walk them from zero — then,
rather than force a sixth, read the pack's own cross-references for a gap already flagged in-pack
but never closed, which turned up a real one.

- [x] **New-skill candidates researched and rejected, don't re-research without a new angle:**
  (a) trace/correlation-ID propagation across async/queue boundaries — covered by
  `aj-geddes/useful-ai-prompts`' `correlation-tracing` (mirrored across claudskills,
  claudemarketplaces, crossaitools — the same source behind the already-dead `clean-exit` and
  "worker startup/readiness" candidates) plus `majiayu000/claude-skill-registry`'s
  `jaeger-tracing-specialist`; (b) HTTP-level lost-update / concurrent-edit-overwrite (PATCH/PUT
  with no version/ETag check letting a second writer silently clobber a first) — not confirmed dead
  as cleanly as the others (search surfaced unrelated "skill-update concurrency" tooling, not an
  app-review skill), but this is the same shape as this pack's own already-rejected "offline-sync
  conflict resolution" candidate (see the intro paragraph's dropped-candidates list) and overlaps
  `ln 628 concurrency auditor`'s broader scope (claudemarketplaces.com/levnikolaevich) — too close to
  a documented duplicate to ship without a sharper differentiator than what today's search budget
  found; worth one more targeted look (specifically: does any existing skill check for a *missing
  version/If-Match check on a REST write endpoint*, as opposed to general thread/async concurrency or
  offline-sync merge logic) before ruling it out for good; (c) file-upload security (MIME
  sniffing/zip bombs/zip slip) — covered in depth by `florianbuetow/claude-code`'s `file-upload` skill
  and the `endurain-project` `safeuploads` reference; (d) CSV/Excel formula injection as a
  **standalone** skill — covered by this pack's own existing cross-references (see below) once
  `security-sweep` actually names it, so a separate skill would be an internal duplicate.
- [x] **Fixed: `security-sweep` never actually named CSV/spreadsheet formula injection, despite two
  other skills in the pack pointing callers to it for exactly that.** Found while chasing candidate
  (d) above: `export-guard`'s Boundaries section says "Doesn't cover CSV formula injection... that's
  a security finding, also `security-sweep`'s territory" and `import-guard`'s says the same for
  malicious file content — but `security-sweep`'s own "What to actually look for" checklist never
  named the category; it would only be caught if the reviewer happened to generalize from "Injection"
  (scoped to SQL/NoSQL/shell/eval/template) or "Injection into the browser" (XSS), neither of which
  is about a spreadsheet application's own formula-execution-on-open behavior. Verified current and
  real, not just textbook: OWASP's CSV Injection page and CWE-1236 (dangerous leading characters `=
  + - @`, tab, CR — confirmed the single-quote-prefix mitigation is the current recommendation and
  that a once-suggested tab-prefix workaround is now itself on the dangerous-character list) plus a
  live, dated 2026 CVE (CVE-2026-45263, FacturaScripts' `CSVExport.php::writeData()` concatenating a
  user-controlled field with no leading-character check, CVSS 8.0, PoC confirmed via a crafted
  customer name field reaching an admin's CSV export) as a real-world instance of precisely the gap
  this checklist bullet now names. Added one bullet to `skills/security-sweep/SKILL.md`'s risk-category
  list (with the OWASP/CWE/CVE grounding and the single-quote-prefix fix, noting CSV quoting alone
  doesn't stop it) and extended the "match the categories to what the code does" line to mention
  export/report code. `python tools/validate.py` passes (`OK: 33 skills valid and consistent with
  README.`) — no README/example changes needed since this is a checklist addition inside an existing
  skill's body, not a new skill or a changed trigger surface.

Follow-up for the next run: the lost-update/concurrent-edit-overwrite candidate (b above) is the one
genuinely unresolved thread — worth a sharper, narrower search (missing version/If-Match checks on
REST write endpoints specifically) rather than the broad terms tried this round before closing it
for good one way or the other.

## Skill improvement (2026-10-04): ran the deliberate "Boundaries cross-reference" pass, found and fixed one real gap

Before picking a task today, found the git state broken: `HEAD` was detached 3 commits ahead of both
local and remote `main` (the 2026-10-01/02/03 daily runs had committed but never actually landed on
`main` or pushed — likely a bug in an earlier run's own final step). Fixed first by fast-forwarding
`main` to `HEAD` and confirming `origin/main` matched (`storm-guard` and the 2026-10-03
`security-sweep` CSV-injection fix are now actually on `main`, not just sitting in a detached state).

Then did the "quick deliberate pass" the round-9 note above asked for: extracted every skill's
`## Boundaries` section (`awk` across all 33 `SKILL.md` files) and read every cross-reference of the
shape "Not `X`'s territory" / "that's `X`'s territory" / "see X", then checked whether the named
target skill's own body actually covers the thing being pointed at. Most held up (e.g. `export-guard`
→ `security-sweep` for export authz/PII-exposure is covered by security-sweep's existing "Broken
authorization" and "Sensitive-data exposure" bullets). One didn't:

- [x] **Found and fixed: `import-guard`'s Boundaries section points to `security-sweep` for
  "zip bombs, decompression attacks" on a file-upload attack surface, but `security-sweep`'s own
  checklist never named that category** (confirmed by grep — zero other mentions of
  "zip bomb"/"decompression"/"zip slip" anywhere in `skills/`) — the same shape of gap as the
  2026-10-03 CSV-injection fix, found by the same "boundary-points-elsewhere" check that fix's own
  follow-up note asked for. Verified current and real via `WebSearch`, not just CWE-409's textbook
  definition: three corroborating 2026 CVEs on an authenticated file-upload path extracting an
  attacker-supplied archive with no decompressed-size/entry-count cap — CVE-2026-3114 (Mattermost,
  disclosed 2026-03-26 under advisory MMSA-2026-00598, cross-confirmed on Red Hat's and Debian's own
  CVE trackers, not just an aggregator) and CVE-2026-61455 (Grav CMS, `ZipArchiver::extract()` with no
  limit on uncompressed size/file count/nesting depth) — plus CVE-2026-59274 (Spring Integration's
  `UnZipTransformer`) as a third independent instance, checked but not cited in the skill to keep the
  grounding tight. Added one bullet ("Decompression / zip bombs") to
  `skills/security-sweep/SKILL.md`'s risk-category checklist, citing CWE-409/CWE-770 and the two
  verified CVEs, with the trace question (does the extraction path cap decompressed size/entry count
  *during* extraction, not just validate the archive's own compressed metadata) and the fix (an
  incrementally-checked ceiling, not a trust-the-declared-size check). Also extended the
  "match the categories to what the code does" line to mention archive-extraction scrutiny for
  file-upload code. `python tools/validate.py` passes (`OK: 33 skills valid and consistent with
  README.`) — no README/example changes needed, same shape as the 2026-10-03 fix (a checklist
  addition inside an existing skill's body, not a new skill or a changed trigger surface).

Follow-up for the next run: the lost-update/concurrent-edit-overwrite candidate (b, logged
2026-10-03 above) is still the one genuinely unresolved new-skill thread. The "boundary cross-reference"
pass done today checked every skill's Boundaries section once; it's a cheap check worth repeating
whenever a new skill ships (a new skill's Boundaries section might claim territory an existing skill
doesn't actually cover, or an existing skill might gain a Boundaries claim about the new one that
isn't yet true) rather than assuming today's pass caught everything for all future skills. Also worth
a one-time git-hygiene check at the start of a future run: confirm `git branch --show-current` is
`main` and `git status` doesn't say "detached" before trusting `git log` — this run found 3 days of
undetected unpushed work purely by running `git branch -a` out of caution, and the daily-agent
instructions don't currently say to check for that explicitly.

## Git-hygiene check (2026-10-05) + `overwrite-guard` — SHIPPED (verified novel)

Start-of-run check per the 2026-10-04 note: `git status` showed `HEAD` detached again, 4 commits
ahead of the local `main` branch pointer (storm-guard + both 2026-10-03/04 `security-sweep` fixes).
`git fetch origin main` showed `origin/main` was already at that same commit — the detached `HEAD`
and stale local `main` were a local-ref staleness artifact, not actually unpushed work this time (the
2026-10-04 run's push did land). Fixed by fast-forwarding local `main` to `HEAD`
(`git checkout main && git merge --ff-only`); `git push` correctly reported "Everything up-to-date."
Worth keeping this check at the start of every run regardless — it's cheap and the failure mode
(detached HEAD silently diverging from `main`) has now shown up twice.

Picked up the one open thread from the 2026-10-03/04 notes: does any existing skill audit whether a
PATCH/PUT/"save" endpoint on a shared record actually prevents a *lost update* — two concurrent
writers silently clobbering each other because there's no version/revision/`If-Match` check, or one
that exists but never actually fires. Ran several rounds of `WebSearch` with varied terms
(`"SKILL.md"` + `optimistic concurrency`/`If-Match`/`ETag`/`last write wins`/`blind write`/`lost
update`/`version column`, combined with `audit`/`review`/`PATCH`/`PUT`). Consistently found only two
kinds of near-misses, read rather than assumed from a snippet: (1) broad code-review checklists
(`addyosmani/agent-skills`, `wshobson/agents`, `garrytan/gstack`) that list "race conditions" or
"state inconsistencies" as one generic bullet among dozens, with no dedicated mechanic for *this*
bug; (2) in-process concurrency skills (`martinholovsky/SOTA-skills` → `async-concurrency`) scoped to
threads/goroutines/channels/deadlocks — a genuinely different failure mode (shared memory inside one
process) from two independent HTTP requests racing on the same stored row. Confirmed this candidate
is distinct from this pack's own already-rejected "offline-sync / conflict-resolution" candidate
(logged above): that one is about a client offline for hours/days needing real merge/CRDT logic
against a mutation queue; this one is about an ordinary synchronous web/API save racing by seconds,
which doesn't need (and would be the wrong framing for) merge logic — just a correctly-enforced
version check.

- [x] **`overwrite-guard` — SHIPPED (verified novel).** Audits whether two editors of the same record
  (two people, two tabs, a person and a background job) can silently clobber each other on a
  PATCH/PUT/ORM-`save()` read-modify-write path. Grounded in two real, filed bugs rather than a
  hypothetical, each illustrating one of the skill's two failure categories: `spidermila/MedCover`
  issue #461 (fetched and read in full) — eight SQLAlchemy models declare a `version` column
  documented for optimistic locking, but it's never registered as the ORM's `version_id_col`, so the
  `UPDATE` never gets a `WHERE version = :old_version` predicate; the column increments on every
  write and enforces nothing, so a second concurrent edit silently overwrites the first with no
  `StaleDataError`/`409` anywhere — "declared but never enforced." `CoderLambert/react-learning-playground`
  issue #133 (fetched and read in full) — the subtler opposite trap: a revision check exists and
  looks correct, but the editor's local draft is initialized once while the component later re-renders
  with a refreshed `question` prop; the submit path builds `expectedRevision` from the *refreshed*
  prop instead of the draft's actual base, so the compare-and-swap always matches current storage and
  the stale draft overwrites newer data despite the optimistic-concurrency mechanism being present —
  "enforced against the wrong baseline." Added `skills/overwrite-guard/SKILL.md` (four steps: find
  read-modify-write paths on shared records; check whether a version/revision mechanism is actually
  wired into the write, not just declared; if one exists, trace its baseline on both the server and
  client side rather than trusting its presence; check whether a detected conflict is actually
  rejected and surfaced or caught-and-overwritten-anyway), `examples/overwrite-guard.md` (a customer
  profile PATCH endpoint with exactly the MedCover-shaped bug — a `version` column that increments
  but is never read back or added to the `WHERE` clause — walked through all four steps, including a
  clean N/A on step 3 rather than padding it, to a BLOCK verdict), README skills-table row +
  decision-table row + intro paragraph (thirty-three → thirty-four) + Examples section + install-tip
  count, `examples/README.md` link. `python tools/validate.py` passes (`OK: 34 skills valid and
  consistent with README.`).

Follow-up for the next run: no candidates parked from this thread. Per the 2026-08-23/26 notes the
backend/infra novelty space was already assessed as largely saturated before this run found one more
(`overwrite-guard`) — the next run should either run a fresh, differently-angled novelty sweep, repeat
the boundary-cross-reference check now that a 34th skill exists, or continue drift-auditing existing
skills' external citations as their sources age. Also worth it: `overwrite-guard` is brand new and
hasn't had a dedicated fact-verification pass yet (it's grounded in the two GitHub issues cited above,
not a versioned tool/API doc, so there's less drift surface than most skills, but it's still
unverified-since-shipping by the pack's own convention).

## Maintenance pass (2026-10-06): all checks clean, one new-skill candidate researched and rejected

Git hygiene check first (per the 2026-10-04/05 notes): `git status` clean, `main` matched
`origin/main`, no detached-HEAD drift this time. Then worked the three items the 2026-10-05 note
left open, in order, plus a fresh novelty candidate — all came back clean, so nothing needed fixing
and no skill file changed.

- [x] **Boundary cross-reference pass, repeated for all 34 skills.** Extracted every skill's
  `## Boundaries` section and checked each "not X's territory" / "that's X's territory" claim against
  the named skill's actual body (the same mechanical check that found the CSV-injection and zip-bomb
  gaps in `security-sweep` on 2026-10-03/04). Read all 34 sections in full this round. Every
  cross-reference held up — most notably re-verified `trail-guard`'s claim that secrets/PII leaking
  into logs is `secret-spill`'s and `security-sweep`'s territory: `security-sweep`'s checklist already
  names both ("secrets logged or returned in responses" under Secrets, "PII in logs" under
  Sensitive-data exposure). No new gap found; the two fixes made in the 2026-10-03/04 passes appear to
  have closed the only real gaps that existed.
- [x] **`overwrite-guard` fact-verification pass (the explicit follow-up from 2026-10-05).** Fetched
  both grounding GitHub issues in full rather than trusting the skill's own summary:
  `spidermila/MedCover` #461 confirmed exactly as cited (eight SQLAlchemy models with a documented
  `version` column never registered as `version_id_col`, so no `WHERE version = :old_version`
  predicate is ever added — "dead metadata"); `CoderLambert/react-learning-playground` #133 confirmed
  exactly as cited (a draft editor sends `expectedRevision: question.revision` from a prop that
  refreshed after the draft was taken, so the compare-and-swap always matches current storage). No
  drift — both citations are accurate.
- [x] **Re-verified the three CVEs `security-sweep` cited in its 2026-10-03/04 additions** (not yet
  independently re-checked since those fixes landed): CVE-2026-45263 (FacturaScripts
  `CSVExport.php::writeData()`, CVSS 8.0), CVE-2026-3114 (Mattermost zip-bomb memory exhaustion,
  MMSA-2026-00598), and CVE-2026-61455 (Grav CMS `ZipArchiver::extract()`, CVSS 7.1) — all three
  confirmed via independent vulnerability-database sources (Mend.io, Red Hat, Debian's own tracker,
  SecureLayer7, Wiz, OSV) to match the skill's description of the flaw, the affected method, and the
  impact. No drift found.
- [x] **New-skill candidate: `idempotency-key-guard` (server-side `Idempotency-Key` header
  implementation audit) — RESEARCHED, REJECTED as covered.** The angle: does an API's own
  inbound-`Idempotency-Key` handling actually work — hashing/comparing the request body (not just the
  key) so a reused key with a *different* payload doesn't silently return a stale cached response, a
  genuine atomic claim (unique-constraint insert) instead of a check-then-act race between two
  simultaneous identical requests, and a TTL/cleanup story consistent with the documented retry
  window. Confirmed distinct from this pack's own `job-warden` (Q1 is about a job/worker correctly
  *passing* an idempotency key to an outbound call, e.g. Stripe — not about building and auditing a
  server's own inbound key-handling infrastructure) before researching external coverage. Found
  `Intense-Visions/harness-engineering` → `agents/skills/claude-code/api-idempotency-keys/SKILL.md`
  (fetched and read in full, not just a listing) covers all three core mechanisms nearly verbatim:
  explicit "store a hash of the original request body alongside the key and compare on retry" with a
  422 on mismatch, the key-as-distributed-lock/409-on-in-flight race-condition handling, and a
  documented 24-hour TTL with a cleanup job. The one gap it doesn't cover — per-user/per-tenant key
  scoping, so one caller can't guess or collide another's key and read their cached response — is real
  but too thin to carry a standalone skill alone (same shape as several already-rejected candidates in
  this file with a single thin residual gap). The broader space is also well-trodden in blog/article
  form (`dev.to`, `zuplo.com`, multiple "the race condition nobody tests for" posts all converging on
  the same unique-constraint-not-check-then-act fix), reinforcing that this is settled, not novel,
  ground. Closed as covered; do not re-research without a materially different angle than
  harness-engineering's skill.

Follow-ups discovered this run, logged for whoever picks this up next (none investigated further —
flagging, not claiming):
- Drift-audit due: `migration-guard` and `job-warden`'s Postgres/MySQL/k8s/queue-platform specifics
  were last verified in round 2 (2026-08-18), about seven weeks before this note — worth a fresh pass
  against current docs given how much else has shipped since, even though nothing specific is
  currently flagged as wrong.
- New-skill candidate, unresearched: **webhook signature/replay-window verification** — does an
  *inbound* webhook handler verify its HMAC signature with a constant-time compare, reject requests
  outside a timestamp freshness window (replay protection), and avoid a secret-rotation window where
  both old and new secrets are silently accepted with no sunset. Check it isn't already covered by the
  same aggregator packs (`majiayu000/claude-skill-registry`, `hookdeck/webhook-skills`) that saturated
  the 2026-08-23 "webhook/API delivery reliability" sweep before writing anything.
- New-skill candidate, unresearched: **saga/multi-step compensation-completeness audit** — when a
  multi-step workflow fails partway through (charge card, then provision resource, then notify), does
  the code actually roll back/compensate the steps that already succeeded, or leave orphaned side
  effects with no reconciliation. Verify this is distinct from `job-warden`'s poison-message/batch
  questions (which cover one step's retry behavior, not a multi-step workflow's rollback completeness)
  and from `backfill-pilot`'s undo-capture (a single engineer-run script, not a user-facing multi-step
  product flow) before researching external novelty.
`python tools/validate.py` still passes (`OK: 34 skills valid and consistent with README.`) — no
skill files touched this run, so no README/example changes were needed either.

## Maintenance pass (2026-10-07): two open candidates researched and rejected, due drift audit cleared

Git hygiene check first (per the 2026-10-04/05 notes): `git status` showed `HEAD` detached but
pointing at the same commit as local and remote `main` (a local-ref staleness artifact, same
harmless shape as 2026-10-05, not unpushed work) — fast-forwarded local `main` to match. Then worked
the three items the 2026-10-06 note left open, in order. All three came back either rejected or
clean, so no skill file changed — this run's deliverable is the research record below.

- [x] **New-skill candidate: webhook signature/replay-window verification — REJECTED, saturated.**
  The angle: does an *inbound* webhook handler verify its HMAC signature with a constant-time
  compare, reject requests outside a timestamp freshness window, and handle secret rotation without
  a window where neither old nor new secret works. Fetched one dedicated skill in full rather than
  trusting a listing: `Intense-Visions/harness-engineering` →
  `agents/skills/claude-code/api-webhook-security/SKILL.md` covers all three mechanisms essentially
  verbatim — `crypto.timingSafeEqual` for the comparison, a documented ±5-minute (300s) timestamp
  tolerance window matching Stripe's own `stripe.webhooks.constructEvent` behavior, and an explicit
  dual-secret-acceptance rotation procedure (`verifyAnySecret()` trying both old and new secrets
  during the rotation window) with no downtime gap. This is the same `Intense-Visions/harness-engineering`
  pack already cited against the 2026-10-06 `idempotency-key-guard` rejection, now confirmed to cover
  this candidate too. Independently corroborated by four more distinct hits found via `WebSearch`
  (not read in full, but consistent naming/scope across unrelated authors is itself evidence of
  saturation): `jeremylongshore/claude-code-plugins-plus-skills` → `webhook-signature-validator`
  (explicitly flags "replay-window misconfiguration" as a pitfall it checks for), `comeonoliver/SkillsHub`
  → `webhook-security`, `terminalskills/skills` → `webhook-security`, and `hookdeck/webhook-skills`
  → `github-webhooks` (the same aggregator pack that already saturated the 2026-08-23 "webhook/API
  delivery reliability" sweep this item's own wording flagged as a risk to check against). Closed as
  covered; do not re-research without a materially different angle than
  harness-engineering's skill (e.g. a slice specific to a less-common signing scheme, or
  per-tenant/per-caller key-scoping abuse rather than the HMAC+timestamp+rotation mechanics
  themselves).
- [x] **New-skill candidate: saga/multi-step compensation-completeness audit — REJECTED, saturated.**
  The angle: when a multi-step workflow fails partway through, does the code actually
  compensate/roll back the steps that already succeeded, or leave orphaned side effects. Confirmed
  distinct from `job-warden` (single-step retry/idempotency, not multi-step rollback) and
  `backfill-pilot` (an engineer's own script, not a user-facing product flow) before researching
  externally, per the 2026-10-06 note's own framing. Found the category densely covered by multiple
  independent authors: `wshobson/agents` → `saga-orchestration` lists "debugging stuck saga states in
  production where compensation steps never complete" and "test compensation paths explicitly" as
  core use cases/best practices (per its own listed description, not a vague marketplace blurb) —
  that is this candidate's exact audit angle, not just scaffold-a-new-saga; `dykyi-roman/awesome-claude-code`
  → `saga-pattern-knowledge` is explicitly framed as "patterns, antipatterns, and audits"; a `tessl.io`
  registry listing for the same `wshobson/agents` skill separately describes "a troubleshooting
  section that pairs each problem with specific code fixes" — again the audit/debug angle, not pure
  scaffolding. Two further independent hits (`Skillforge` → `saga-pattern-orchestrator` and
  `saga-orchestration-engineer`, from `jamiojala`) reinforce that this is a well-mined niche with
  several authors converging on the same scope. Could not fetch any of these `SKILL.md` files in full
  (several aggregator domains — `tessl.io`, `playbooks.com`, `openskillindex.com`, `grep.app` — are
  blocked by this environment's egress proxy, and guessed raw GitHub paths 404'd without a way to list
  the actual tree), so this rejection rests on multiple independent, consistently-worded secondary
  hits rather than one primary-source read — weaker grounding than the webhook item above. Flagging
  that explicitly: if a future run can reach one of these (e.g. from an environment without the
  egress block, or by finding the exact file path another way) and it turns out *not* to cover the
  audit angle as claimed, this should be reopened rather than treated as permanently settled.
- [x] **Drift audit: `migration-guard` and `job-warden`'s Postgres/k8s claims, due since round 2
  (2026-08-18).** Re-verified the two most load-bearing externally-checkable claims against current
  primary docs. `migration-guard`'s `CREATE INDEX CONCURRENTLY` section: confirmed a failed
  `CONCURRENTLY` build leaves an entry in `pg_index` marked invalid *before* the build starts, which
  `IF NOT EXISTS` on a retry will silently accept as "already exists" rather than rebuilding — the
  exact failure mode the skill already names ("don't assume a failed run left nothing behind"), and
  the documented recovery (`DROP INDEX CONCURRENTLY IF EXISTS` then retry as a separate autocommit
  statement) matches the skill's wording exactly. `job-warden`'s `concurrencyPolicy: Forbid` claim:
  confirmed against the current Kubernetes `batch/v1` CronJob API reference — `Allow`/`Forbid`/`Replace`
  with `Forbid` skipping the next run if the previous one hasn't finished, as the skill states. No
  drift found in either; no skill file changed.

`python tools/validate.py` still passes (`OK: 34 skills valid and consistent with README.`) — no
skill files touched this run, so no README/example changes were needed either.

Follow-up for the next run: the saga-audit rejection above has weaker grounding than this pack's
usual bar (secondary hits only, no primary-source fetch) — worth revisiting if a way around the
egress-blocked aggregator domains turns up. Otherwise the backend/infra novelty space remains
assessed as saturated (per 2026-08-23/26 and 2026-10-06 notes); the next run should either run a
fresh, differently-angled novelty sweep or continue drift-auditing the remaining skills whose
external citations haven't been re-checked since they shipped.

## Drift audit — round 8 (2026-10-08): `storm-guard`, the one skill round 7 didn't reach

`storm-guard` shipped 2026-10-02, after round 7 (2026-10-01, which covered `resync-guard` and
`backpressure-guard`) — it had never had a dedicated fact-verification pass, and the round-7 note
explicitly listed it as the obvious next target. `overwrite-guard` (shipped 2026-10-05) was already
covered by the 2026-10-06 maintenance pass, so this round only needed `storm-guard`. Read the full
`SKILL.md` and identified three externally-checkable claims:

- **Discord's "You've Got (Too Much) Mail" postmortem (March 25, 2026 voice outage) — re-confirmed,
  no drift.** The skill's own text already hedges that primary blog access was unavailable when it
  was written and leans on corroborating secondary write-ups. This round found the primary post
  (`discord.com/blog/behind-the-scenes-of-the-3-25-26-voice-outage`) does exist and is indexed (title,
  authors Bo Ingram and Stephen Birarda, and a summary confirming "a configuration update
  unintentionally shut down a large share of session management servers at once... losing 17% of them
  at once sent a cascade through downstream systems, ultimately overwhelming a service responsible for
  routing voice/video calls" — matching the skill's framing), but `discord.com` itself is
  egress-blocked in this environment, so the specific Erlang-supervisor/mailbox-queue detail still
  can't be confirmed from the primary source today, same as when the skill was written. No change —
  the existing hedge is still the accurate thing to say.
- **Slack's Flannel edge cache — re-confirmed, no drift.** `slack.engineering` is also egress-blocked
  this round, but search results confirm the underlying post exists and describes exactly the
  mechanism the skill cites: mass reconnects (an entire office losing and regaining network at once)
  overloading backend servers, fixed by an edge cache that serves bootstrap/startup data to
  reconnecting clients instead of hitting the core. The skill's specific "100K clients" / "Gateway
  Server" phrasing wasn't independently confirmed in secondary snippets this round (not contradicted
  either — just not covered), consistent with the skill's existing citation confidence. No change.
- **GCP's "24h WebSocket cap" — found and fixed a real overclaim.** The skill stated GCP's global
  external Application Load Balancer enforces "a hard, non-configurable 24 hours" WebSocket lifetime.
  Multiple secondary sources (a GitHub discussion quoting Google's own docs, a third-party GCP
  load-balancing guide) instead describe 86400 seconds (24h) as the *effective maximum you're allowed
  to configure* for the backend service timeout — Google documents it as a value you set, and
  recommends against going higher because GFEs restart periodically for maintenance regardless of the
  configured value. That's a materially different claim than "hard, non-configurable": the timeout is
  a setting, not a fixed wall, even though Google's own maintenance cadence makes ~24h a practical
  ceiling in practice. (Official `cloud.google.com`/`docs.cloud.google.com` pages were egress-blocked
  this round, so this rests on secondary sources quoting the docs rather than a direct primary read —
  flagging that explicitly rather than treating it as fully settled.) Fixed the overclaim in both the
  frontmatter description and the intro paragraph of `skills/storm-guard/SKILL.md` to describe it as a
  configurable backend-service-timeout setting with a documented ~24h recommended ceiling (tied to
  periodic GFE maintenance restarts), rather than an immutable 24h hard cap — the underlying
  mass-disconnect-by-connection-start-time insight the skill builds on is unchanged and still correct
  either way, only the "non-configurable" framing was wrong. `examples/storm-guard.md` doesn't repeat
  this claim, so it needed no change.

`python tools/validate.py` passes (`OK: 34 skills valid and consistent with README.`). One skill file
changed (`skills/storm-guard/SKILL.md`); `overwrite-guard` needed no further action (already verified
2026-10-06).

Follow-up for the next run: all 34 skills now have at least one dedicated fact-verification pass since
their most recent content change. If a future session has unblocked egress to `cloud.google.com`/
`docs.cloud.google.com`, worth a direct primary-source read of the backend-service-timeout docs to
fully settle the GCP claim above rather than relying on secondary quotes. Otherwise, continue either a
fresh differently-angled novelty sweep (per the 2026-08-23/26/2026-10-06 saturation notes) or drift-audit
on a specific-known-change basis rather than a fixed schedule.

## Maintenance pass (2026-10-09): GCP egress re-check (still blocked), two new-skill candidates researched and rejected

Git hygiene check first: `HEAD` was detached at the same commit `origin/main` had just fast-forwarded
to (another local-ref staleness artifact, same harmless shape as prior notes) — fetched and
fast-forwarded local `main` to match, no data at risk.

- Re-tried the round-8 follow-up: direct `WebFetch` of `cloud.google.com/load-balancing/docs/backend-service`
  (redirects to `docs.cloud.google.com/...`) still fails (`ENOTFOUND` — egress to that host remains
  blocked in this environment). A `WebSearch` for the `timeoutSec` range turned up a third-party API
  mirror (flutter-io) stating the allowed range is 1–2,147,483,647 seconds with a 30s default, and an
  unrelated App Engine Flexible doc (1-hour WebSocket timeout, a *different* product from the global
  external ALB this skill's claim is about) — nothing that contradicts or confirms the ~24h
  recommended-ceiling wording `storm-guard` already carries since the 2026-10-08 fix. No change needed;
  still blocked for a true primary-source read.
- [x] **New-skill candidate: agent cost/loop-runaway audit — REJECTED, saturated.** The angle: review
  code that orchestrates LLM/agent calls (agentic loops, tool-calling chains, recursive sub-agent
  spawning) for missing iteration/recursion caps, no per-call or per-session $ budget, unbounded
  retry-around-LLM-call loops, and unbounded sub-agent fan-out. Distinct from this pack's own
  `job-warden` (queue/cron idempotency, not LLM-specific) and from the prompt-injection *security*
  review already rejected on 2026-08-27 (that's abuse-resistance, not cost/runaway control). Found
  multiple independent, directly-on-point hits, fetched (via `raw.githubusercontent.com`, returned as
  model-summarized rather than verbatim content — flagging that fidelity caveat explicitly) rather than
  trusted from a search snippet: `sickn33/agentic-awesome-skills` →
  `skills/runaway-guard/SKILL.md` (named $-cap per call site, concrete iteration-bound constants,
  bounded retries with no retry on 4xx, amplifier anti-patterns like recursion-over-LLM-output and
  webhook-triggers-itself); `wolverin0/claude-skills` → `skills/audit/audit-domain-10-cost/SKILL.md`
  (explicit audit-phase checklist: runaway loops, unbounded LLM/API calls, missing rate limits, infra
  cost amplifiers); `jiayaoqijia/cryptoskill` →
  `skills/payments/0xklen-cap-agent-tool-call-recursion-depth/SKILL.md` (the fan-out/depth slice
  specifically — caps subagent spawn depth and total descendant count); `ericrisco/rsc-harness` →
  `skills/agent-safety/SKILL.md` plus sibling `cost-tracking/SKILL.md` and `llm-pipeline/SKILL.md`
  (tool-call rate cap, session cost cap, loop/step cap, abort-not-just-log budget enforcement).
  Closed as covered; do not re-research without a materially different angle than these (e.g. a slice
  none of them name, such as cross-session budget aggregation across multiple concurrent agent runs).
- [x] **New-skill candidate: GraphQL N+1 / resolver fan-out cost audit — REJECTED, saturated.** The
  angle: review GraphQL resolver code for N+1 patterns an ORM-level checker wouldn't catch, missing
  query depth/complexity limits, and per-item resolver fan-out. Found a direct, dedicated match read
  in full (same fetch-fidelity caveat as above): `majiayu000/claude-skill-registry-data` →
  `data/graphql-reviewer/SKILL.md` — explicitly a *review* skill (triggers on reviewing existing
  schema/resolver code, not scaffolding a new server), checks missing DataLoader batching (rated
  critical), over-fetching, missing depth/complexity limits, unbounded list pagination, and raw error
  leakage, with a file:line severity-rated output format near-identical to this pack's own report
  style. Closed as covered; do not re-research without a different angle.
- Gap acknowledged, not treated as settled: this round's research used GitHub code search only — the
  GitHub MCP tool itself is scoped to `0xmortuex/claude-code-skills` and refused every other repo, so
  all of the above came from `WebFetch` of raw URLs (summarized, not verbatim) rather than the
  `search_code`/`get_file_contents` tools. Marketplace sites (claudskills.com, mcpmarket, lobehub) and
  two repos named in earlier backlog entries (`UnitOneAI/SecuritySkills`,
  `Intense-Visions/harness-engineering`) were not independently re-checked this round — the GitHub
  code-search hit volume (2,000–15,000+ results per query across many independent authors) is
  consistent with genuine saturation rather than one false positive, but flagging the narrower tool
  access so a future run doesn't assume marketplace coverage was re-verified here.

`python tools/validate.py` still passes (`OK: 34 skills valid and consistent with README.`) — no skill
files touched this run (both candidates died), so no README/example changes were needed either.

Follow-up for the next run — three fresh, unresearched candidates, deliberately *outside* the
backend/infra space the 2026-08-23/26 notes called saturated (per their own suggestion to look further
afield before re-sweeping the same territory):
- New-skill candidate, unresearched: **dynamic-UI accessibility regression audit** — SPA route changes
  and async content updates that silently break ARIA live-region announcements, focus management (focus
  lost or stuck after a modal/route change), and keyboard-trap regressions introduced by a component
  rewrite. Check novelty against a11y-specific skill packs before writing anything; this pack has no
  frontend-accessibility coverage at all today.
  **[CORRECTED 2026-10-10: this was not actually unresearched — see the maintenance-pass entry below.
  "Accessibility (WCAG) source-code review audit" was already REJECTED as saturated on 2026-09-03ish
  (search this file for that exact line) and re-confirmed today. Do not re-research without a
  materially narrower angle than plain WCAG/ARIA auditing.]**
- New-skill candidate, unresearched: **offline-first sync conflict-resolution audit** — a mobile/PWA
  app that queues writes made while offline and replays them on reconnect: does the replay actually
  detect and resolve conflicting edits (last-write-wins silently discarding a concurrent edit, vs. a
  documented merge/CRDT strategy), and does a replay failure partway through leave the local queue and
  server state inconsistent. Verify distinct from `job-warden` (server-side queue idempotency, not
  client-side offline-queue replay) and `overwrite-guard` (concurrent-edit detection on a live
  request, not a replayed offline queue) before researching external novelty.
  **[CORRECTED 2026-10-10: this was not actually unresearched either — "Offline-sync / conflict-
  resolution correctness audit" was already REJECTED twice (first pass, then re-confirmed in the
  `push-guard` round) — see the maintenance-pass entry below. Do not re-research without a materially
  different angle than LWW-vs-merge/CRDT failure-mode auditing.]**
- New-skill candidate, unresearched: **i18n pluralization/RTL-layout correctness audit** — string
  concatenation that assumes English word order or a simple singular/plural split (breaks for
  languages with 0/1/few/many/other plural categories, per CLDR), and RTL-layout mirroring gaps
  (icons/chevrons that don't flip, text-direction-dependent CSS that was only tested in LTR). Distinct
  from `clock-sweep` (date/time correctness, not text/layout). Check this isn't already covered by a
  dedicated i18n-review skill before writing anything.
  **[CORRECTED 2026-10-10: also not actually unresearched — "Internationalization/locale correctness
  audit" was already REJECTED as saturated in the same round as the offline-sync rejection above, and
  that round's own citation (`i18n-readiness-review`) explicitly names pluralization *and* RTL as two
  of its eight checked dimensions, so this item is the same rejected category, not a narrower one. See
  the maintenance-pass entry below. Do not re-research without a materially different angle.]**

## Maintenance pass (2026-10-10): all three "fresh" candidates from the 2026-10-09 note were stale duplicates

Before researching any of the three "unresearched" candidates the previous note left (dynamic-UI
accessibility, offline-first sync conflict-resolution, i18n pluralization/RTL), ran
`grep -n -i "REJECTED\|already mined" BACKLOG.md` on all three terms first — the exact discipline this
file's own 2026-09-27 process note (`push-guard`'s entry) calls for and the exact step the 2026-10-09
note's author skipped. All three turned out to be re-hashes of categories already closed, in one case
after a non-trivial amount of fresh search budget was spent before the duplicate was caught:

- **Offline-first sync conflict-resolution audit — re-confirmed REJECTED.** Didn't trust the grep
  alone; re-ran real research to see if today's ecosystem had changed since the original 2026-09-05
  rejection. It hadn't. Fresh hits, all read for real content rather than trusted from a listing:
  `secondsky/claude-skills` → `mobile-offline-support` (fetched in full) opens "Build offline-first
  mobile applications..." and its only conflict guidance is an uncommented last-write-wins function
  with a commented-out "or merge" alternative and no guidance on which is safe when — a build/scaffold
  skill, not a review skill, consistent with the original rejection's framing. `SylphxAI/skills` →
  `design-offline-sync` (fetched in full; the `offline-sync-conflict-review` name a search engine
  surfaced doesn't actually exist as a directory in that repo — it's an aggregator's own re-title of
  this same skill) is a 19-line *design* skill ("Design an offline sync and conflict protocol..."),
  not an audit of existing code. A paid ToolForge Labs listing on agensi.io ("Repair Offline Sync,
  Reconnect & Conflict Recovery Bugs," $8.99) describes almost exactly this candidate's scope in its
  marketing copy — real evidence the pain point is genuine and monetized, but paywalled and
  unverifiable in full, so it doesn't count as "read the actual content" under this pack's bar either
  way. None of this contradicts the original verdict: real coverage exists, distributed across
  scaffold-side skills and at least one multi-lens review skill's "Replication/Sync correctness" lens
  (per the original citations), not packaged as a standalone audit skill — same shape as the
  `clean-exit`/RBAC rejections. Also independently re-confirmed `overwrite-guard`'s own Boundaries
  section already draws this exact line ("Not offline-sync / mobile conflict-resolution territory...
  it needs a real merge strategy, not a version check") — that boundary was written deliberately, not
  left as an oversight, so it's not a found gap either. Closed as covered, now for the third time; the
  next run should not pick this back up without an angle none of the three rounds have tried.
- **i18n pluralization/RTL-layout audit — re-confirmed REJECTED.** Fetched `daymade/claude-code-skills`
  → `i18n-expert/SKILL.md` in full: its "Audit → Fix → Validate" workflow is real and does lean
  audit-first, but it only checks `_one`/`_other` plural keys (not full CLDR zero/one/two/few/many/
  other) and treats RTL as conditional/out-of-scope by default — so today's narrower framing isn't
  covered by *this* skill. But the category itself doesn't need a narrower framing to die: the
  original 2026-09-03ish rejection's own citation, `i18n-readiness-review`, already names pluralization
  and RTL/layout-expansion as two of its eight checked dimensions in one audit. Closed as covered.
- **Dynamic-UI accessibility regression audit — re-confirmed REJECTED.** Fresh search for the
  specific ARIA-live-region/focus-management/keyboard-trap framing surfaced `sanky369/vibe-building-
  skills` → `accessibility-excellence` (explicit live-region guidance: `role="alert"` for blocking
  errors vs. `aria-live="polite"` for background status, plus a rule that the region must pre-exist in
  the DOM) and `ibelick/ui-skills` → `fixing-accessibility` (eval scenarios specifically covering modal
  focus-trapping, initial focus, and focus restoration on close — the "regression after a rewrite"
  shape this candidate wanted). Both are additional, more specific confirmations on top of the original
  rejection's citations. Closed as covered.

Lesson for future rounds, stated plainly since this is the second time it's been skipped (first at
2026-09-27): a candidate landing in a "Follow-up for the next run" note is not evidence it's
unresearched — it only means whoever wrote the note didn't check. `grep -n -i "REJECTED"` against the
candidate's keywords is a 10-second step that would have saved essentially all of the search budget
this round spent re-confirming three dead ends. Doing the grep *first* and then still re-verifying with
fresh searches (rather than trusting a 2026-09-03-era rejection blindly forever) is the right balance —
done above — but skipping the grep entirely, as both the 2026-10-09 note and (almost) this round did
before catching it, is pure waste.

`python tools/validate.py` still passes (`OK: 34 skills valid and consistent with README.`) — no skill
files touched this run; all three candidates died, so no README/example changes were needed either.

Follow-up for the next run — two genuinely fresh leads, checked against this file's full history
(not just skimmed) before being written down here, in territory the saturation notes above haven't
named yet:
- [x] **`cipher-guard` — SHIPPED 2026-10-11 (verified novel), see the maintenance-pass entry below.**
  The field-level encryption / key-rotation correctness audit candidate. Picked up this thread.
- New-skill candidate, unresearched: **mobile app privacy-label/data-safety-form accuracy audit** —
  does an app's actual code (SDKs embedded, data actually collected/transmitted, third-party
  processors) match what its App Store "Privacy Nutrition Label" or Play Console "Data Safety" form
  declares, catching the common drift mode of a new analytics SDK or ad network added to the code
  without anyone updating the declared-data-types form. Caution before researching: `rollout-guard`'s
  own research already found several *pre-submission compliance* checkers (`cruisediary/apple-app-
  review-skills`, `devsemih/appstore-review-skill`, `safaiyeh/app-store-review-skill`) that check
  "privacy manifests, entitlements, metadata" — read those in full first, since "does the declared
  manifest match the code" may already be exactly what one of them does, which would kill this
  candidate the same way the other three died today.

## `cipher-guard` — SHIPPED (2026-10-11, verified novel)

Git hygiene check first: `HEAD` was detached at the same commit `origin/main` already pointed to
(the same harmless local-ref-staleness shape every prior note has described) — fast-forwarded local
`main` to match, no data at risk.

Picked up the 2026-10-10 note's first fresh lead: **field-level encryption / key-rotation
correctness audit** — does an application that encrypts specific columns/fields actually keep that
encryption sound over the data's whole lifetime, not just at write time. Researched all three named
sub-angles against primary sources before writing anything:

- **Deterministic/searchable encryption vs. equality-query correctness — confirmed uncovered.**
  Checked `briiirussell/cybersecurity-skills` → `skills/crypto-audit/SKILL.md` (fetched in full, a
  real dedicated audit skill, not a scaffold — "Audit cryptography implementation," output is an
  audit report) since it's the closest match found for the broader candidate: it covers nonce
  uniqueness and a point-in-time "verify IAM permissions cover both encrypt AND decrypt" KMS check,
  but never mentions deterministic encryption, searchable encryption, or equality-query/uniqueness
  tradeoffs at all. Also checked `mukul975/Anthropic-Cybersecurity-Skills` →
  `performing-cryptographic-audit-of-application/SKILL.md` (fetched in full) — static algorithm/mode/
  hardcoded-key/KDF scanning only, no searchable-encryption content. Found no skill anywhere covering
  this angle. Independently found a real, filed bug confirming the problem is genuine, not
  hypothetical: `rails/rails#51553` ("Validation Does Not Work with Multiple Encryption Scheme") — a
  `uniqueness: true` validation on a column migrating from non-deterministic to
  `deterministic: true` encryption silently stops catching duplicates against any row still holding
  old-scheme ciphertext, per the maintainer-side comment: "the uniqueness validator cannot issue a DB
  query to check for uniqueness" against the previous scheme.
- **Key-rotation re-wrap vs. re-encrypt — confirmed uncovered.** The same `crypto-audit` skill
  mentions key-ID-per-ciphertext and a revocation question but never distinguishes re-wrapping a DEK
  from re-encrypting the rows it protects. `mukul975/.../implementing-envelope-encryption-with-aws-kms`
  (fetched in full) is a scaffold/build skill ("Objectives" are implementation tasks) whose only
  rotation language is "Key rotation re-encrypts DEKs with new master key" — that's the KEK-rewrap
  operation, and the skill never flags that this is a different, weaker guarantee than re-encrypting
  the actual data; an initial search summary's claim that this skill has an automated "auditkeypolicy"
  check turned out to be unfounded once the raw file was actually read (worth noting as a concrete
  instance of why this file's rule is "read the actual content," not "trust a search snippet"). Found
  a real, filed design issue confirming the exact two-operations distinction this candidate names:
  `pgexperts/chisel#140` names "credential rotation" (KEK re-wrap, O(1), "touches only the
  superblock") as different from "bulk DEK rotation" (full re-encryption, O(total_pages)), and states
  the bulk path "is only needed when the DEK itself is believed compromised — e.g., a process memory
  dump exposed the in-session DEK."
- **Envelope-encryption key-policy access-control drift — confirmed uncovered.** Checked
  `briiirussell/cybersecurity-skills` → `skills/iam-audit/SKILL.md` (fetched in full, since
  `crypto-audit` explicitly defers to it for "KMS / HSM patterns") — it's a general IAM least-privilege
  audit (cloud roles, access-advisor reports, permission accretion) that never mentions KMS, HSMs, or
  key policies at all; general IAM audits don't substitute for a KMS-key-specific one. Grounded the
  mechanism in AWS's own KMS IAM best-practices guidance, which warns that an IAM statement with
  `Resource: "*"` on `kms:Decrypt`/`kms:GenerateDataKey` can reach keys the account doesn't own,
  letting a principal decrypt ciphertext under *any* key that granted that account access — not just
  the one a reviewer thinks they're scoping.

Added `skills/cipher-guard/SKILL.md`, `examples/cipher-guard.md`, README skills-table + decision-table
rows, intro paragraph/count updates (thirty-four → thirty-five). `python tools/validate.py` passes
(`OK: 35 skills valid and consistent with README.`).

Follow-up for the next run: the second 2026-10-10 lead — **mobile app privacy-label/data-safety-form
accuracy audit** — is still unresearched; its own entry above already flags the caution to check
`rollout-guard`'s cited pre-submission compliance checkers in full before researching external
novelty, since one of them may already do exactly this.

## Maintenance pass (2026-10-12): privacy-label candidate researched and rejected; two fresh leads logged

Picked up the one open lead from the 2026-10-11 note (git hygiene: local `main` was 6 commits behind
`origin/main` after a detached-HEAD checkout — fast-forwarded, no data at risk, same harmless shape
every prior note has described).

- [x] **Mobile app privacy-label/data-safety-form accuracy audit — REJECTED, covered.** The angle:
  does an app's actual code/SDKs (what's collected and transmitted) match what its App Store "Privacy
  Nutrition Label" or Play Console "Data Safety" form declares, catching the common drift mode of a
  new analytics/ad SDK added without the form being updated. Followed the caution the 2026-10-10 note
  left and checked `rollout-guard`'s own cited pre-submission checkers in full first: fetched
  `cruisediary/apple-app-review-skills`'s `privacy-manifest-check`, `data-minimization-audit`, and
  `privacy-policy-check` (all three read in full, not trusted from a listing) — all three check
  `PrivacyInfo.xcprivacy`/permission-API usage/in-app policy links, but none compare the store's "App
  Privacy" declared data types against actual code or SDK behavior; also fetched `github/awesome-copilot`
  → `apple-appstore-reviewer` in full — it flags "data collection without disclosure" and "3rd-party SDK
  compliance" generically but never names the Nutrition Label or instructs a declared-vs-code
  cross-reference. The iOS side was a real (if partial) gap. The **Android side kills the candidate
  outright**: `android/skills` (the official Android team's own GitHub org, `developer.android.com`-
  sourced, read in full at `play/play-policy-insights/SKILL.md`) is "an automated auditor... that
  cross-references static code analysis with Play Store declarations to generate deterministic
  compliance reports, identifying undeclared data collection... across... Data Safety and Privacy
  domains" — a two-phase orchestrator + subagent pipeline whose explicit goal set includes
  `data_safety_part_1`/`data_safety_part_2`. That is this candidate's exact core mechanic (declared
  label vs. actual code), shipped by the platform owner itself, not a third party. The problem is real
  (an academic study of 6,051 apps found ~1/3 of collection/sharing disclosures conflict and 90%+ of
  Data Safety labels have at least one inconsistency; a 2023 Mozilla study separately found ~80% of
  reviewed apps' labels false or misleading vs. their own privacy policy) but it's already solved by a
  prominent, official source — same shape as the `clean-exit`/RBAC/offline-sync rejections: a near-exact
  match exists, the residual (iOS-side explicitness, cross-release drift tracking) is too thin to carry
  a standalone skill alone. Closed as covered; do not re-research without an angle neither
  `play-policy-insights` nor the three cruisediary skills touch.

No skill shipped this round (the one candidate died) — per the daily-agent rule, an unverified/covered
candidate is worse than no skill, and `python tools/validate.py` still passes (`OK: 35 skills valid and
consistent with README.`), unchanged since no skill files were touched.

Two fresh leads for the next run, surfaced while closing out the above but **not yet verified as
novel** — research before writing either:
- New-skill candidate, unresearched: **webhook/API signature-verification correctness audit** — HMAC
  computed over a re-parsed/re-serialized body instead of the exact raw bytes (breaks verification or,
  worse, gets implemented as "skip verification if it fails to parse"), a non-constant-time comparison
  (`==`/`string.Equals`) vulnerable to timing attacks instead of `crypto.timingSafeEqual`/`hmac.compare_digest`,
  and a missing or too-wide replay-tolerance window on the signed timestamp. Caution: `security-sweep`
  already lists "missing signature verification" as one bullet under its "Crypto misuse" category
  (`skills/security-sweep/SKILL.md:24`) — check whether that's a thin mention a dedicated skill would
  duplicate, or whether the raw-body/timing-safety/replay-window specifics are a genuinely deeper audit
  that bullet doesn't attempt, before researching external coverage.
- New-skill candidate, unresearched: **concurrent OAuth/JWT refresh-token race audit** — two requests
  that both see an expiring token and both trigger a refresh, where the loser's refresh either forks the
  token family (both mint valid-looking tokens) or overwrites/revokes the winner's new token, logging the
  user out or breaking single-use/rotation guarantees. Grounded in real, named 2026 advisories found this
  round (not yet independently re-verified against primary sources, and not yet checked against any
  existing skill pack for novelty): `better-auth` CVE-2026-53517 (non-atomic read-validate-revoke-mint at
  the refresh endpoint forks the token family under concurrent requests), NocoDB CVE-2026-47386 (concurrent
  single-use-code exchange mints two valid token pairs, breaking the PKCE single-use guarantee), and a
  real Coder PR (singleflight-dedup + optimistic-locking fix for one caller's refresh clearing another's
  valid token). Distinct from this pack's own `job-warden` (queue/cron idempotency, not an interactive
  auth-refresh race) and `overwrite-guard` (concurrent record edits, not token state) — verify that
  framing holds and check for existing coverage before writing anything.

## Maintenance pass (2026-10-13): both "fresh" leads were stale duplicates (again); shipped a small clock-sweep gap instead

Git hygiene check first: local `main` was detached and 7 commits behind `origin/main` (same harmless
staleness shape every prior note has described) — fetched and fast-forwarded to `origin/main`, no data
at risk.

Before researching either of the 2026-10-12 note's "two fresh leads," ran the `grep -n -i "REJECTED"`
discipline this file's own 2026-10-10 entry calls for — and both died immediately, for the third time
this exact mistake has happened (first at 2026-09-27, again at 2026-10-10, now the leads themselves
were stale on arrival):

- [x] **Webhook/API signature-verification correctness audit — already REJECTED, same category.**
  This is the identical candidate rejected on 2026-10-07 (search this file for "api-webhook-security"):
  `Intense-Visions/harness-engineering` → `api-webhook-security/SKILL.md` already covers
  `crypto.timingSafeEqual` constant-time comparison, a documented ±5-minute timestamp-tolerance window,
  and dual-secret-acceptance rotation — the exact three mechanisms the 2026-10-12 note re-described
  (raw-body HMAC, non-constant-time compare, replay-tolerance window) almost word-for-word. No new
  angle was offered this time either. Closed as covered; still the same verdict.
- [x] **Concurrent OAuth/JWT refresh-token race audit — already REJECTED, same category.** This is the
  identical candidate rejected on 2026-09-06 (search this file for "thundering-herd refresh calls"):
  `jeremylongshore/tons-of-skills-marketplace`'s auth-pack skills (`hubspot-auth`, `podium-auth`, etc.)
  already name both halves — the concurrent-refresh thundering-herd/single-flight fix and the
  rotation-invalidates-a-concurrent-caller's-token race. The 2026-10-12 note's framing (loser's refresh
  forks the token family or clobbers the winner's new token) is the same race described from the other
  side, with sharper CVE citations (`better-auth` CVE-2026-53517, NocoDB CVE-2026-47386) — real and
  worth keeping as grounding evidence if this is ever revisited, but they document the same mechanism
  the 2026-09-06 rejection already found covered, not a new one. Closed as covered; still the same
  verdict.

Both candidates died without needing fresh external research — the grep-first discipline worked exactly
as the 2026-10-10 note intended. Rather than end the run with nothing shipped, read every skill's
`SKILL.md` in full looking for a real, narrow, *already-grounded* gap small enough to verify and fix in
one sitting, instead of starting a new broad novelty sweep cold. Found one in `clock-sweep`: its sweep
list covers naive/aware mixing, DST-unsafe day arithmetic, offset-as-zone, and serialization boundaries,
but never mentions **month-granular calendar arithmetic** — adding/subtracting months for billing
anchors or annual reminders, where a day-of-month that doesn't exist in the target month must clamp
(Jan 31 + 1 month → Feb 28/29) and, critically, the clamped result must never be fed back in as the next
anchor or the date silently walks earlier every time it crosses a short month. Verified this is a real,
documented bug class, not a hypothetical: Stripe's own billing-cycle docs describe the clamp-from-the-
*original*-anchor contract explicitly (a day-31 anchor bills Feb 28/29, then back to Mar 31 — it doesn't
stay clamped), which is exactly the "derive from last month's result" bug that violates that contract.
Confirmed `proration-guard` doesn't cover this either (its period-boundary language is about which
billing period a credit applies against, not how the next recurrence date itself is computed) — so this
isn't an internal duplicate. **Added as a 7th sweep bullet + a Fix-patterns bullet + a hostile-clock
verification case to `skills/clock-sweep/SKILL.md`** (not a new skill — this is a real gap in an
existing skill's sweep list, and the pack is well past the point where every new finding deserves its
own file). Also added "month-granular calendar arithmetic (billing-anchor day-of-month drift)" to the
frontmatter description and a "renews on the wrong day every few months" trigger phrase so this
actually fires. `python tools/validate.py` passes (`OK: 35 skills valid and consistent with README.`,
unchanged skill count since this touched an existing file, not a new one).

Follow-up for the next run: the two 2026-10-12 leads are now closed for good — do not re-log either
without a materially different angle than what's cited above and in their original 2026-10-07/09-06
rejections. No fresh unresearched candidates are queued; the next run should do a genuinely new novelty
sweep in territory this file hasn't named yet (the pack is 35 skills deep across backend/infra, mobile,
billing, messaging, compliance, and real-time/connection correctness — frontend-build-tooling and
data-pipeline/ETL-specific correctness are two areas no prior round has explicitly tried), or continue
drift-auditing specific tool-syntax claims as docs age.

## Maintenance pass (2026-10-14): the two newly-suggested areas tried, five candidates all saturated

Git hygiene check first: local `main` matched `origin/main` exactly (clean fast-forward state, nothing
to reconcile) — no action needed, unlike most prior runs' detached-HEAD staleness.

Picked up the 2026-10-13 note's suggestion to try the two previously-untouched areas (frontend-build-
tooling, data-pipeline/ETL correctness) plus two infra-adjacent ideas that came up while reading. All
five died on external saturation, each checked against real `SKILL.md` content (not just listing
snippets) via GitHub code search:

- [x] **Frontend build-output secret/source-map leakage — REJECTED, saturated.** The candidate:
  production source maps left enabled (`.map` files exposing full original source — comments, internal
  endpoints, sometimes literal keys) and secrets inlined into the client bundle via a bundler's public-
  env-var convention (`NEXT_PUBLIC_*`, `VITE_*`, `EXPO_PUBLIC_*`) when a value needed to stay server-only.
  Real problem, but already shipped as a dedicated check in many places, not a stray mention: `addyosmani/
  web-quality-skills` (official — Addy Osmani, Google Chrome web-perf lead) → `skills/best-practices/
  SKILL.md` has the exact "hidden-source-map vs. exposed source-map in production" code comparison,
  mirrored verbatim across at least 8 other repos that vendor it (`davila7/claude-code-templates`,
  `tech-leads-club/agent-skills`, `open-gsd/gsd-pi`, others). `Shankulkarni/vibe-audit` →
  `audit-vercel-deployment/SKILL.md` names this exact pairing as one "consistent class of
  misconfiguration": "secrets end up in the browser bundle (via `NEXT_PUBLIC_` prefix), source maps are
  enabled in production." `JoviDeCroock/forklight` → `audit-secrets/SKILL.md` and
  `suhailkakar/the-skills` → `secrets-and-env/SKILL.md` both dedicate a skill specifically to client-
  bundle secret exposure. Closed as covered; do not re-research without a sub-angle none of these touch.
- [x] **Stale JS chunks after a rolling deploy (`ChunkLoadError`/`vite:preloadError`) — REJECTED,
  saturated.** The candidate: a tab left open across a deploy requests a content-hashed chunk the new
  build no longer serves, breaking navigation with no recovery. `enowdev/enowxcli` →
  `skills/frontend-errors/SKILL.md` has a dedicated "§7: After a deploy" section naming the exact
  mechanism and all three browsers' error strings. Multiple Sentry-triage skills (`brianlovin/agent-
  config`, `getsentry/sentry-for-ai`, and four more mirrors) explicitly classify `ChunkLoadError` as a
  known, self-resolving deployment-caching pattern with a documented fix (reload-on-chunk-error). Closed
  as covered.
- [x] **Tailwind JIT/purge silently dropping dynamically-constructed class names
  (`` `bg-${color}-500` `` never generated because the scanner needs literal strings) — REJECTED,
  saturated.** Extremely common ground: 15+ independent `SKILL.md` files name this exact gotcha
  (`0xDarkMatter/claude-mods` → `tailwind-ops`, `curiositech/windags-skills` + its `port-daddy` mirror →
  `tailwind-v4-expert`, `mew-ton/coding-guidelines` → a skill with no other purpose than this one rule,
  `antfu/skills` → `unocss`, and a dozen more), all converging on the same fix (`safelist` /
  `@source inline(...)`). Closed as covered.
- [x] **Serverless/Lambda-to-RDS connection-pool exhaustion (each cold-started function opening its own
  connection, no pooling) — REJECTED, saturated.** This is treated as baseline AWS-serverless knowledge,
  not a gap: the official `aws/agent-toolkit-for-aws` → `rds-oracle/SKILL.md` and `rds-sqlserver/
  SKILL.md` both name "module-level connection pool outside the handler" + RDS Proxy explicitly, and the
  same RDS-Proxy-for-Lambda fix appears near-verbatim in at least 10 other independent serverless/AWS
  skills found this round. Closed as covered.
- [x] **Distributed lock / leader-election fencing-token correctness — re-confirmed already REJECTED.**
  Before researching, grepped this file per the 2026-10-10 discipline and found this exact candidate was
  already researched and closed as saturated on 2026-09-28 (`j4flmao/agent-skills` → `dist-sys-auditor`
  cites the same Kleppmann fencing-token argument). No new angle offered; not re-opened.

Also checked whether `stale-guard`'s own "near-miss" search-index/primary-database sync-audit thread
(flagged unresolved in two earlier rounds, around the 2026-09 marks) had anything new to add — re-read
`skills/stale-guard/SKILL.md`, which already explicitly lists "search indexes (Elastic mirroring the
DB)" as one of the copies it audits for staleness; this is an internal duplicate, not a gap, so left
alone.

No skill shipped this round — five real candidates, five saturated. `python tools/validate.py` still
passes (`OK: 35 skills valid and consistent with README.`), unchanged since no skill files were touched.

No fresh unresearched candidates survived this round's checking to queue for next time. The next run
should either (a) try territory further from this pack's existing backend/infra/billing/compliance
center of gravity — e.g. CLI-tool argument-parsing/exit-code correctness, desktop-app auto-update
integrity, or game-server tick/simulation determinism — none of which this file has tried yet, or
(b) pick up the standing drift-audit fallback: re-verify specific tool-syntax claims (Postgres/MySQL/
git/CI/cloud-provider command flags) across the 35 skills against current docs, since that surface ages
independent of novelty and hasn't had a full pass since round 8 (2026-10-08).

## Maintenance pass (2026-10-15): three fresh-territory candidates saturated; drift audit round 9 (`cipher-guard`) clean

Git hygiene check first: local `main` was detached one commit ahead of the local `main` ref (the
2026-10-14 maintenance commit existed on `origin/main` already — just a stale local branch pointer,
same harmless shape prior notes describe) — fast-forwarded local `main` to match, no data at risk.

Tried the three specific unresearched areas the 2026-10-14 note named (CLI-tool argument-parsing/exit-
code correctness, desktop-app auto-update integrity, game-server tick/simulation determinism). All
three died on real, dedicated external coverage, checked via GitHub code search against actual
`SKILL.md` content:

- [x] **CLI argument-parsing/exit-code correctness — REJECTED, saturated.** Searched
  `filename:SKILL.md` for exit-code/argument-parsing audit language. Found a crowded field of
  dedicated CLI-correctness skills, not just incidental mentions: `kylesnowschwartz/ralph-ban` →
  `skills/cli-qa/SKILL.md` ("QA a CLI tool", "validate exit codes", golden-file comparison of
  stdout/stderr/exit-code as separate evidence channels), `0xDarkMatter/claude-mods` →
  `skills/cli-ops/SKILL.md` (semantic exit-code enumeration 0-7, stderr-vs-stdout discipline),
  `Roasbeef/beefstack` → `skills/agent-cli/SKILL.md` (explicit "use semantic exit codes, not just
  0/1" + documenting them for agent consumption), and `alibaba/fast-modeling-language` →
  `skills/fml/SKILL.md` (a full exit-code table with distinct codes per failure class). Closed as
  covered; do not re-research without a sub-angle none of these touch.
- [x] **Desktop-app auto-update integrity — REJECTED, saturated.** The candidate (signature
  verification on update artifacts, staged/rollback-capable rollout) is explicitly named, not a
  tangential mention, across multiple dedicated sources: `martinholovsky/claude-skills-generator` →
  `skills/auto-update-systems/SKILL.md` (and its `ConnectiveTCS/Gradient_Generator` mirror) is
  entirely about this — cites CVE-2024-39698 (a real signature-verification-bypass CVE) by name and
  covers signature verification, rollback mechanisms, and staged rollouts as its three stated
  specialties. `florianbuetow/claude-code` → `plugins/appsec/skills/integrity/SKILL.md` (mirrored in
  `florianbuetow/codex-plugins`) and `scholarly360/owasp-top10-web-skills` →
  `skills/software-data-integrity-failures/SKILL.md` both name "auto-update without verifying digital
  signatures" as an explicit checklist item (the latter citing CWE-494 directly). Closed as covered.
- [x] **Game-server tick/simulation determinism — REJECTED, saturated.** `zeroes-ones/Skills` →
  `skills/05-development/game-networking-developer/SKILL.md` states the exact property this
  candidate targets as "Rule 6: Determinism is a requirement for lockstep, not a luxury... one
  divergent `sin()` call desyncs the entire simulation," naming fixed-point/deterministic-float
  libraries as the fix. `dreamteam-hq/brigid` → `skills/gamedev-multiplayer/SKILL.md` has a dedicated
  "Determinism Assumptions Without Verification" anti-pattern section plus a separate tick-rate-
  stability check. `fcsouza/agent-skills` → `skills/game-backend-architecture/SKILL.md` (mirrored in
  two other repos) covers the fixed-timestep-accumulator/configurable-tick-rate mechanics this
  candidate would have needed to build from scratch. Closed as covered.

With all three fresh leads dead, ran the overdue drift-audit round instead (last full pass was round 8,
2026-10-08; `cipher-guard` shipped 2026-10-11, after that round, and had never had a dedicated
fact-verification pass). Read the full `skills/cipher-guard/SKILL.md` and verified every externally-
checkable claim against primary/authoritative sources:

- **`rails/rails#51553`** ("Validation Does Not Work with Multiple Encryption Scheme") — confirmed real
  via direct fetch of the issue page: closed as stale/`completed` in August 2024 with no fix merged, a
  maintainer reply confirming the limitation is inherent (the validator can't query ciphertext encrypted
  under the previous non-deterministic scheme). If anything this *strengthens* the skill's claim — the
  bug is still live in current Rails, not patched. No change needed.
  Note: GitHub's own page now shows this backlog file's own prior entry as the only other citation of
  the issue found on the web — expected, not a problem.
- **`pgexperts/chisel#140`** — confirmed via search: issue separates "credential rotation" (re-wrap,
  touches only the superblock, O(1)) from "bulk DEK rotation" (full re-encryption, O(total_pages)),
  matching the skill's wording closely; PR #159 implementing bulk DEK rotation is linked as closing it.
  No drift.
- **AWS KMS wildcard-`Resource: "*"` cross-account `kms:Decrypt` reach** — confirmed against AWS's own
  IAM-policies-best-practices page: an IAM policy (as opposed to a key policy) with a wildcard resource
  can reach keys in other accounts that have granted the caller's account access, not just keys the
  account owns itself — matches the skill's framing. No drift.
- **AWS KMS automatic rotation rotates only the CMK's backing key material, leaving already-wrapped
  DEKs decryptable** — confirmed: AWS retains all prior backing key material indefinitely specifically
  so ciphertext encrypted under earlier rotations keeps decrypting; the key ID itself never changes.
  No drift.

All four claims checked out — no fixes needed, no skill files touched this round. `python tools/validate.py`
still passes (`OK: 35 skills valid and consistent with README.`), unchanged skill count.

Follow-up for the next run: no fresh unresearched candidates survived today's checking. The next run
should either (a) try territory further still from this pack's backend/infra/billing/compliance/
real-time center of gravity than today's three attempts (which were themselves already one layer out
and still saturated) — e.g. machine-learning training-pipeline reproducibility, embedded/firmware
OTA-update correctness, or browser-extension permission/manifest drift — or (b) treat the drift-audit
thread as fully caught up again (all 35 skills now have a pass since their last content change) and wait
for either a new skill to ship or a specific external fact to be reported stale before re-checking.

## Maintenance pass (2026-10-17): the three 10-15 leads plus five more, all saturated

Git hygiene check first: this session's clone had a stale `origin/main` remote-tracking ref (showed
3438765, two commits behind the real `origin/main`/`432dbdd` — the 2026-10-14/15 maintenance commits
had in fact already landed on the remote). A plain `git fetch` resolved it; no actual divergence, no
force-push, nothing lost. Noting it in case another run's clone shows the same stale-ref symptom.

Tried all three leads the 2026-10-15 note named, plus five more candidates that came up while reading
this file's own exhaustive "already covered" list for gaps in its coverage. All eight died on real,
dedicated external coverage, each checked against actual `SKILL.md` content via GitHub code search
(not just a title match):

- [x] **Browser-extension permission/manifest drift — REJECTED, saturated.** `sealad886/agent-plugins`
  → `extension-security-and-permissions/SKILL.md` ("re-audit permissions whenever the feature set
  expands"), `saeedkolivand/ai-job-hunter-app` → `.claude/skills/extension-standards/SKILL.md` (a
  dedicated "Permissions — least privilege" section plus protocol-lockstep drift checks), and
  `LeoYeAI/openclaw-master-skills` → `openclaw-cws-publisher/SKILL.md` (a `validate_cws_package.py`
  script that specifically blocks "persistent host permissions... missing permission justifications,
  privacy-practice drift") all cover this directly, not tangentially. Closed as covered.
- [x] **Embedded/firmware OTA-update correctness — REJECTED, saturated.** Extremely crowded: at least
  eight independent dedicated OTA skills found (`easyzoom/aix-skills` → `ota-update-integration`,
  `tonone-ai/tonone` → `volt-ota` + `volt-firmware` with explicit partition-table/rollback-condition
  design, `asalhamed/dev-agents` → `firmware-ota-agent` naming TUF/Uptane/IETF SUIT signed-update
  metadata, `ggrace519/claude-code-dev-studio` → `embed-ota` covering signature verification/A-B
  swap/resumability). Closed as covered.
- [x] **ML training-pipeline reproducibility — REJECTED, saturated.** 9000+ code-search hits; dozens
  of dedicated MLOps skills name the exact practice (seed-setting, dataset/environment versioning,
  experiment-tracking lineage) as a first-class concern (`ayush488-glitch/mlops-stack` →
  `mlops-training-eval/SKILL.md` has a literal "Step 5: Model Training Pipeline / The Four
  Reproducibility Elements" section). Closed as covered.
- [x] **Soft-delete query-scope leakage (`deleted_at` filter forgotten in some read path, leaking
  soft-deleted rows back to users) — REJECTED, saturated.** A real, specific bug pattern, but it's
  treated as a standard bullet in general schema-design guidance everywhere it was found
  (`mohitagw15856/pm-claude-skills` → `database-schema-design/SKILL.md`: "All application queries
  MUST filter `WHERE deleted_at IS NULL`... Use a view or ORM scope to enforce this"; `avo-hq/avo` →
  `avo-filters/SKILL.md` ships a first-class `Scope` construct specifically for this; PostHog's own
  `signals-scout-feature-flags/SKILL.md` independently reinvents the same "soft-deleted but still
  called" check for a different entity). Also overlaps this pack's own prior-rejected "multi-tenant
  isolation" candidate (line ~127, 269 hits, 4+ dedicated auditors) closely enough that a standalone
  skill would mostly duplicate it. Closed as covered.
- [x] **JWT algorithm-confusion / `alg:none` verification correctness — REJECTED, saturated.** Over a
  dozen near-identical dedicated skills found (`sickn33/agentic-awesome-skills` →
  `hunt-jwt-crypto`, `plurigrid/asi` → `exploiting-jwt-algorithm-confusion-attack`, mirrored in at
  least six other marketplaces). This pack's own `security-sweep` already names crypto-misuse as one
  of its OWASP-style categories, so the defensive angle is covered in-pack too. Closed as covered.
- [x] **Third-party script / SRI supply-chain trust — REJECTED, saturated.** `addyosmani/
  web-quality-skills` (official, Google Chrome web-perf lead) → `best-practices/SKILL.md` covers this
  by name, citing the real 2024 `polyfill.io` supply-chain attack (~100k sites); `UnboundCompute/
  security-agent-skills` → `auditing-third-party-script-and-sri-trust/SKILL.md` is a dedicated skill
  for exactly this; `jamditis/claude-skills-journalism` → `api-hardening/SKILL.md` cites the same CVE
  with a date and source. Closed as covered.
- [x] **Mobile deep-link / App Links / Universal Links hijacking (`assetlinks.json` / AASA
  verification) — REJECTED, saturated.** A whole family of near-identical
  `exploiting-deeplink-vulnerabilities` skills, mirrored across a dozen+ repos, plus
  `agents-inc/skills` → `mobile-deep-linking-app-links/SKILL.md` covering the defensive/correctness
  side (verification-file hosting requirements, custom-URI-scheme hijacking risk). Closed as covered.
- [x] **Idempotency-key TTL/expiry correctness (TTL shorter than the retry window silently
  reintroducing duplicates) — re-confirmed already covered.** This is the same ground this file
  already closed as "duplicate of `job-warden` Q1" (line ~127); today's search surfaced a specific
  dedicated skill making the exact point (`j4flmao/agent-skills` → `idempotency/SKILL.md`: "Expiring
  keys too early: If the TTL is shorter than the maximum retry window, retries after expiry create
  duplicates") — strengthens the prior rejection rather than reopening it. Not re-opened.

No skill shipped this round — eight real candidates, eight saturated. `python tools/validate.py`
still passes (`OK: 35 skills valid and consistent with README.`), unchanged skill count and `main`
now correctly tracks `origin/main` at the same commit (see git-hygiene note above).

Follow-up for the next run: two genuinely fresh, *unresearched* leads surfaced while reading today —
hand these off rather than re-trying today's eight exhausted angles:
- [x] **LLM prompt/response cache invalidation** — researched and REJECTED, saturated; see
  maintenance pass (2026-10-18) below.
- [x] **Monorepo remote build-cache poisoning/staleness** — researched and REJECTED, saturated; see
  maintenance pass (2026-10-18) below.

## Maintenance pass (2026-10-18): the two outstanding 10-17 leads tried, both saturated

Git hygiene check first: this session's clone had `HEAD` detached one commit *ahead* of the local
`main` ref (local `main` was pinned to `3438765`, three commits behind `48c3842`), while `origin/main`
already carried all three — the same harmless stale-local-ref shape prior rounds have described, just
inverted (ahead instead of behind). `git checkout main && git merge --ff-only 48c3842` fast-forwarded
the local branch; `git push origin main` correctly reported "Everything up-to-date" and a fresh
`git fetch` confirmed `origin/main` already matched. No divergence, no force-push, nothing lost.

Tried both leads the 2026-10-17 note handed off, each checked against actual `SKILL.md` content via
GitHub code search (not just a title match):

- [x] **LLM prompt/response cache invalidation — REJECTED, saturated.** `ajyadav013/claude-kit` →
  `skills/llm-caching-strategies/SKILL.md` names this exact scenario as a trigger condition verbatim:
  "Designing invalidation for cached answers when the underlying knowledge base or policy changes" and
  "Diagnosing a prompt cache that reports a surprisingly low hit rate despite a 'stable' system prompt" —
  the dedicated failure mode this candidate would have built from scratch. `jamiojala/skillforge` →
  `skills/llm-caching-strategist/SKILL.md` ships a validation step literally named `invalidation-test`
  against `semantic cache`/`prompt cache` keywords. Both treat cache-key-dimension completeness
  (template/model/policy version) as the core correctness property, not a tangential mention. Closed as
  covered; do not re-research without a sub-angle neither of these touches.
- [x] **Monorepo remote build-cache poisoning/staleness — REJECTED, saturated.** `yigitkonur/
  skills-by-yigitkonur` → `skills/ci-cd-optimize/SKILL.md` names "poisoning" by that word as one of the
  three things its dedicated `references/caching.md` covers for dependency/build caches. `mckissinger/
  bosun` → `skills/bosun-ci/SKILL.md` states the exact invariant this candidate targets: "the key must
  cover every input the task reads, including environment variables and tool versions... cached passes
  hide the reruns that flake evidence depends on." `mcorbett51090/RavenClaude` →
  `plugins/developer-tooling/skills/optimize-build-and-cache/SKILL.md` has a dedicated "hermeticity
  leaks" section calling out timestamps, absolute paths, mid-build network fetches, and unpinned tool
  versions as poisoning a build cache's trust, with "a cache that can return a wrong artifact is worse
  than no cache." All three hit the specific mechanism (under-specified cache key vs. non-hermetic
  input), not just general build-speed advice. Closed as covered.

No skill shipped this round — two real candidates, two saturated. `python tools/validate.py` still
passes (`OK: 35 skills valid and consistent with README.`), unchanged skill count.

Follow-up for the next run: three fresh, *unresearched* leads surfaced while reading today — hand these
off rather than re-trying today's two exhausted angles:
- [x] **Infrastructure-as-code state drift** — researched and REJECTED, saturated; see maintenance pass
  (2026-10-19) below.
- [x] **Feature-flag lifecycle staleness** — researched and REJECTED, saturated; see maintenance pass
  (2026-10-19) below.
- [x] **Kubernetes liveness/readiness probe correctness** — researched and REJECTED, saturated; see
  maintenance pass (2026-10-19) below.

## Maintenance pass (2026-10-19): eight candidates researched, all saturated — crowded adjacent territory

Git hygiene check first: this session's clone had `HEAD` detached at `f3fd4c1` (four commits ahead of
the local `main` ref, which was still pinned to `3438765`) while `origin/main` already carried all four
— the same harmless stale-local-ref shape prior rounds have described (rounds 2026-10-15, -17, -18), each
time in a different direction. `git checkout main && git merge --ff-only f3fd4c1` fast-forwarded the
local branch; `git push origin main` correctly reported "Everything up-to-date". No divergence, no
force-push, nothing lost.

Tried all three leads the 2026-10-18 note handed off, each checked against actual `SKILL.md` content via
GitHub code search (not just a title match):

- [x] **Infrastructure-as-code (Terraform/Pulumi/CloudFormation) state drift — REJECTED, saturated.**
  Extremely crowded, not a tangential mention: `tonone-ai/tonone` → `skills/terra-drift/SKILL.md` is a
  dedicated drift-detection-and-remediation workflow triggering verbatim on "our state does not match
  reality"; `fabn/claude-plugins` → `plugins/terraform/skills/drift/SKILL.md` names the exact
  out-of-band-change mechanism ("identify resources where remote state differs from Terraform code...
  approve alignment, commit verified code"); `thrashr888/hcptf-cli` → `.skills/drift/SKILL.md` and at
  least ten other `terraform-*`/`iac-*` skills all carry a named drift-detection section. Closed as
  covered.
- [x] **Feature-flag lifecycle staleness (fully-rolled-out flags and their dead code paths never
  removed) — REJECTED, saturated.** `SamuelChien/mega-skills-collection` →
  `flag-cleanup/SKILL.md` is a dedicated `/flag-cleanup` workflow scanning for "flags older than 90
  days, used in ≤2 places"; `moonshineaitech/LunaStack` → `feature-flag/SKILL.md` states the exact
  failure mode this candidate targets almost verbatim ("Don't let flags accumulate past 90 days without
  review... Don't forget to remove both the flag AND the dead code path when cleaning up — half-removed
  flags are worse than active ones"); `iceflower/agent-skills` → `feature-flag/SKILL.md` adds CI-enforced
  flag-age tracking. Closed as covered.
- [x] **Kubernetes liveness/readiness probe correctness (a probe checking the wrong dependency boundary)
  — REJECTED, saturated.** This is the same failure mode the 2026-08-20 round already rejected under
  "worker startup/readiness audit" (health-check-validator, prod-readiness-review, etc.), re-confirmed
  today with an even more specific match: `ericrisco/rsc-harness` → `skills/monitoring/SKILL.md` states
  the exact anti-pattern verbatim as a table row — "Probe cascades every downstream [dependency] → one
  slow dep fails the probe → restart loop" and "Liveness checks the database → slow DB → restart loop
  turns a blip into an outage → liveness = process only; DB lives in readiness". `cjsmitty/ai-agent-lab`
  → `k8s-probe-tuning/SKILL.md`, `RedHatProductSecurity/prodsec-skills` → `health-probes/SKILL.md`, and
  `ShaileshRawat1403/dax` → `deploy-readiness/SKILL.md` ("Flag readiness handlers that signal ready
  before warm-up is complete") all cover the same boundary-confusion bug. Closed as covered; do not
  re-research without a sub-angle none of these touch.

With all three leads dead, searched five more candidates in adjacent-but-untried territory before
concluding today's research (all checked against real `SKILL.md` content, not title matches):

- [x] **Webhook receiver signature verification / replay / idempotency — REJECTED, saturated.**
  `deangrant/agents` → `.agents/skills/api-webhook-signature-verification/SKILL.md` and
  `jeremylongshore/tons-of-skills-marketplace` → `skills/.curated/creating-webhook-handlers/SKILL.md`
  cover HMAC-over-raw-body, constant-time compare, timestamp replay windows, and idempotent handling as
  their stated scope, not a side mention. Closed as covered.
- [x] **Distributed rate limiting / token-bucket state not actually shared across instances — REJECTED,
  saturated.** `sickn33/agentic-awesome-skills` → `skills/upstash-ratelimit/SKILL.md` ("Because state
  lives in Redis, every instance of a serverless function...") and `axosecurity/ai-function-builder-
  skills` → `skills/redis-token-bucket-rate-limiter/SKILL.md` are dedicated, correctly-scoped skills for
  exactly this failure mode. Closed as covered.
- [x] **SAML/OIDC signing-certificate rotation across multiple IdPs/applications — REJECTED,
  saturated.** `selvarajmurugesan90/ops-engineering-skills` →
  `certificate-lifecycle-management-at-scale/SKILL.md` is named by a sibling skill specifically as the
  place that tracks "rotating the SAML/OIDC signing certificates this federation trust depends on,
  across many applications at once" — the exact candidate. Closed as covered.
- [x] **Saga/distributed-transaction compensation completeness (a failed step leaves an earlier step's
  side effect uncompensated) — REJECTED, saturated.** At least eight independent dedicated skills
  (`wshobson/agents` → `saga-orchestration/SKILL.md`: "Don't skip compensation testing — the rollback
  path is the hardest to get right"; `ggichuru/cto-brain` → `distributed-sagas-and-workflows/SKILL.md`;
  `giuseppe-trisciuoglio/developer-kit` → `spring-boot-saga-pattern/SKILL.md`: "Verify every forward
  step has a corresponding compensation"). Closed as covered.
- [x] **Read-replica lag causing read-after-write staleness — REJECTED, saturated.** A full family of
  dedicated skills: `SkillMedev/skills` → `replication-lag-debugger/SKILL.md` (triggers verbatim on
  "users see stale data right after saving"), `bedkillerspacex-boop/codex-skill-library` →
  `read-replica-lag-incident/SKILL.md`, `shubhamtaywade82/node-agent-skills` → three separate
  `node-*-read-replica*` skills, `ericrisco/rsc-harness` → `skills/scaling/SKILL.md` ("Replicas serve
  reads, never the source of truth for read-after-write"). Closed as covered.

Two more candidates checked quickly after that (confirming the pattern rather than exhausting the
search): **OAuth token-refresh thundering herd** (`jeremylongshore/tons-of-skills-marketplace` →
`hubspot-auth/SKILL.md` and `guidewire-install-auth/SKILL.md` both name the exact "single-flight gate"
fix) and **presigned-URL scope/expiry abuse** (`UnboundCompute/security-agent-skills` →
`auditing-presigned-url-scope-abuse/SKILL.md` is a dedicated skill matching this candidate almost
word-for-word) and **mobile IAP receipt-validation/entitlement-restore correctness** (Unity's own
official `Unity-Technologies/skills` → `implement-in-app-purchases/SKILL.md`, plus `capawesome-team` and
multiple KMP packs, all cover receipt validation, entitlement checking, and restore-purchase flows as
named sections) — both saturated too.

No skill shipped this round — eight candidates researched in depth, two more spot-checked, all ten
saturated. `python tools/validate.py` still passes (`OK: 35 skills valid and consistent with README.`),
unchanged skill count.

**Pattern worth naming plainly:** today's ten candidates spanned this pack's own adjacent territory
(infra drift, probes, flags) and genuinely different territory (webhooks, rate limiting, SSO certs,
sagas, replication, OAuth, presigned URLs, IAP) — all ten were already covered by dedicated, specific
skills elsewhere. The broader Claude-skill ecosystem (large generic marketplaces like
`sickn33/agentic-awesome-skills`, `jeremylongshore/tons-of-skills-marketplace`,
`shubhamtaywade82/node-agent-skills`) has grown dense enough that most well-known backend/infra
correctness bugs now have a dedicated skill somewhere. This pack's remaining edge is likely in narrower,
more specific "audit an existing implementation for a particular lifecycle bug" framings (the
`*-guard` pattern already used here) rather than broad infra/protocol topics — future rounds should
lean into that rather than re-trying generic infra ground.

Follow-up for the next run: three fresh, *unresearched* leads for next time, chosen to be a layer away
from today's ten exhausted angles rather than adjacent to them:
- [x] **Multi-tenant Postgres row-level security (RLS) policy drift/bypass** — researched and REJECTED,
  saturated; see maintenance pass (2026-10-20) below.
- [x] **ETL/data-pipeline schema-evolution silent data loss (positional/implicit mapping)** — researched
  and REJECTED, saturated; see maintenance pass (2026-10-20) below.
- [x] **OTP/email-link single-use and rate-limit correctness** — researched and REJECTED, saturated; see
  maintenance pass (2026-10-20) below.

## Maintenance pass (2026-10-20): five candidates researched, all saturated — the pattern holds

Git hygiene check first: clean clone, `main` already matched `origin/main`, no detached-HEAD/stale-ref
repair needed this time (the first round in several without one).

Tried the three leads the 2026-10-19 round handed off, each checked against actual `SKILL.md`/reference
content via GitHub code search (not title matches):

- [x] **Multi-tenant Postgres RLS policy drift/bypass — REJECTED, saturated.** The exact audit framing
  (not how-to-write-RLS) is already explicit, dedicated content: `Nmor/the-council` →
  `skills/postgres-patterns/SKILL.md` states it as a checklist line almost verbatim — "Verify cross-tenant
  reads and writes with the actual runtime role; it must lack superuser, BYPASSRLS and ownership bypass.
  Test missing tenant context and pooled connection reuse. Use FORCE ROW LEVEL SECURITY where owners need
  isolation." At least six independent forks of a Supabase-focused skill (`Asymmetric-al/core`,
  `seaworld008/Commonly-used-high-value-skills`, `PracticalSwan/agent-skills`, others) carry the same
  `SECURITY DEFINER` / `BYPASSRLS` bypass warning as a named anti-pattern:
  "`SECURITY DEFINER` functions bypass RLS... Never add `SECURITY DEFINER` to resolve a permission error;
  it silently removes access control without fixing the underlying cause." `aibot88/sec_skill_store` →
  `postgres-security-and-data-access-hardening/SKILL.md` names the exact design step ("state the bypass
  risks (table owner, `BYPASSRLS`)"). Closed as covered.
- [x] **ETL/data-pipeline schema-evolution silent data loss (positional mapping) — REJECTED, saturated.**
  The specific positional-reuse failure is named directly: the "Schema Evolution Compatibility" entry on
  claudskills.com (surfaced via web search, content not independently re-fetched but the description is
  specific and on-point) states it evolves shared data contracts — "events, API payloads, DB columns,
  protobuf/avro" — "without breaking live consumers," with the explicit rule "never reusing an Avro
  position and reserving retired fields." `selvarajmurugesan90/ops-engineering-skills` →
  `kafka-schema-registry-and-compatibility-management/SKILL.md` and `Nmor/the-council` →
  `skills/api-design/references/schema-evolution.md` cover the same producer/consumer contract-breakage
  territory with compatibility-mode enforcement (`BACKWARD`/`FORWARD`/`FULL`) as their stated scope. The
  specific "positional/implicit mapping with no named contract" framing is less densely covered than the
  schema-registry case, but close enough (the Avro-position rule is the same root cause under a different
  serialization) to not clear the novelty bar today. Closed as covered.
- [x] **OTP/email-link single-use and rate-limit correctness — REJECTED, saturated.** The most densely
  covered of the three: `himself65/auth-spec` → `skills/create-auth/references/features/email-otp.md`
  states the exact invariants this candidate names, almost verbatim — "Each code is single-use — consume
  with one conditional write (affected-rows check), never find-then-delete," "Delete all previous codes
  for the same email when generating a new one," and "3-5 failed attempts per code, then invalidate it and
  require a new send (OWASP recommends 3)." `tyroneross/build-loop` →
  `skills/authentication/references/resend-otp-magic-link.md` adds the companion half ("Within
  `expiresIn` window: invalidate the previous token, send a new one... Rate-limit per email: max 3 sends
  per 10 minutes"). `diegosouzapw/awesome-omni-skills` → `broken-authentication/SKILL.md` (and its v2/omni
  variants) audits exactly these properties ("Single-use enforcement," "Test rate limiting on OTP
  endpoint"). Closed as covered.

Two more candidates spot-checked beyond the handoff list, both also saturated:

- [x] **ML feature-store training/serving skew (a feature computed one way at training time, another at
  serving time, degrading a model silently) — REJECTED, saturated.** `databricks/databricks-agent-skills`
  → `skills/databricks-ml-training/SKILL.md` and its `references/feature-store.md` name the exact failure
  mode as the lead paragraph: "The problem it solves — training-serving skew. When your training pipeline
  computes features one way and your serving pipeline computes them differently, models degrade silently
  in production," plus the companion point-in-time-join/future-leakage check. Closed as covered.
- [x] **Email authentication (SPF/DKIM/DMARC alignment) deliverability audit — REJECTED, saturated.**
  `aaron-he-zhu/aaron-marketing-skills` → `email/setup/deliverability-qa/SKILL.md` and
  `mcorbett51090/RavenClaude` → `plugins/email-engineering/skills/deliverability-audit/SKILL.md` are
  dedicated pre-send audits scoring SPF/DKIM pass, DMARC *alignment* specifically ("does DMARC pass (an
  authenticated identifier aligns with `From:`)? A pass on auth but fail on alignment is the most common
  'but we have SPF!' trap"), domain/IP reputation, and list hygiene. Closed as covered.

No skill shipped this round — five candidates researched, all saturated. `python tools/validate.py` still
passes (`OK: 35 skills valid and consistent with README.`), unchanged skill count. Two quick checks on
candidate #6/#7 (credential-rotation propagation lag, seat/license-count enforcement drift) came back
noisy/inconclusive rather than a clean saturated-or-clear verdict — logged below as genuinely unresearched
leads rather than guessed at.

Follow-up for the next run — two fresh, *unresearched* leads:
- [x] **`rotation-guard` — SHIPPED (verified novel), credential/secret rotation propagation lag.** A
  DB/API credential rotated in the secrets manager (Vault lease renewal, RDS password, a rotated API key)
  where a long-lived connection pool, sidecar cache, or in-memory client keeps using the stale credential
  until a forced restart/reconnect — causing either an outage at the old-credential revocation boundary,
  or the more interesting bug: silently continuing to work past expected revocation because rotation
  never actually propagated to every consumer. Verified uncovered with a properly targeted pass (the
  "noisy" search from last run was the wrong query shape): the most prominent mirrored "rotation" skill
  across marketplaces, `aj-geddes/useful-ai-prompts` → `skills/secrets-rotation/` (mirrored on
  claudskills.com, crossaitools.com, claudemarketplaces.com, skillselion.com), was fetched directly
  (SKILL.md + all three `references/` guides: Node.js, Python/Vault, Kubernetes) and confirmed to be a
  *build-a-rotation-pipeline* scaffold (generate/store/rollback a new secret) with no coverage at all of
  stale connection pools, in-memory client caches, Vault lease-renewal responsibility, or the
  env-var-vs-volume-mount Kubernetes distinction — the "use grace periods" bullet is the only overlap, one
  line of general advice, not an audit. The openclaw-superpowers `secrets-hygiene` skill that also
  surfaces for rotation queries audits a different thing entirely (which *Claude Code skills* have access
  to secrets), not application credential propagation. Grounded in real, documented mechanics rather than
  invented ones: Kubernetes' own env-var-resolved-once-at-container-start vs. volume-mount-refreshed-on-sync
  behavior (confirmed via Microsoft's engineering playbook and a Huawei Cloud CCE guide, both naming the
  exact `secretKeyRef`-stays-stale / volume-gets-updated split), HashiCorp Vault's documented
  client-owns-lease-renewal model, and AWS Secrets Manager's documented alternating-users rotation
  template (the real fix for the no-overlap-window outage case) versus the single-user template's
  revoke-on-the-spot shape. Distinct from this pack's `secret-spill` (incident response for a credential
  that already *leaked*) and `cipher-guard` (data-at-rest encryption-key rotation, not operational
  auth credentials). Added `skills/rotation-guard/SKILL.md`, README skills-table row + decision-table row
  + intro paragraph (thirty-five → thirty-six), `examples/rotation-guard.md` (an RDS single-user rotation
  causing a partial-pod outage, diagnosed down to the missing connection-pool max-lifetime and the
  never-refreshed `secretKeyRef` env var, with a billing-key rotation about to repeat the same mistake).
  `python tools/validate.py` passes (36/36).
- [x] **`seat-guard` — SHIPPED (verified novel), seat/license-count enforcement drift.** Distinct from
  this pack's `proration-guard` (billing math on plan changes, not seat-limit enforcement). The prior
  pass had confirmed the concurrent-read race angle (two requests both read the seat count before either
  write lands) as likely novel via `securifyai.co` and a from-scratch fix PR at
  `github.com/impruthvi/saas-foundation`, but left the other two sub-angles unresolved. This pass closed
  both: **deactivation-still-counts** (a deactivated/suspended user keeps silently occupying a seat
  because the counter invite-time enforcement reads is never decremented by deactivation) — searched
  GitHub code search across ~600+ `SKILL.md` hits for seat/SCIM/deactivate terms plus claudskills.com/
  claudemarketplaces.com/skillselion.com; the closest hits
  (`AwesomeSalesforceSkills` → `skills/admin/experience-cloud-member-management/SKILL.md`,
  `dragonked2/alphacode` → `playbook/SKILL.md` §43.2.116) are an admin operational runbook for one's own
  org and a one-line mention inside a sprawling generic bug catalog, not a dedicated code-level audit —
  confirmed as a real, recurring, named complaint via Jira FE-5012, and GitLab/Pipedrive/Docketwise/
  Kayako support docs all describing exactly this discrepancy independently. **SCIM/JIT-provisioning
  bypass** (a new user provisioned via SSO JIT or SCIM auto-provisioning never runs the seat check that
  only lives in the manual "invite user" path) — no skill or marketplace listing addresses this; closest
  hits (a Clerk orgs skill, `dragonked2/alphacode` §43.2.280) cover SCIM *authorization/tenant-binding*,
  not seat-count enforcement. Verified as real, documented mechanics via Scalekit's own vendor cookbook
  ("Enforce seat limits with SCIM provisioning," stating plainly that "the provisioning protocol doesn't
  check licence counts, so the customer's identity provider can push users past the plan limit") and
  Clockify's SCIM error docs independently corroborating seats running out during SCIM sync. All three
  sub-angles — race, deactivation, SCIM/JIT — bundled into one `seat-guard` skill rather than three
  separate skills, since they're three ways the same single "seat count" invariant can drift, which
  matches how this pack's other `*-guard` skills group related failure modes of one invariant (e.g.
  `cipher-guard` bundling uniqueness-check drift + key-rotation correctness + KMS policy scope). Added
  `skills/seat-guard/SKILL.md`, README skills-table row + decision-table row + intro paragraph (thirty-six
  → thirty-seven, plus fixing a stale "thirty-five" left over from an earlier count-bump miss),
  `examples/seat-guard.md` (an org over its 25-seat limit, diagnosed to a disconnected billing counter
  that deactivation never touches plus a freshly-added Okta SCIM path with zero seat enforcement at all).
  `python tools/validate.py` passes (37/37).

## `restore-guard` — SHIPPED (2026-10-23, verified novel); one more fresh lead found and parked

Git hygiene check first: clean clone, local `main` already matched `origin/main` (no detached-HEAD
repair needed). Since the 2026-10-20 note left no concrete unresearched leads (the handoff list had
already been exhausted into two SHIPPED skills), this run researched four fresh, not-yet-tried candidates
from scratch rather than picking up a stale thread:

- [x] **Soft-delete/trash restore completeness — SHIPPED as `restore-guard` (verified novel).** The
  mirror image of this pack's `erasure-guard`: when a soft-deleted record is restored within its grace
  period, does the restore path actually reverse everything the delete triggered — cascading soft-delete
  of child records, an explicit search-index delete/exclusion, a negative-cache "gone" tombstone with its
  own TTL, cross-service soft-delete fan-out — or does restore just flip the parent's `deleted_at` flag
  back while the rest of the system has already moved on. Also covers a distinct timing bug rather than a
  missing call: a scheduled hard-delete/purge job enqueued at delete time with a fixed fire time that
  restore never cancels, which can still permanently destroy the just-restored row on schedule unless the
  job itself re-checks live state at execution time. Searched GitHub code search across six query variants
  combining soft-delete/restore/undelete with cascading, search-index, CDN, grace-period, and purge-race
  terms; the only hits were generic ORM/framework trash-and-restore *library features* (CakePHP's `Trash`
  behavior, Rails' `paranoia` gem) that implement cascading restore as a feature to build, not a correctness
  audit of an existing implementation, and none mention search-index re-indexing, cache-tombstone clearing,
  or the purge-job race at all. Distinct from `erasure-guard` (that skill verifies deletion reaches
  everywhere; this one verifies the way *back* does, once a restore feature exists), `overwrite-guard`
  (concurrent-edit conflicts on a never-deleted record, not a delete-then-restore cycle), and `tombstone`
  (removing unused *code*, not restoring live *data*). Added `skills/restore-guard/SKILL.md`, README
  skills-table row + decision-table row + intro paragraph (thirty-seven → thirty-eight, including a stale
  "thirty-seven" in the install-tip paragraph the 2026-10-20 count-bump missed), `examples/restore-guard.md`
  (a 30-day workspace trash where a real user report — "search still shows it as deleted after restore" —
  leads to finding that *and* two unreported gaps: child documents' cascading soft-delete never reversed,
  and a purge job that would have hard-deleted the restored workspace in 30 days regardless). `python
  tools/validate.py` passes (38/38).
- [x] **Bulk "select-all-across-pages" admin action correctness — NOVEL, found but not shipped this
  round; next run's first candidate.** An admin UI's "select all N matching filter" (not just the visible
  page) that performs a bulk action (delete/export/reassign) raises two separable backend questions: does
  execution re-resolve the filter at action time (risking the matched set changing between selection and
  execution) or snapshot the ID set at selection time, and is there any bound/confirmation gate on how many
  rows "select all" can actually touch in one action. Searched GitHub code search broadly (500+ raw hits,
  narrowed via tighter queries); every match was a frontend table/UI-component skill (shadcn data-tables,
  generic "bulk actions" UI patterns) addressing the checkbox/toolbar UX, not backend re-resolution,
  pagination-cursor drift under concurrent writes, or a row-count safety bound. Not picked up this round
  only because one ship per day is this pack's own rule, not because it's weaker than `restore-guard` —
  treat it as pre-verified novel, not a fresh research task, for whoever picks it up next.
- [x] **Multi-tab/multi-device autosave collision — REJECTED, substantially covered.** Distinct from
  `overwrite-guard` in theory (autosave has no explicit "Save" button, no user-visible conflict moment, and
  often runs a different debounced-PATCH code path than an explicit save), but two independent skills
  already close that gap in practice: `Manoj-11-Dahal/try-Skills` →
  `.../browser-cross-tab-form-state-conflict/SKILL.md` tests exactly this ("two isolated tabs making
  edits... compare conflict detection, save order, and recovery") and names autosave by name in its
  checklist; `JanKrajewskiIT/claude` → `document-autosave/SKILL.md` states the needed fix directly ("Send
  the last acknowledged revision with each write," "Treat revision mismatch as a conflict, not a transient
  retry," "Do not allow stale responses to overwrite newer local edits"). Together they cover both the
  audit framing and the fix shape. Closed as covered.
- [x] **Usage-metering event double-count/drop for metered billing — REJECTED, covered (borderline).**
  Distinct from this pack's `proration-guard` (billing *math* on plan changes, not event-ingestion
  correctness), but `geminimir/meterguard` names the exact failure modes and fixes directly — deterministic
  idempotency-key dedup ("Every usage event stored with deterministic idempotency key... Send same event
  twice — counts once") and a late-event watermark/replay window (48h lateness + reconciliation epsilon
  check). It's a build-shaped integration guide rather than an audit of an *existing* pipeline and doesn't
  name Kafka-rebalance or crashed-aggregator specifics, but between `meterguard`, `stripemeter`, and
  flowglad's idempotency-key guidance the core double-count/drop failure modes are named and solved by name
  across multiple independent sources. Closer to saturated than the autosave candidate. Closed as covered.

No other skill files touched this round — one shipped, one new fresh lead parked above, two rejected.

Follow-up for the next run: pick up **bulk "select-all-across-pages" admin action correctness** first
(pre-verified novel above, no re-research needed) — scope it as one skill covering both the filter
re-resolution/snapshot question and the row-count safety bound, the same way `seat-guard` bundled three
related drift modes of one invariant into a single skill rather than three.

## `selectall-guard` — SHIPPED (2026-10-24, verified novel)

Git hygiene check first: clean clone, local `main` already matched `origin/main` (no detached-HEAD
repair needed).

- [x] **Bulk "select-all-across-pages" admin action correctness — SHIPPED as `selectall-guard`.** Picked
  up the pre-verified-novel lead the 2026-10-23 run parked. Ran one confirmatory round before writing
  (two targeted web searches for SKILL.md / skill-registry content on filter re-resolution vs.
  ID-snapshot semantics and row-count bounds for "select all matching" bulk actions) rather than trusting
  the prior pass blind — turned up only generic admin-UI bulk-action docs (Goodnotes, CVAT, PatternFly,
  a GitLab design issue) and one close-but-different GitLab MR (bulk AI vulnerability actions resolving
  scope server-side via an empty-ID-array convention) — no dedicated SKILL.md or skill-registry entry
  audits the snapshot-vs-re-resolve question or the row-count-bound question for an *existing*
  implementation. Confirms the 2026-10-23 finding; shipped. Scoped as one skill bundling both
  sub-questions (which contract the backend implements, and whether there's an observable cap), the same
  grouping pattern as `seat-guard`/`cipher-guard`/`restore-guard` bundling related drift modes of one
  invariant rather than splitting into separate skills. Distinct from `job-warden` (correctness of
  processing a queued item once scope is fixed, not how scope gets fixed), `backfill-pilot` (engineer-run
  one-off migration, not a user-triggered admin feature with no dry-run), `blast-guard` (audience
  targeting for irreversible sends specifically, not bulk admin actions generally), and `overwrite-guard`
  (single-record concurrent edits, no bulk selection). Added `skills/selectall-guard/SKILL.md`, README
  skills-table row + decision-table row + intro paragraph (thirty-eight → thirty-nine, in both the intro
  sentence and the install-tip paragraph), `examples/selectall-guard.md` (a queued ticket-reassignment
  bulk action that re-resolves an open "status=unassigned, team=billing" filter through a real multi-minute
  queue delay with no row-count divergence check, silently reassigning tickets the admin never approved).
  `python tools/validate.py` passes (`OK: 39 skills valid and consistent with README.`).

No other skill files touched this round.

Follow-up for the next run: no concrete unresearched lead parked this time — the next run should do a
fresh novelty sweep from scratch (per the pattern noted in the 2026-10-19 round: this pack's remaining
edge is in narrow "audit an existing implementation for a particular lifecycle bug" framings, not broad
infra/protocol topics) rather than assuming nothing is left.

## Maintenance pass (2026-10-25): fresh novelty sweep, one promising lead parked, four rejected

Git hygiene check first: clean clone, local `main` already matched `origin/main` (no detached-HEAD
repair needed). `python tools/validate.py` passes (`OK: 39 skills valid and consistent with README.`)
both before and after this pass — no skill files touched. Picked up the 2026-10-24 note's instruction
to do a fresh sweep from scratch rather than assume nothing is left. Used targeted GitHub code search
(`filename:SKILL.md` + specific terms, several query variants per candidate, reading actual matched
content rather than titles) across five fresh, not-yet-tried candidates:

- [x] **Inventory/stock oversell race (concurrent purchase exceeding limited stock) — REJECTED,
  saturated.** Extremely densely covered: a "race-condition" hunting `SKILL.md` mirrored across at
  least a dozen pentest-skill repos (`yaklang/hack-skills`, `ersinkoc/security-check`,
  `1arley/ornn` → `race-condition-hunter`, `hiepck/ARTEX-EN` → `hunt-race-conditions`, others) names
  "Inventory Oversell" as a dedicated named subsection with its own detection method. `Rzyfront/Vendix`
  ships a real production fix pattern (`skills/vendix-inventory-stock/SKILL.md`: reserve-on-add inside
  the same transaction, `allow_negative_available: false` atomic claim). Closed as covered.
- [x] **Referral/reward clawback on reversal (referrer credited and spends the reward before the
  referred user's purchase is refunded/reversed) — REJECTED, covered.** `0disoft/mustflow` →
  `.mustflow/skills/referral-incentive-integrity-review/SKILL.md` names this almost exactly in its own
  trigger description — "pending, vested, or reversed rewards... self-referral and reward farming
  controls... refundable purchases." `finsilabs/awesome-ecommerce-skills` →
  `skills/customer-crm/referral-program/SKILL.md` and `referral-viral-loops/SKILL.md` state the
  structural fix directly ("Wait 7–14 days after the referee's order before granting the referrer
  reward — this prevents rewards on returned orders"). `H-mmer/pentest-agents` →
  `agent-business-logic/SKILL.md` lists "Referral / invite abuse" (self-referral, circular chains,
  payment without delivery) as a named business-logic exploit class. Closed as covered.
- [x] **Support/admin impersonation ("login as user") session-lifecycle audit (scope limits, audit
  logging, termination conditions, token identity leakage) — REJECTED, covered.** `AS-FOSS/aegis-skills`
  → `skills/code/authz-access-control/SKILL.md` has a dedicated "Delegation & Impersonation" section
  naming the exact checks this candidate proposed almost verbatim: "verify scope limits (time-boxed,
  reason captured), immutable audit log entry with actor+target+reason, termination on password change,
  and no token minting that drops the original actor identity." `0disoft/mustflow` →
  `session-management-review/SKILL.md` covers session-id reissuance at impersonation start/end;
  `bedkillerspacex-boop/codex-skill-library` → `account-takeover-methodology/SKILL.md` lists "Support /
  impersonation: Overbroad 'login as user' without audit" as a named ATO vector. Closed as covered.
- [x] **Trial/plan-tier expiration enforcement drift (trial-to-paid/expired transition not atomic, a
  downgrade leaving premium access reachable via a direct endpoint) — REJECTED, covered.**
  `jschulte/claude-plugins` → `codebase-audit/skills/health-audit-domain/SKILL.md` names this nearly
  word-for-word as a dedicated checklist: "Can a user on a free plan access premium features by knowing
  the right URL or API endpoint?", "What happens at the exact moment of expiration? Is there a grace
  period? Is the transition from trial to paid/expired handled atomically?", "When they downgrade, is
  access to premium features revoked? Is data created with premium features handled correctly after
  downgrade?" Closed as covered.
- [x] **Terms-of-service / privacy-policy version re-acceptance gating — SHIPPED as `reaccept-guard`.**
  Did the confirmatory pass this item asked for before shipping: two fresh search variants
  (`SKILL.md` + "terms of service"/"privacy policy" re-acceptance enforcement; `must_reaccept`/
  `tos_version`/`policy_version` enforcement/bypass) turned up no existing skill auditing this —
  only generic skill-safety-review tooling and a general compliance-checker skill unrelated to
  re-acceptance enforcement, confirming the prior round's six-variant search. Grounded in real
  platform mechanics rather than the search-emptiness alone: Google's Zero Touch Enrollment API
  returns a 403 with a `latestTosAccepted: false` field for stale-ToS API requests (confirming
  API-level enforcement is a real, named mechanic, not a hypothetical edge case), and a USPTO
  patent filing on EULA-version-aware gateways plus independent practitioner guidance both make
  the same point this skill's Step 1 opens with: client-side version checks are tamperable and
  bypassable, so the server must enforce the decision per-request, independent of which client
  asked. Shipped `skills/reaccept-guard/SKILL.md` + `examples/reaccept-guard.md`, wired into both
  README tables and the Examples list; `tools/validate.py` passes (40 skills).

Shipped `reaccept-guard` this round (see above) — the one parked lead from the prior round, after its
confirmatory pass and real-world grounding. No other backlog items are currently open.

Follow-up for the next run: no parked candidate exists right now, so the next run needs to research and
log 3-5 fresh, specific candidates before picking one to ship (per this pack's own process) rather than
inventing busywork. Leads worth checking first since they're adjacent to what's already in the pack but
not yet confirmed covered or novel: (1) feature-flag/experiment kill-switch audit — does flipping a flag
off in an incident actually stop every code path that reads it (cached flag evaluations, a client SDK that
only polls periodically, a server that read the flag once at boot) rather than just the admin-panel toggle
looking flipped; (2) webhook-delivery idempotency/replay audit — distinct from `job-warden` (internal
cron/queue correctness) and `rotation-guard` (credential propagation), this would be about whether a
receiving endpoint actually dedupes a third-party webhook provider's at-least-once redelivery instead of
double-processing a payment-captured or order-shipped event; (3) multi-currency/rounding-drift audit for
money math across conversion, tax, and refund paths — distinct from `proration-guard` (plan-change policy
correctness) and `cipher-guard`/`seat-guard` (not money-math at all). All three need the same novelty
research `reaccept-guard` got before being shipped, not assumed clear.

## Drift audit — round 10 (2026-10-27): the five post-round-9 skills, plus the three 10-25 leads closed

Git hygiene check first: clean clone, local `main` already matched `origin/main`. `python tools/validate.py`
passes (`OK: 40 skills valid and consistent with README.`) both before and after this pass — no skill
files touched.

**The three parked leads from the 2026-10-25 note — all REJECTED, saturated.** Used targeted GitHub code
search (`filename:SKILL.md` + specific terms, multiple query variants, reading actual matched content)
before touching any of them, per this pack's own bar:

- [x] **Feature-flag/experiment kill-switch audit (does flipping a flag off in an incident actually stop
  every code path, not just the admin-panel toggle) — REJECTED, saturated.** `JantonioFC/skillsbank` →
  `skills/flag-cleanup/SKILL.md` ships a dedicated `kill_switch_audit.py` script literally named for this.
  `cosmix/loom` → `skills/loom-feature-flags/SKILL.md` covers the exact cached-evaluation mechanic this
  candidate proposed almost verbatim: "Never make the availability of a feature depend on the availability
  of the flag service... Cache aggressively (in-memory + local file/Redis), refresh in the background,
  tolerate staleness... Propagate activation fast (pub/sub/streaming), but the hot-path read is always
  local." `SkillMedev/skills` → `skills/feature-flags/SKILL.md` adds the client-SDK-polling angle directly
  ("Cache evaluations locally and stream updates; a per-request network call... puts the flag provider on
  your critical path") plus a named "re-test a kill switch quarterly" discipline. Closed as covered.
- [x] **Webhook-delivery idempotency/replay audit for a receiving endpoint — REJECTED, saturated.**
  Extremely densely covered, more so than almost anything else checked in this pack's history:
  `hookdeck/webhook-skills` ships a whole dedicated `webhook-handler-patterns` skill with its own
  `references/idempotency.md` ("Dedupe retries and replays") and `references/handler-sequence.md`
  ("Verify first, parse second, handle idempotently third"), repeated per-provider across a dozen sibling
  skills in the same repo (`maxio-webhooks`, `twitter-webhooks`, `cronofy-webhooks`, `telnyx-webhooks`,
  etc). `sandeepmvl/rails-skills` → `skills/30-webhook-handling/SKILL.md` and `ericrisco/rsc-harness` →
  `skills/webhooks/SKILL.md` both describe themselves as exactly this candidate ("a provider-agnostic
  endpoint that proves pushed events are authentic and never processes one twice: raw-body HMAC, ~5-min
  replay window, idempotency on the event id, fast-ack-then-queue"). Closed as covered.
- [x] **Multi-currency/rounding-drift audit for money math across conversion, tax, and refund paths —
  REJECTED, saturated.** `Sir-chawakorn/sanook-cli` → `skills/money-decimal-arithmetic/SKILL.md` covers
  this almost exactly: "per-currency exponents (ISO 4217), explicit rounding modes (banker's vs half-up),
  largest-remainder allocation that sums exactly, FX triangulation... to eliminate float drift and
  off-by-a-penny totals." `codekit-labs/testctl` → `skills/money-guard/SKILL.md` is explicitly a drift-audit
  framing: "Generate tests that protect money math — correct rounding to each currency's precision, no
  floating-point drift, multi-currency conversion, and totals that reconcile." `open-mercato/open-mercato`'s
  security-report skill and several CFO/ecom-tax skills independently name the same reconciliation angle
  (conversion/tax/refund rounding drift). Closed as covered.

**Three fresh candidates tried this round — all REJECTED, saturated**, continuing the sweep rather than
re-treading the closed three above:

- [x] **Outbound webhook delivery reliability (retry schedule, ordering guarantees, dead-letter/replay for
  *your* customers subscribing to events you send) — REJECTED, saturated.** Distinct in principle from the
  receiving-side webhook skills above, but just as densely covered from the sending side:
  `samber/developer-platform-skills` → `skills/webhook-platform-design/SKILL.md` ("this skill applies
  [retry/idempotency] ideas to outbound delivery only"), `alexpate/devtool-skills` →
  `skills/webhook-delivery/SKILL.md`, `nahid-sparktales/agent-dispatcher` → `skills/backend/webhooks/SKILL.md`
  ("Outbound: contract published, deliveries signed, backoff bounded, destination URL restricted"), and
  `cosmix/loom` → `skills/loom-webhooks/SKILL.md` (per-endpoint delivery/DLQ/retry metrics, customer-facing
  delivery log + self-serve replay) all name this exact scope. Closed as covered.
- [x] **Cursor/keyset-pagination drift audit (does a paginated listing API skip or duplicate rows when the
  underlying table changes between page fetches) — REJECTED, saturated.** `loqmanali/backend-ai-skills-pack`
  → `skills/cursor-pagination/SKILL.md` is a dedicated skill on exactly this ("paginating a large or
  fast-changing table... keyset pagination walks the table by remembering the last row seen, not by
  counting"). Closed as covered.
- [x] **Multi-tenant resource quota / noisy-neighbor isolation audit (per-tenant compute/storage quota
  enforcement, as distinct from this pack's `seat-guard` which is user-count licensing, not resource
  quotas) — REJECTED, saturated.** At least three dedicated skills across two repos cover this directly:
  `syntedge/syntedge-skills` → `skills/multi-tenant-isolation/SKILL.md` ("Isolate tenants at data, compute,
  and noisy-neighbor layers with measurable guarantees"), `sickn33/agentic-awesome-skills` →
  `skills/saas-multi-tenant/SKILL.md` and `skills/multi-tenant-llm-hosting/SKILL.md` (tenant isolation,
  quotas, noisy-neighbor protection, billing attribution). Closed as covered.

One more candidate tried and also rejected, surfaced while reading pentest-skill hits during the above
searches:

- [x] **Single-use promo/coupon code redemption race (concurrent redemption exceeding max-uses, or two
  codes silently stacking when policy says only one should apply) — REJECTED, saturated.** Same shape as
  `seat-guard`'s Step 1 race applied to coupons instead of seats, but already covered on both the
  security-testing side (`elementalsouls/Claude-BugHunter`, `uphiago/recon-skills`, and several forks all
  ship `hunt-race-condition/SKILL.md` naming "coupon double-redemption" and "gift-card double-spend" as
  dedicated named attack classes with working PoCs) and the build side (`finsilabs/awesome-ecommerce-skills`
  → `skills/pricing-promotions/coupon-management/SKILL.md`: "Validate at order creation, not just at
  cart — re-check coupon validity (expiry, usage limits) when the order is actually placed to handle race
  conditions"). Closed as covered.

**No new-skill candidate survived novelty research this round** — seven tried, seven rejected. Rather than
force a 41st skill into already-crowded territory or invent busywork, did the standing fallback instead:
drift-audited the five skills shipped since drift-audit round 9 (2026-10-15, which covered `cipher-guard`)
that had never had a dedicated fact-verification pass — `rotation-guard` (2026-10-21), `seat-guard`
(2026-10-22), `restore-guard` (2026-10-23), `selectall-guard` (2026-10-24), and `reaccept-guard`
(2026-10-26). Read all five `SKILL.md` files in full, identified every externally-checkable claim, and
verified each via `WebSearch`:

- `rotation-guard`: re-verified the AWS Secrets Manager "alternating users" rotation strategy claim against
  AWS's own current docs (`docs.aws.amazon.com/secretsmanager/.../tutorials_rotation-alternating.html` and
  `.../rotation-strategy.html`) — confirmed accurate: two cloned DB users take turns being "current" so the
  previous one stays valid through the rotation cycle, exactly as described. Re-verified the Kubernetes
  `Secret`-as-volume-vs-env-var claim, including the specific `subPath` exception — confirmed via multiple
  independent current sources (a Kubernetes Discuss thread, a GitLab merge request quoting the upstream
  docs, `ahmet.im`'s writeup on `configMapAndSecretChangeDetectionStrategy`, the Secrets Store CSI driver's
  own "Known Limitations" page): a `subPath`-mounted Secret never receives live updates regardless of
  change-detection strategy, while a whole-volume mount updates after the kubelet sync period plus cache
  propagation delay (documented as up to roughly a minute or two) — matching the skill's claim exactly. No
  drift.
- `seat-guard`: re-verified the "Jira, Pipedrive, Docketwise, Kayako, and GitLab have all tracked exactly
  this discrepancy" claim company-by-company rather than taking the original research's word for it. Jira:
  confirmed, `jira.atlassian.com/browse/FE-5012` ("Deactivated JIRA users still count against license
  seats") still resolves and matches. Pipedrive: confirmed via Pipedrive's own support docs plus a Pipedrive
  staff reply in their community forum — a deactivated user's seat "remains active—and billable—unless it's
  manually removed." Docketwise: confirmed via their support center — "A deactivated user still occupies a
  user license. The only way to free that license is to delete the user." Kayako: confirmed the discrepancy
  exists but as an internal *contradiction* rather than one clean statement — one Kayako Classic article
  says disabled staff don't count against the seat limit, another says the account "will still be charged
  continuously for the number of seats you have purchased" regardless. GitLab: the nuance runs the other
  way from a flat restatement — GitLab's current docs say a deactivated user does *not* count toward
  current billable seats, but does count toward the historical peak used for overage/true-up billing, so
  the discrepancy is real but shows up at true-up time rather than as an immediately-occupied seat. Verdict:
  no fabrication — all five companies do have a real, documented version of "deactivation doesn't cleanly
  free what you'd expect it to," though GitLab's and Kayako's versions are more nuanced than the skill's
  one-line summary suggests. Not drift serious enough to require an edit (the skill's own Step 2 already
  frames this as "a well-documented, recurring SaaS complaint," not a claim about any one company's exact
  mechanism), but noted here for the next audit pass to watch rather than re-verify from scratch. Also
  re-verified the PatternFly/shadcn admin-table claim from `selectall-guard` (see below) turned up while
  researching this — unrelated skill, checked opportunistically.
- `restore-guard`: read in full — carries no named external citations (company names, issue numbers, specs)
  to verify, only generic soft-delete/cascade engineering reasoning. Nothing to check against an external
  source; no drift possible in the sense this audit checks for.
- `selectall-guard`: re-verified the "PatternFly, shadcn, and most admin-table components ship the
  pagination-aware select-all toggle for free" claim. PatternFly: confirmed directly — its current "bulk
  selection" pattern (`v5-archive.patternfly.org/patterns/bulk-selection`) documents exactly this: a bulk
  selector with "Select none," "Select page," and "Select all" (cross-page) options, with item-selected text
  reflecting the cross-page total. shadcn: not independently confirmable as a single doc page (shadcn/ui is
  a composable set of primitives over Radix + TanStack Table, not a single component with its own select-all
  spec), but the broader claim holds via Elastic EUI's table-selection pattern and a Retool community thread
  describing the same cross-page-selection problem space third-party widgets commonly ship for. No drift —
  the core claim (PatternFly ships this) is directly confirmed; the shadcn mention is a reasonable
  generalization, not a specific fabricated citation.
- `reaccept-guard`: shipped only yesterday (2026-10-26) with its own fresh grounding pass already done at
  ship time (Google Zero Touch Enrollment API's `latestTosAccepted` 403 field, a USPTO patent filing, and
  independent practitioner guidance) — skipped re-verification this round since nothing has had time to go
  stale; it's next in line for round 11 once some time has passed.

No fixes needed in any of the five skills — every externally-checkable claim held up against current
source text, and the one claim with real nuance (`seat-guard`'s five-company list) is still substantively
accurate, just imprecise at the edges in a way the skill's own wording already allows for.

Follow-up for the next run: no candidate parked from a confirmatory pass — the next run needs a fresh
novelty sweep from scratch rather than assuming anything above is still open (all seven tried this round are
now closed). One promising, not-yet-fully-researched thread surfaced while reading SRE/review skills during
this round's searches, worth trying first: **distributed/per-instance rate-limit enforcement drift** — does
a rate limit actually cap aggregate usage across a horizontally-scaled fleet, or does an in-memory
per-instance counter quietly let N× the intended limit through because nothing coordinates across
instances? Found only a single passing checklist line in `dancovello/golf-platform` →
`.claude/skills/sre-review/SKILL.md` ("Review rate limiting config... is it per-instance or distributed?")
and generic rate-limiter *build* skills (token-bucket/GCRA algorithm references) — no dedicated code-level
audit skill with file:line findings and a BLOCK/CAUTION/SAFE verdict shape, the form this pack's skills
take. Needs the same multi-variant confirmatory search `reaccept-guard` got before being trusted as novel,
not assumed clear from one hit. If that also turns out saturated, the next fallback is drift-auditing
`reaccept-guard` once round 11 is due, or trying a fresh sweep entirely outside this pack's current
territory (its first 40 skills now cover an unusually wide swath of SaaS/distributed-systems correctness
bugs — a genuinely fresh angle may need to come from outside that genre rather than one more adjacent
variant of it).

## `throttle-guard` — SHIPPED (2026-10-28, verified novel)

Picked up the 2026-10-27 note's parked lead — distributed/per-instance rate-limit enforcement drift —
and ran it through the same confirmatory bar `reaccept-guard` got rather than trusting the single prior
hit. Git hygiene check first: clean clone, local `main` already matched `origin/main`. `python
tools/validate.py` passed (`OK: 40 skills valid and consistent with README.`) before this pass; no
skill files were touched before the new one was added.

Research: six query variants via `WebSearch` and `mcp__github__search_code` (`filename:SKILL.md` +
"per-instance"/"rate limit", "horizontally"/"distributed rate limit", "per replica"/"per pod"/"per
worker" + review, "N times the intended"/"exceed the intended limit", "BLOCK"/"CAUTION"/"SAFE" +
"rate limit", plus direct fetches of the most plausible hits). Consistent finding across all of them:
**build-side guidance for this exact mechanic is everywhere** — `j4flmao/agent-skills` →
`skills/backend/universal/rate-limiting/SKILL.md` states the core fact almost verbatim ("In-process
limiters multiply the effective limit by the instance count"; anti-pattern table: "Per-instance
in-memory limits for paid quotas" → fix "Shared store or gateway") — but every hit checked is
implementation/design guidance (how to build a rate limiter correctly, output artifact "middleware/gateway
code or config"), never a dedicated **audit** skill that reviews *existing* code for this drift with
file:line evidence and a BLOCK/CAUTION/SAFE verdict, the shape this pack's `-guard` skills take. Fetched
`google/skills` → `google-cloud-waf-reliability/SKILL.md` directly on the chance a reliability-audit
skill already covered it — confirmed it mentions rate limiting only once, in a generic validation
checklist, with no per-instance/distributed-state angle at all. No existing skill reviews deployed code
for: (1) an in-memory counter silently becoming a per-instance limit once a service scales to N
instances, (2) a "shared" store whose check-then-increment is a non-atomic read-compare-write that
reopens the same race one layer out, or (3) a limit enforced on one entry point that a second path
(internal call, background worker, newer endpoint) never goes through. Closed as genuinely novel.

Shipped `skills/throttle-guard/SKILL.md` + `examples/throttle-guard.md`, wired into both README tables
and the Examples list; bumped the two stale "forty"/"thirty-nine" skill-count mentions in `README.md`'s
intro and install tip to "forty-one" while touching the file for the new entry anyway (same drift class
the 2026-09-20 note already fixed once — noting here in case it recurs and needs a structural fix rather
than a one-off edit each time). `python tools/validate.py` now passes (`OK: 41 skills valid and
consistent with README.`).

Follow-up for the next run: no candidate parked from a confirmatory pass — the next run needs a fresh
novelty sweep from scratch. `reaccept-guard` (shipped 2026-10-26) and `throttle-guard` (this entry) are
both now due for a drift-audit fact-check pass once some time has passed, alongside whatever the next
drift-audit round picks up from between them.

## `quote-guard` — SHIPPED (2026-10-29, verified novel)

Fresh novelty sweep from scratch, as the 2026-10-28 note required. Git hygiene first: local `main`
was detached at the previous run's already-pushed `throttle-guard` commit (`8b8bc80` matched
`origin/main`) — reattached `main` to it via `git checkout main && git reset --hard origin/main`,
no data lost, nothing to re-push. `python tools/validate.py` passed (`OK: 41 skills valid and
consistent with README.`) before this pass.

Tried several angles before landing on one: a RAG/vector-embedding re-indexing staleness audit
(dead — `WebSearch` found dedicated coverage: a "Freshness Framework"-style skill in
`jamelna-apps/claude-dash` tracking file mtimes/git commits to choose incremental vs. full reindex,
and a dedicated `adt-rag-drift` skill counting stale chunks and recommending rebuilds); an
LLM structured-output/tool-call schema-validation-drift audit (not conclusively covered but also not
clearly a "real recurring production incident" in this pack's grounding style — more a meta/tooling
concern than an app-code correctness bug class, so set aside rather than force-grounded); and a
double-booking/overlapping-reservation race audit, which on `mcp__github__search_code` for
`filename:SKILL.md "double booking" OR "overlapping reservation"` turned up exactly one hit
(`dilusha-c/supipi-guest-house` → a single checklist line in a one-off guest-house project's security
audit, not a reusable dedicated skill) — but is the same check-then-act concurrency shape already
closed as covered under the inventory-oversell and coupon-redemption race entries above (`hunt-race-
condition`-style skills across `elementalsouls/Claude-BugHunter`, `uphiago/recon-skills`, and forks
name exactly this race-condition class generically), so didn't chase it further.

Landed on **checkout/cart price integrity between quote and capture**: does the amount a customer saw
and agreed to match the amount actually captured, once anything (a catalog price edit, a promo window
closing, a coupon re-validated differently, a tax/inventory recompute) gets a chance to land in the
gap between them — a gap that's seconds in an instant checkout but hours or months for a pre-order,
backorder, BNPL installment, or trial-to-paid conversion. Confirmatory search: `mcp__github__search_code`
for `filename:SKILL.md "stale price" OR "price drift" checkout` (1 hit, an e-commerce "pricing-and-
channels" skill in `tensology/decisionsai` whose content doesn't actually mention price drift or stale
pricing when fetched directly — a loose keyword match, not real coverage) and `filename:SKILL.md
"authorize" "capture" amount mismatch price` (825 hits, but every one checked is either a security/
business-logic-tampering angle — `UnboundCompute/security-agent-skills` →
`auditing-payment-callback-and-amount-integrity` audits attacker-forged payment *callbacks*, a trust-
boundary problem, not a legitimate system silently re-pricing its own flow — or unrelated red-team
"hunt-business-logic" skills that name "price manipulation" as an attacker-input class, not a
quote-to-capture drift audit). No existing skill reviews a codebase's own checkout/capture logic for
whether the captured amount still matches what the customer was shown, as the gap between quote and
charge widens. Closed as genuinely novel.

Grounded in two independently verified facts rather than invented plausibility: (1) *Kahn v. Walmart*
(7th Cir., No. 23-1751, 2024) — the Seventh Circuit reversed a dismissal and held that a receipt
showing the price actually charged does not, as a matter of law, cure the deception from an inaccurate
displayed price, confirmed via the Wisconsin Law Journal's docket listing and Today's General Counsel's
summary of Judge Hamilton's opinion; (2) Stripe's `PaymentIntents` capture API rejects an
`amount_to_capture` greater than the amount originally authorized (confirmed via `docs.stripe.com/api/
payment_intents/capture`), meaning a checkout flow that silently recomputes "today's real price" at
capture time can't just capture the higher number without its own explicit re-authorization handling.

Shipped `skills/quote-guard/SKILL.md` + `examples/quote-guard.md`, wired into both README tables and
the Examples list; bumped the "forty-one"/"41-skill" mentions in `README.md`'s intro and install tip to
"forty-two"/"42-skill" while touching the file for the new entry anyway. `python tools/validate.py`
now passes (`OK: 42 skills valid and consistent with README.`).

Follow-up for the next run: no candidate parked from a confirmatory pass — the next run needs a fresh
novelty sweep from scratch. The LLM structured-output/tool-call schema-drift thread set aside above is
worth a deeper look before discarding outright — it may just need a sharper, more concrete framing
(e.g. "does the app still validate a model's structured output against the current schema after a
prompt/model swap, or did validation get silently loosened") rather than the vague form tried this
round. `reaccept-guard` (2026-10-26), `throttle-guard` (2026-10-28), and `quote-guard` (this entry) are
all now due for a drift-audit fact-check pass once some time has passed.

## Maintenance pass (2026-10-30): two candidates researched and rejected, shipped a validator check instead

Git hygiene check first, and it mattered this time: the clone started with `main` detached two
commits behind `origin/main` (`8b8bc80` throttle-guard, `3801f1e` quote-guard were already pushed to
`origin/main` by the prior two runs, but the local `main` branch ref itself had never been moved
forward — a stale ref, not lost work). Fixed with `git checkout main && git merge --ff-only
origin/main`; nothing was re-pushed since `origin/main` already had both commits. `python
tools/validate.py` passed (`OK: 42 skills valid and consistent with README.`) before this pass.

Picked up the 2026-10-29 note's sharper framing of the LLM structured-output/tool-call schema-drift
thread — REJECTED, saturated. `WebSearch` plus three `mcp__github__search_code` variants
(`"structured output" schema drift validation`, `"tool call" schema mismatch validation silently`,
`"model swap" OR "swapping models" output validation`, `"prompt change" OR "model upgrade"
"validation" "silently" output`) all land on the same conclusion: this exact mechanic — pin golden
inputs, validate structured output against schema before/after a model/prompt swap, gate on
regression — is the explicit core of a dense cluster of `eval-driven-development` /
`llm-eval-harness` / `ai-evaluation-patterns` skills (e.g. `jacob-balslev/skill-graph` →
`eval-driven-development/SKILL.md`: "every model upgrade or vendor switch changes the system under
test and must be re-gated against the private suite"; a prompt-engineering skill: "Pin production
prompts to a specific model snapshot. Model upgrades silently shift behaviour, and your evals are the
only signal."; `SamoTech/skills-tree` → `json-schema-validation/SKILL.md` names "Schema drift: LLM
trained on old schema produces output matching old spec" as a named anti-pattern row with its own
fix). Closed as covered — this is build-side guidance as densely covered as `throttle-guard`'s
rate-limiting territory was before it found the audit-shaped gap, but no comparable audit-shaped gap
exists here: the eval-harness skills already are the audit mechanism (gate every model/prompt change
against a golden set), not just advice to build one.

Tried one more angle while in adjacent territory: **idempotency-key-reuse-with-a-different-payload**
(same key, different request body, server should 409 rather than silently serving the first response)
— REJECTED, saturated, including on the audit side this pack requires. `addyosmani/agent-skills` →
`api-and-interface-design/SKILL.md` and `agentsope/SkillAlchemy` → `agentsop-llm-tool-idempotency/
SKILL.md` cover the build-side fix almost verbatim ("Same key, different body is a client bug, and
must fail loudly"). Critically, the audit angle this pack's own bar requires is also already covered:
`briiirussell/cybersecurity-skills` → `business-logic-testing/SKILL.md` names the exact test
("Idempotency key scoped to the path, not the principal... Submit two different operations under one
key") and `sickn33/agentic-awesome-skills` → `hunt-race-condition/SKILL.md` covers the same bypass
technique — the same pattern that closed the coupon-redemption-race candidate in round 10 (a dedicated
pentest/hunt skill already names the attack). Closed as covered.

No new-skill candidate survived — two tried, two rejected, both for the same reason: skill-build
guidance for the mechanic exists everywhere, and unlike `throttle-guard`'s gap, the dedicated
audit-shaped version (gate-on-regression for the first; a named pentest technique for the second) also
already exists. Rather than force a weak 43rd skill, picked up the recurring prose-drift class
`throttle-guard` flagged on 2026-10-28 ("noting here in case it recurs and needs a structural fix
rather than a one-off edit each time") and the earlier 2026-09-20 fix of the same class: `README.md`'s
intro ("no 42-skill kitchen sink — forty-two that earn their place") and install tip ("copying all
forty-two at once") state the pack's size in prose, in both digit and word form, and nothing re-derives
either from the actual skill count — so it goes stale every time a skill is added or removed unless
whoever ships that skill remembers to grep for it by hand, which has already failed to happen at least
twice.

Added `validate_skill_count_mentions` to `tools/validate.py`: a `SKILL_COUNT_DIGIT` regex for the
`42-skill` form, a `SKILL_COUNT_WORD` regex plus a small `word_to_number` word-to-int helper (covering
one through ninety-nine) for the `forty-two` form, both scoped tightly to the two phrasings
("`N-skill`", "`copying all <word> at once`", "`<word> that earn their place`") that this drift class
has actually used, so it can't misfire on an unrelated number word elsewhere in the prose (e.g. the
install tip's own "start with one or two" skills advice). Verified it actually catches the drift, not
just that it passes today: temporarily rewrote both mentions to "41"/"forty-one" in a scratch copy,
confirmed `tools/validate.py` fails with a clear per-mention message naming the stale count, then
restored the real `README.md` and reran clean (`OK: 42 skills valid and consistent with README.`). No
skill files touched this round — this was a tooling-only change, following the same pattern as the
2026-09-09 (`examples/` consistency) and 2026-09-15 (decision-table drift) tooling entries above.

Follow-up for the next run: fresh novelty sweep from scratch — no candidate parked. `reaccept-guard`
(2026-10-26), `throttle-guard` (2026-10-28), and `quote-guard` (2026-10-29) remain due for a drift-audit
fact-check pass once more time has passed; four days (reaccept-guard) is still probably too soon to
expect anything to have gone stale, so that pass is better spent once a couple of weeks separate it
from ship time.

## Fresh novelty sweep (2026-10-31): five candidates researched and rejected, shipped a README prose-drift fix

`python tools/validate.py` passed (`OK: 42 skills valid and consistent with README.`) before this pass;
git was already on `main`, in sync with `origin/main`, nothing stashed or stale.

Five new-skill angles tried, all rejected as already covered elsewhere (checked via `WebSearch` and
`mcp__github__search_code` on `filename:SKILL.md`, not just a single-skill spot check):

1. **Multi-tenant row-level isolation audit (missing `tenant_id` filter on a tenant-owned table/query).**
   REJECTED — a dense, direct cluster already exists: `hainrixz/claude-db` → `db-multitenancy` flags
   exactly this (severity-rated missing/nullable tenant column, non-leading tenant_id index/PK), plus
   independent hits in `omer-metin/skills-for-antigravity`, `Eibon7/roastr-ai`, and
   `davila7/claude-code-templates`'s `saas-multi-tenant`. Not a thin keyword match — multiple
   dedicated, specific skills.
2. **Inbound webhook receiver audit (signature verification, duplicate/out-of-order delivery, replay).**
   REJECTED — extremely saturated on both the build side and, critically, the audit side this pack's bar
   requires: `affaan-m/ECC` → `production-audit` and its mirror `Fmarzochi/EGC` both ask "are webhook
   signatures verified… is each webhook idempotent… are replay, duplicate, and out-of-order delivery
   handled" verbatim as an audit checklist; `lroy-stack/ai-pod-store` → `audit-webhooks-idempotency` is a
   dedicated audit skill with the same severity framing this pack uses (CRITICAL/FAIL/WARN/PASS); several
   `*-security-audit` skills (`shopsys/shopsys`, `vulpy-io/vulpy-commerce-core`) name the identical
   CWE-tagged checklist. This is the same shape that killed earlier candidates — real audit coverage
   exists, not just build guidance.
3. **Currency rounding / allocation-remainder audit (float money, naive `total/n` splits, tax/discount
   allocation that doesn't sum to the total).** REJECTED — `adamentwistle/fable-skills` →
   `numerical-care`, `Sir-chawakorn/sanook-cli` → `money-decimal-arithmetic`, and
   `zakariaf/Flutter-Skills` → `value-objects-money-and-units` all state the exact rules (integer minor
   units, round once at the boundary, largest-remainder allocation, `sum(parts) == total` assertion) as
   both guidance and an explicit list of anti-patterns to catch reviewing existing code. A paid listing
   (`agensi.io` → "Repair Money Rounding Bugs") targets this almost exactly as an audit-and-fix skill,
   confirming it's a recognized-enough niche to already be commercialized.
4. **Offset-pagination drift under concurrent inserts/deletes (skipped/duplicated rows while paging).**
   REJECTED — the skipped-or-duplicated-under-concurrent-writes failure mode is named explicitly as the
   core anti-pattern in `klod68/littlerae` → `pagination-cursor-offset`, `oborchers/fractional-cto` →
   `response-design-and-pagination`, and generic REST-design skills, consistently paired with "use
   cursor/keyset instead" as the fix — dense build-side coverage of the exact failure this pack would
   have audited for.
5. **Feature-flag bucketing consistency (inconsistent hash/salt causing a user to flip between
   control/treatment across requests or services).** REJECTED — `cosmix/loom` → `loom-feature-flags`
   covers per-flag salting and bucketing-unit choice explicitly; `greenblacked/AI` →
   `release-strategy` states "ring assignment must be sticky… hash the user/tenant/session id, not the
   request" as a named anti-pattern; `zeroes-ones/Skills` → `growth-engineer` has an explicit AA-test
   audit step ("is it using consistent hashing? sticky across devices?") for exactly this regression.

No new skill survived. Rather than force a weak 43rd, found and fixed a real, independently-verified gap
instead: `README.md`'s intro paragraph carries a long "what survived the novelty filter" sentence
describing every surviving skill in prose — but checking it mechanically (does each skill's distinguishing
phrase from its own README table row actually appear in that paragraph) showed it stopped being updated
after `restore-guard` (`7052336`): the five skills shipped after it — `seat-guard`, `selectall-guard`,
`reaccept-guard`, `throttle-guard`, and `quote-guard` — were each added to the skills table and decision
table (which `tools/validate.py` checks) but never folded into the intro's prose summary (which nothing
mechanically checks). Fixed by appending matching clauses for all five, in the same "whether X actually Y
instead of Z" style as the rest of the paragraph, sourced from each skill's own README row so the wording
stays accurate. Verified every one of the 42 skills now has a matching phrase in the intro (not just the
five added) via a quick per-skill substring check, not just that the five gaps closed. `python
tools/validate.py` still passes (`OK: 42 skills valid and consistent with README.`) — this prose list
isn't mechanically checked, so the drift wasn't caught by CI; a cheap per-skill-slug check isn't feasible
since the paragraph deliberately describes skills by function, not by slug, so this needs a human/agent
read every few rounds rather than a validator rule. No skill files touched this round.

Follow-up for the next run: fresh novelty sweep from scratch — no candidate parked; the five rejected
above are now documented so they aren't re-researched from zero. Worth periodically re-running the
"does every skill's phrase appear in the intro paragraph" spot check by hand after a run of several
new-skill ships, since nothing automated catches it. `reaccept-guard`, `throttle-guard`, and `quote-guard`
are still the nearest due for a drift-audit fact-check pass once more time has passed.

## Novelty sweep + new skill (2026-11-01): recall-guard shipped

Git hygiene check first: `main` was already at `origin/main` (`6740cce`), clean working tree, no stale
ref this time. `python tools/validate.py` passed (`OK: 42 skills valid and consistent with README.`)
before this pass.

Tried one new-skill angle first — **support "login as" / admin impersonation session audit**
(does impersonation require a separate elevated/time-boxed session, log actor+target+reason, and stay
scoped so a support rep can't silently escalate or leak the target's private data) — REJECTED, covered.
A `claudskills.com` → `auth-isolation` skill already treats uncontrolled support impersonation as a
named failure mode (elevated sessions must expire quickly and be tied to actor/session/reason/scope,
background jobs acting as a user must declare it). More decisively, `trannhatbuilder/evvo-vapt-ai` →
`shield_engine/skills/support-override-and-backoffice-admin-abuse/SKILL.md` names the exact mechanic as
a dedicated hunt step ("The 'Impersonation' (Login-As) Trap": token leaking into browser storage,
impersonating up to a Super Admin, audit log attributing the action to the wrong actor) — the same kind
of dedicated pentest/hunt-skill match that has closed several earlier candidates in this log (e.g. the
idempotency-key-reuse rejection on 2026-10-30). Closed as covered, following that same precedent.

**Shipped `recall-guard` — verified novel.** The angle: does a message edit-for-everyone/unsend/
delete-for-everyone/recall feature actually reach every copy of the content it already made — a push
payload already sitting in the OS's own notification store, a webhook/search-index/export mirror the
retraction code never touches, a transport boundary (relayed email, a federated bridge) it can never
reach at all — and does the recall action itself check the right actor and enforce its promised time
window server-side rather than just in the client. Verified uncovered: `WebSearch` for an existing
"unsend"/"message recall"/"delete for everyone" audit skill turned up only functional send/delete
automation skills (Telegram/Feishu/Lark message-deletion tools, security-scanned for *their own*
behavior, not for auditing a product's recall feature) — no dedicated review-this-feature skill.
Targeted `gh api search/code` passes on `"unsend" "push notification" filename:SKILL.md`,
`"message recall" OR "delete for everyone" "search index" filename:SKILL.md`, and `"edit message"
"already delivered" filename:SKILL.md` returned no on-topic hits at all (7, 0, and 0 results,
respectively, none matching the actual mechanic). In-pack: `push-guard` audits token lifecycle (is the
token still valid/bound to the right account), not whether a payload already delivered through a valid
token can be un-shown; `stale-guard` proves an ongoing cache read path can't serve wrong data, not
whether a one-shot retraction action reaches every secondary copy; `erasure-guard` is account-deletion
reach, not single-message retraction. None of the three cover this.

Grounded in a real, named, dated vulnerability rather than a hypothetical: CVE-2026-28950, patched in
iOS 26.4.2 / iPadOS 26.4.2 and iOS 18.7.8 / iPadOS 18.7.8 (confirmed via TidBITS, Bitdefender's
HOTforSecurity, and multiple other outlets reporting the same patch and mechanism) — deleted and
disappearing Signal message content was recoverable from the iPhone's own notification database months
after the app had faithfully deleted it (and after the app itself had been uninstalled), because the OS
had already cached a full preview in a store the app doesn't control. This is exactly the "can't be
recalled, only avoided" failure mode `recall-guard`'s step 2 and step 4 ask the reviewer to separate out
from the fixable "should be updated but isn't" gaps (search index, webhook mirrors).

Shipped `skills/recall-guard/SKILL.md` + `examples/recall-guard.md`, wired into both README tables, the
Examples list, and the intro paragraph's "what survived the novelty filter" summary sentence; bumped the
"forty-two"/"42-skill" mentions in `README.md`'s intro and install tip to "forty-three"/"43-skill" in the
same pass. `python tools/validate.py` now passes (`OK: 43 skills valid and consistent with README.`).

Follow-up for the next run: no candidate parked from a confirmatory pass — fresh novelty sweep from
scratch next time. `recall-guard` is now also on the drift-audit rotation alongside `reaccept-guard`
(2026-10-26), `throttle-guard` (2026-10-28), and `quote-guard` (2026-10-29) for a fact-check pass once a
couple of weeks have passed — none of the four are due yet.

## Maintenance pass (2026-11-02): three new candidates researched and rejected; Boundaries cross-reference pass on the 9 post-2026-10-06 skills

Git hygiene check first, and it mattered: the clone started with `main` detached two commits
(`6740cce`, `a04950d` — the `recall-guard` ship and its README-intro follow-up) ahead of where local
`main` pointed, though both were already pushed to `origin/main` by the 2026-11-01 run — a stale local
branch ref, not lost or unpushed work. Fixed with `git checkout main && git merge --ff-only a04950d`;
`git push origin main` confirmed `origin/main` already had both commits ("Everything up-to-date"). Same
stale-ref class the 2026-10-30 note already hit once. `python tools/validate.py` passed (`OK: 43 skills
valid and consistent with README.`) before this pass; no skill files touched before the research below.

Three new-skill angles tried, all rejected as already covered by a dedicated existing skill — checked via
`WebSearch` and `gh api search/code` on `filename:SKILL.md`, with the closest hit fetched and read
directly rather than trusted from title/snippet alone, per this pack's own bar:

1. **JWT/session revocation-not-actually-revoking audit (does logging out or banning a user actually
   stop an already-issued stateless JWT from authenticating until it expires, or is there no jti
   blocklist/denylist checked on the hot path).** REJECTED, saturated. `bedkillerspacex-boop/
   codex-skill-library` → `jwt-jti-blocklist-design/SKILL.md` is a dedicated skill on exactly this
   mechanic (fetched and confirmed: "Stateless JWT cannot be revoked natively; a blocklist of `jti`...
   restores logout/compromise response at the cost of state," with its own "When To Use" line for
   "Access tokens with non-trivial TTL need explicit logout/revocation"). `sandeepmvl/rails-skills` →
   `10-rails-security-baseline/SKILL.md` covers the same ground for Rails specifically. On the audit
   side this pack's bar actually requires: `sickn33/agentic-awesome-skills` → `broken-authentication/
   SKILL.md` and several `jwt-attacks`/`api-auth-and-jwt-abuse` pentest skills name "logout doesn't
   invalidate the JWT" as a dedicated, named vulnerability class to hunt for — the same pattern that
   closed the idempotency-key-reuse candidate on 2026-10-30 (a named pentest technique already exists).
   Closed as covered on both the build and audit sides.
2. **Employee-offboarding credential-revocation cascade audit (SSO deprovisioning turns off directory
   access, but API keys, personal access tokens, OAuth grants to third-party services, and scheduled
   jobs running as that user silently keep working).** REJECTED, saturated. `bedkillerspacex-boop/
   codex-skill-library` → `python-scim-deprov/SKILL.md` is a direct, near-verbatim match (fetched and
   confirmed: its own pitfalls table names "Soft delete but refresh tokens still valid; only hide user
   in UI," its cascade checklist lists "Sessions, refresh tokens, API keys, personal access tokens...
   Outbound OAuth tokens to third parties... Scheduled jobs acting as user," and it explicitly scopes
   itself to "Auditing incomplete offboarding (ghost access)"). `cbrock84/headcount` →
   `identity-lifecycle-administration/SKILL.md` covers the same ground from the IT-ops process side
   ("API keys and tokens they created... the gap is almost always the systems identity management does
   not reach... Hunt specifically for orphaned accounts... credentials that have not been used in
   months but still work"). Closed as covered — this is the SCIM-deprovisioning-cascade audit this
   candidate proposed, already shipped under that name.
3. **Mobile in-app-purchase entitlement/refund-revocation audit (does a refunded or charged-back IAP
   actually revoke the entitlement it granted, and does "restore purchases" on a new device actually
   re-grant what StoreKit/Play Billing says the account owns).** REJECTED, saturated. `kensaurus/skills`
   → `audit-monetization-iap/SKILL.md` is a dedicated read-only audit skill on exactly this (fetched and
   confirmed: "Entitlements must match what users paid for: no unlock-without-pay, no paid-but-locked,
   no double-charge, no lost purchase on reinstall," explicitly scoped to "receipt validation, restore,
   lifecycle sync, grace periods, entitlements" for StoreKit 2/Play Billing/RevenueCat). `CharlesWiltgen/
   Axiom` → `axiom-audit-iap/SKILL.md` (mirrored into at least two other repos) is a second independent
   audit skill on the same mechanic, plus `dangnhh92/viber-harness` → `iap-entitlement/SKILL.md` and
   `j4flmao/agent-skills` → `in-app-purchase/SKILL.md` on the build side. Closed as covered.

No new skill survived — three tried, three rejected. Rather than force a weak 44th skill into
already-saturated territory, ran the standing fallback the 2026-10-04/10-06 entries established: a
**Boundaries cross-reference pass** on every skill shipped since the last one (2026-10-06, which covered
all 34 skills current at that time). Nine skills have shipped since: `cipher-guard` (10-11),
`rotation-guard` (10-21), `seat-guard` (10-22), `restore-guard` (10-23), `selectall-guard` (10-24),
`reaccept-guard` (10-26), `throttle-guard` (10-28), `quote-guard` (10-29), and `recall-guard` (11-01).
Read each one's `## Boundaries` section in full and checked two things per bullet: (1) every skill named
in a "not `X`'s territory" bullet actually exists under that exact slug in `skills/`, and (2) the
distinction drawn is still accurate against the referenced skill's current scope, not a stale
description of what it used to cover.

All clear — every cross-reference resolved to a real, correctly-described skill: `cipher-guard` →
`secret-spill`, `security-sweep`; `rotation-guard` → `secret-spill`, `cipher-guard`; `seat-guard` →
`proration-guard`; `restore-guard` → `erasure-guard`, `overwrite-guard`, `tombstone`; `selectall-guard`
→ `job-warden`, `backfill-pilot`, `blast-guard`, `overwrite-guard`; `reaccept-guard` → `consent-guard`,
`pref-guard`; `throttle-guard` → `backpressure-guard`, `storm-guard`; `quote-guard` → `proration-guard`;
`recall-guard` → `stale-guard`, `push-guard`, `erasure-guard`. No dangling references, no distinctions
that had gone stale. Nothing needed fixing.

Follow-up for the next run: no candidate parked — fresh novelty sweep from scratch next time; all three
tried this round are now closed and documented so they aren't re-researched from zero. `reaccept-guard`
(2026-10-26), `throttle-guard` (2026-10-28), `quote-guard` (2026-10-29), and `recall-guard` (2026-11-01)
remain the drift-audit fact-check queue once a couple of weeks have passed — still too soon for any of
them. The next Boundaries cross-reference pass is due once another batch of skills ships past
`recall-guard`.

