# Backlog

Real, finishable improvements — the daily agent picks ONE and ships it end-to-end.
Rules: check items off when done, add follow-ups you discover, never do two at once.
The pack's bar for NEW skills: the problem must be real and verified uncovered by
prominent existing skills (research first, write second) — see README.

## Pack quality
- [x] `examples/` directory: one short real transcript per skill showing the trigger firing and the output shape (start with git-rescue and migration-guard). Done for those two (`examples/git-rescue.md`, `examples/migration-guard.md`), linked from README. `examples/env-detective.md`, `examples/atomic-io.md`, `examples/tombstone.md`, `examples/skew-check.md`, `examples/job-warden.md`, and `examples/security-sweep.md` added since (see Skill improvements below). `examples/security-sweep.md` added 2026-08-06: an invoice-fetch + PDF-export diff walked through the skill's actual report format (severity-ordered, file:line, attack path, fix) — a High IDOR (invoice fetch missing an ownership check, sequential IDs) and a Critical SSRF (unvalidated `logoUrl` reaching a server-side fetch, exploitable against the cloud metadata endpoint), plus a clean pass on the ORM-parameterized query so the example shows the skill *not* padding findings — linked from `examples/README.md` and the main README's Examples section. `examples/changelog.md` added 2026-08-07: a v2.2.0→v2.3.0 cut showing tag-boundary detection, two feature commits collapsed into one entry, noise (a lodash bump, a `wip`, a typo fix) named and dropped rather than silently omitted, a path-traversal fix surfaced from an undersold commit message, and a `BREAKING` unit-change flagged with the exact migration step — linked from `examples/README.md` and the main README's Examples section. `examples/backfill-pilot.md` added 2026-08-08: a live-table `region` column backfill showing the pre-mutation count/scope check, the four concrete failures named in the rejected one-shot UPDATE, the full batched/keyset/checkpointed/idempotent script, the separate undo-table and before/after verification-query steps, and the live-table chase problem (fix the INSERT path first) — linked from `examples/README.md` and the main README's Examples section. Follow-up: still need examples for the remaining 8 skills (clock-sweep, codebase-tour, devlog, portability-audit, readme-forge, secret-spill, ship-it, stale-guard — trim as done) — do a few at a time, not all at once. `examples/stale-guard.md` added 2026-08-09: a per-team Redis inbox-count cache keyed only by `teamId`, showing invariant B catching a real cross-user leak (the key is missing the `assigned_to`/role dimension, so the first agent to populate a cold key gets their filtered counts served to every other agent on the team) and invariant A catching an independent gap (an admin bulk-redistribute action writes via raw SQL and skips the cache invalidation the normal reassign endpoint calls) — linked from `examples/README.md` and the main README's Examples section. Remaining 7: clock-sweep, codebase-tour, devlog, portability-audit, readme-forge, secret-spill, ship-it. `examples/secret-spill.md` added 2026-08-10: a public-repo Stripe key leak walked through the skill's actual order (rotate the flagged key first, widen to the other secrets sitting in the same leaked `.env`, assess blast radius including fork-network exposure a purge can't reach, purge with `git filter-repo` gated on explicit user go-ahead since it force-pushes shared history, verify with `gitleaks git --all-branches` plus a real 401 call rather than trusting "I clicked revoke", one-paragraph prevent step) — linked from `examples/README.md` and the main README's Examples section. Remaining 6: clock-sweep, codebase-tour, devlog, portability-audit, readme-forge, ship-it.
`examples/ship-it.md` added 2026-08-11: a pnpm-monorepo rate-limit fix showing the skill scoping checks to the touched package (`pnpm --filter api...`) instead of the whole workspace, a real typecheck failure caught and fixed (missing default for an optional `windowMs` reaching `setTimeout`), a stray debug `console.log` flagged from reading the actual staged diff before writing the message, a conventional-commit message matching the repo's existing `git log` convention, staging without pushing since the user said "ship it" not "push it," and a PR-ready summary that names the one broader suite it deliberately didn't run and why — linked from `examples/README.md` and the main README's Examples section. `examples/clock-sweep.md` added 2026-08-12: a Sao Paulo DST "24h reminder fires an hour off" report walked through a whole-surface sweep (not just the reported file) that finds 4 hits of the same two root mistakes — naive `datetime.now()` inheriting the server's zone, and `timedelta(days=1)`-as-calendar-arithmetic on what's actually a future wall-clock time — classifies each against the instant/wall-clock/date types before fixing, fixes all 4 (not a partial subset), verifies under `TZ=America/Sao_Paulo` and `TZ=Pacific/Chatham` plus a case pinned at the exact transition instant, and surfaces the historical-data ambiguity (old rows have no recorded zone) as a separate backfill question instead of guessing — linked from `examples/README.md` and the main README's Examples section. Remaining 4: codebase-tour, devlog, portability-audit, readme-forge. `examples/codebase-tour.md` added 2026-08-13: an inherited-repo "where do I start, and where would I add a discount code type" walkthrough showing the entry-point trace (routes → services → repositories → Redis event → async fulfillment worker) with `file:line` citations, the answer landing on the specific files for the actual question asked (the discount-type switch, the Joi schema whitelist, the DB CHECK constraint, the test file to follow) rather than a generic "look in services/", and an honest note about the two coexisting error-handling styles and the separately-started fulfillment worker — linked from `examples/README.md` and the main README's Examples section. `examples/portability-audit.md` added 2026-08-14: a Windows-bug-report-triggered sweep of a CLI tool through all six hazard classes, showing two real shell-out fixes (`os.system("rm -rf ...")` → `shutil.rmtree`, `subprocess.run("mkdir -p ...", shell=True)` → `os.makedirs`) and two real path-construction fixes (string-concatenated paths → `pathlib`), plus two candidates checked in context and correctly dropped as non-findings (a `rm -rf` inside a Docker-only entrypoint script, and a `.aux.json` filename that isn't actually a reserved Windows stem) and one unrelated dead-code line (`signal.signal(signal.SIGKILL, ...)`, uncatchable on any platform) flagged separately rather than padding the count — ends with the `windows-latest` CI-matrix recommendation since nothing was actually run on Windows to confirm the fixes — linked from `examples/README.md` and the main README's Examples section. Remaining 2: devlog, readme-forge. `examples/devlog.md` added 2026-08-15: an end-of-day "devlog" run across two scanned repos, showing the multi-repo scan where one repo (`infra-scripts`) has zero commits and is dropped silently rather than padded with "no activity" filler, the deeper `--stat`/`git status` dig on the repo with real activity, a reverted first-attempt fix kept in the entry per the anti-slop "tried X, didn't work, why" rule instead of being smoothed away, uncommitted WIP captured from `git status` alone, and the append-not-overwrite behavior noted for a same-day second session — linked from `examples/README.md` and the main README's Examples section. Remaining 1: readme-forge. `examples/readme-forge.md` added 2026-08-16: a "TODO"-only README rewrite for a small CLI tool showing the actual investigation (pyproject.toml scripts, cli.py subcommands, .env.example, existing CI workflow, tests for real usage) before writing a word, the specific-value hook over a generic description, and an honest wrap-up flagging what was left as a placeholder (no LICENSE file found) rather than guessed — linked from `examples/README.md` and the main README's Examples section. **All 18 skills now have a worked example — this backlog item is fully done, not just the remaining-count tracker.**
- [x] CONTRIBUTING.md: the novelty-check bar, the SKILL.md house style (pushy description, "why" in the body, boundaries section), and how to test a skill locally. Linked from README's Contributing section.
- [x] Frontmatter validator script (`tools/validate.py`) + CI. Checks per skill: closed `---` frontmatter, `name` present + kebab-case + equal to the directory, `description` within [40, 1024] chars, and a matching `# <name>` H1 in the body. Plus two cross-file checks against README.md: every skill is linked, and every `skills/<x>/SKILL.md` link resolves. Stdlib only (no yaml dep). `.github/workflows/validate.yml` runs it on push/PR. Passes on all 16 skills today; verified it fails (exit 1) on a name/description/link-broken fixture.
- [x] README: add a "which skill do I want?" decision table mapping symptoms → skill. Done — one row per skill, symptom-first phrasing pulled from each SKILL.md's own trigger language, linked to its SKILL.md.

## Future skills (research-verified novel, 2026-07-24 sweep — sketches in the item)
- [x] **`clean-exit` — REJECTED again 2026-08-23, audit angle also covered.** Re-checked with the
  exact "different angle" this item called for: an *audit of existing shutdown code* (not a
  scaffold-a-new-service skill) catching readiness-not-failed-before-drain, preStop/grace-period
  budget math, missing drain deadlines, and worker checkpointing before the SIGKILL window.
  `curiositech/windags-skills` (mirrored as `curiositech/port-daddy`) →
  `kubernetes-graceful-shutdown/SKILL.md` already ships almost exactly this bug catalog as an
  Anti-patterns table + Quality gates checklist (readiness-stays-green-during-shutdown, preStop-sleep
  exceeding grace-period, no drain ceiling) plus a synthetic-load rolling-deploy SIGTERM test —
  the specific "verify by SIGTERM-under-load" idea this item proposed. `robotijn/ctoc` →
  `resilience-checker/SKILL.md` independently covers the same SIGTERM-handler/readiness-flip/
  drain-budget checks as one section of a wider resilience audit. The one thin gap found —
  worker/queue-consumer checkpointing specifically before the SIGKILL window — is treated as a
  one-line afterthought everywhere, but it's too narrow to carry a standalone skill on its own.
  Closed as a documented non-starter; do not re-research without pairing that checkpointing slice
  with something else genuinely new.
- [x] `atomic-io` — crash-safe local file state: find truncate-then-write of state files, fix with temp-file → fsync → rename (`os.replace`), single-writer locks, validate-on-read recovery, Windows AV/EPERM retries. Added `skills/atomic-io/SKILL.md`, README table row + decision-table row (2026-07-31). Verified uncovered: searched for an existing Claude Code skill/marketplace entry for atomic writes / crash-safe file state (superpowers, awesome-claude-code lists) and found none — only generic "atomic commit" (git) and one open Claude Code bug report about its own non-atomic `.claude.json` writes, which is the exact failure mode this skill catches. Worked example added 2026-08-02: `examples/atomic-io.md` (OOM-killed worker, truncated `state.json`, four-piece fix + validate-on-read + single-writer boundary), linked from `examples/README.md` and the main README's Examples section. Follow-up: `tombstone` still has no worked example.
- [x] `tombstone` — evidence-based removal of "unused" surface: classify deletion risk (intra-repo vs externally reachable), gather prod evidence (access logs, pg_stat, tombstone counters), instrument-and-soak covering monthly jobs, then delete reversibly. Added `skills/tombstone/SKILL.md`, README table row + decision-table row (2026-08-01). Verified uncovered: searched for existing Claude Code skills on dead-code/cleanup (mcpmarket, lobehub, claudskills, ClaudeCN) — all found are static-analysis-only (knip, ts-prune, vulture, depcheck, grep-based reference checking within one repo); none gather runtime/production evidence for externally-reachable surfaces (HTTP logs, pg_stat_statements, cadence-aware soak windows for infrequent jobs). Also checked `clean-exit` (the other unchecked item) and found it's *not* novel — a "Graceful Shutdown" skill already exists on a prominent marketplace (crossaitools.com/skills, aj-geddes/useful-ai-prompts) and graceful-shutdown scaffolding is bundled into multiple existing service-scaffold skills — so left `clean-exit` unchecked below with that note rather than shipping a duplicate. Worked example added 2026-08-03: `examples/tombstone.md` (DB column deletion — grep-only false confidence, pg_stat_statements evidence, BI-dependency check, blast-radius-matched delete), linked from `examples/README.md` and the main README's Examples section.

## Skill improvements
- [x] ship-it: add a monorepo note (run checks only for affected packages; how to detect the workspace layout). Added to `skills/ship-it/SKILL.md`: a detection bullet in step 1 (pnpm-workspace.yaml, lerna.json, nx.json, turbo.json, package.json `workspaces`, `go.work`, Cargo `[workspace]`) and a scoping subsection in step 2 with the native affected/filter command per tool (pnpm, Nx, Turborepo, Lerna, Yarn workspaces, Cargo, Go workspaces), plus when to broaden back to the full-repo command (shared root config/deps) and what to do when affected packages can't be determined confidently. Follow-up: none of the other skills (backfill-pilot, job-warden) have monorepo-specific notes yet — likely not needed since they're not about running repo-wide checks.
- [x] env-detective: add a worked end-to-end example (CI log → delta table → binary search → fix). Added `examples/env-detective.md` (TZ-delta test failure: delta table, TZ-toggle binary search, class-level fix over a `.skip`), linked from `examples/README.md` and the main README's Examples section.
- [x] devlog: support a weekly rollup entry (`devlog week`) summarizing the week's dailies. Added a "Weekly rollup" section to `skills/devlog/SKILL.md`: triggers on "devlog week"/"weekly rollup"/"summarize this week", synthesizes (not re-digs) from the last 7 days of already-written daily entries, writes to `entries/weekly/YYYY-Www.md` (ISO week, separate from `entries/YYYY/MM/` so month-spanning weeks don't collide), groups by thread instead of concatenating days. Updated the frontmatter description and README row/triggers to match.

## Skill accuracy / drift audit
- [x] secret-spill: fix broken `gitleaks --all-branches` command. Verified against gitleaks' actual `cmd/git.go` flag set (`--platform`, `--staged`, `--pre-commit`, `--log-opts` — no `--all-branches` flag exists, so the command as written would error). Plain `gitleaks git` also only walks the current branch's history by default, so a "clean" result under the old wording didn't actually prove all refs were scanned — a real correctness gap in a skill whose step 4 is specifically about verifying-not-asserting. Fixed to `gitleaks git --log-opts="--all --reflog"` (the documented way to make `git log` cover every ref plus reflog-only commits) in `skills/secret-spill/SKILL.md` and the matching line in `examples/secret-spill.md`. Also fixed the trufflehog invocation from the invalid `--branch=--all-branches` to the real standalone `--all-branches` flag. `python tools/validate.py` still passes (18/18). Follow-up: only spot-checked the CLI references most likely to drift (gitleaks/trufflehog syntax) — the pnpm/nx/turbo/lerna/cargo/go.work commands in `ship-it/SKILL.md` and the `git filter-repo` flags in `secret-spill/SKILL.md` were checked in this pass and are still current as of 2026-08-17, but the remaining tool references across the other 16 skills (Docker, CI matrix syntax, DB-specific commands in migration-guard/backfill-pilot, etc.) haven't been re-verified — worth another pass.

## Note for the next run (2026-08-17)
Everything is checked off except `clean-exit` (stays unchecked on purpose — confirmed not novel, see its entry) and the drift-audit follow-up above. **Do not treat that as "nothing to do" and stop** — per the daily-agent instructions, do fresh novelty research and add 3-5 real, specific candidate items before picking, rather than assuming the pack is finished. Two directions still open: (1) finish the drift audit — the DB/Docker/CI-specific commands in migration-guard, backfill-pilot, job-warden, and portability-audit haven't been re-verified against current docs; (2) whether a genuinely different-angle `clean-exit` (an *audit* of existing shutdown code, not a scaffold) would clear the novelty bar — it wasn't re-verified after the 2026-08-01 check.

## Drift audit — round 2 (2026-08-18)
Re-verified the specific claims in `migration-guard`, `backfill-pilot`, `job-warden`, and `portability-audit` against current sources (Postgres/MySQL docs, Rails/Django migration docs, live-tested the `portability-audit` case-collision command in this repo). Findings:
- `migration-guard`: the `CREATE INDEX CONCURRENTLY` / `atomic = False` / `disable_ddl_transaction!` claims checked out. Found a real, verified gap: a failed `CONCURRENTLY` build doesn't roll back like a normal `CREATE INDEX` — it leaves an `INVALID` index still costing write overhead, and needs an explicit `DROP INDEX CONCURRENTLY` before retrying. This wasn't in the skill. **Fixed** — added as a bullet in the "Locks / downtime" section of `skills/migration-guard/SKILL.md`.
- `backfill-pilot`, `job-warden`: SQL/Redis/queueing terminology (`SET NX PX`, `concurrencyPolicy: Forbid`, keyset pagination, `IS DISTINCT FROM`) all checked out against current docs — no drift found.
- `portability-audit`: live-ran `git ls-files | sort -f | uniq -di` in this repo (exit 0, correct behavior on a repo with no case collisions) — command is correct as written. MySQL instant-DDL claims are still accurate as hedged ("covers *some* ALTERs") though MySQL 8.0.29 introduced a documented redo-log corruption bug with INSTANT ADD/DROP COLUMN under some conditions (bugs.mysql.com) — worth a one-line caution if this skill's hazard-checklist section is ever extended to cover MySQL ALTER specifics in more depth, but the current wording doesn't overclaim, so left as-is rather than churning working text.
Drift audit for these four skills is now done. Remaining un-reverified surface: `changelog`, `stale-guard`, `skew-check`, `clock-sweep`, `security-sweep`, `env-detective`, `atomic-io`, `tombstone`, `secret-spill`'s `git filter-repo` flags (checked 2026-08-17, still current) haven't had a fresh pass — low priority, no known drift reported.

## Drift audit — round 3 (2026-08-19)
Read every remaining un-reverified `SKILL.md` in full against current sources/behavior, plus the five skills no prior round had touched (`ship-it`, `git-rescue`, `devlog`, `codebase-tour`, `readme-forge`), closing out the drift-audit backlog thread completely — every one of the 18 skills has now had at least one focused verification pass.
- `atomic-io`: `os.replace` vs `os.rename` on Windows (rename raises `FileExistsError` if dest exists, replace doesn't), same-directory temp-file requirement, `fcntl.flock`, Windows `MoveFileEx`/antivirus-lock retry pattern — all checked out.
- `tombstone`: `pg_stat_statements`, knip/ts-prune/vulture/depcheck as real static-analysis tools, `410 Gone` retirement pattern — checked out.
- `clock-sweep`: Python `datetime.now()`/`utcnow()` naive-by-default behavior, `Pacific/Chatham` as a genuine +12:45/+13:45 DST-observing zone (a real hostile-TZ choice, not a made-up one), Postgres `timestamp` vs `timestamptz` distinction — checked out.
- `changelog`: Keep a Changelog format/URL and category set — checked out.
- `skew-check`: protobuf field-number immutability / `reserved` keyword, Avro default-on-added-field requirement — checked out.
- `stale-guard`: no version-specific claims to drift-check; the invariants (write-path/key-scoping) are timeless — nothing to verify against an external source.
- `security-sweep`: OWASP-style category list (injection, IDOR, SSRF, deserialization, crypto misuse) — still the current standard framing, no drift.
- `env-detective`: spot-checked the GitHub Actions runner locale claim ("CI runners are UTC + C locale") against current `actions/runner-images` reports — GitHub-hosted runners often ship with `LANG`/`LC_ALL` unset, which behaves like the `POSIX`/`C` locale family; the skill's simplification holds, not drift.
- `git-rescue`: verified the GitHub events-API force-push recovery claim (`gh api repos/OWNER/REPO/events`, `PushEvent.payload.before`) — the field is real and documented; left as-is (the skill already hedges this as one recovery avenue among several, not a guarantee).
- `ship-it`, `devlog`, `codebase-tour`, `readme-forge`: no external-fact claims to drift-check (these are process/methodology skills, not tool-syntax reference) — read in full, no inaccuracy found.
No fixes were needed this round — everything read checked out. This closes the drift-audit thread opened in the 2026-08-17 note; future drift risk is now about *new* tool-syntax changes (Postgres/MySQL/git/CI releases) rather than an unverified backlog.

## Novelty sweep + new skill (2026-08-20)
Ran a fresh two-track novelty sweep (the direction left open by the 2026-08-19 note) across
Claude skill marketplaces (claudskills, mcpmarket, lobehub, crossaitools, smithery),
awesome-claude-code lists, `obra/superpowers`, `anthropics/skills`, and GitHub-wide
`filename:SKILL.md` code search. Results — both previously-noted candidates died, one new one shipped:

- [x] **(a) worker startup / readiness audit — REJECTED, not novel.** "Health Check Endpoints"
  (originating from `aj-geddes/useful-ai-prompts`, the same source that killed `clean-exit`) is
  mirrored across mcpmarket, claudskills.com, claudemarketplaces, aimcp, and claudedirectory, and
  explicitly covers liveness/readiness separation, dependency checks, probe failure config, and
  startup delays. Also found `robotijn/ctoc` → `health-check-validator` (near-exact scope match:
  startupProbe gating on migrations/cache warmup, deep-readiness checks, probe timing budgets),
  `FluxonLab/Skillry` → `09-startup-health-readiness`, and lobehub `prod-readiness-review`. Only the
  migrations-race-at-boot and cold-pool-warmup slices are uncovered — too thin to carry a skill, and
  shipping it would repeat the `clean-exit` mistake in mirror image. Closed as a documented non-starter.
- [x] **(b) PII / data-retention audit — REJECTED, not novel.** `getsentry/warden-skills` →
  `skills/wrdn-pii/SKILL.md` (57★, official Sentry org, actively maintained) covers candidate (b)
  almost verbatim: real PII reaching logs, metrics tags, Sentry scope, analytics events, committed
  fixtures, URL query strings, exports, caches, and session replay, with better exclusion heuristics
  (placeholder/reserved-IP/role-alias filtering) than a fresh skill would ship with.
  `alpha-omega-security/scrutineer` → `skills/audit-pii/SKILL.md` (187★) is a second direct match and
  explicitly traces sources→sinks documenting audience *and retention*. The one thin remaining slice
  (retention windows / purge lifecycle at code level) sits inside `tombstone`'s territory — an internal
  duplicate as much as an external one. Closed as a documented non-starter.
- [x] **`blast-guard` — SHIPPED (verified novel).** Pre-send review for code that messages a real
  user audience (bulk email/push/SMS/chat). Verified uncovered: `filename:SKILL.md` searches on
  bulk-send safety terms returned only marketing/copywriting content (`CosmoBlk/email-marketing-bible`,
  `ever-just/agentskills`); marketplace hits are agent-side email *tools* (mcpmarket
  `gmail-send-for-claude-code`, `email-management-automation`) — dry-run for the agent's own sends,
  not a review of product code that mails users. Nothing in `obra/superpowers` or
  `travisvn/awesome-claude-skills`. In-pack: `job-warden` Q1 covers duplicate *sends* via idempotency
  but nothing about audience correctness, suppression lists, caps, or irreversibility; `backfill-pilot`
  is the data analogue with no messaging equivalent. Grounded in two real incidents rather than a
  hypothetical: a staging push token misconfigured against the production app sent a "test"
  notification to ~30,000 real users (medium.com/@ruchiram4), and Shutterfly's birth-announcement
  congratulations email went to a distribution far wider than the intended recent-purchaser segment.
  Added `skills/blast-guard/SKILL.md`, README skills-table row + decision-table row, intro paragraph
  updated (eighteen → nineteen, rejected-candidates list extended). `python tools/validate.py` passes 19/19.

Follow-ups discovered this run:
- [x] `examples/blast-guard.md` — added 2026-08-21: the suggested winback-campaign scenario (41,200 vs
  an expected ~3,000, unbounded `last_login <` filter with no `deleted_at IS NULL`), walked through all
  four checks in order (audience COUNT + sample, suppression-table join missing, environment binding OK,
  unbatched/no-checkpoint stop mechanism) ending in a BLOCK verdict — linked from `examples/README.md`
  and the main README's Examples section, which now reads "every skill in the pack has one" again.
  `python tools/validate.py` still passes (19/19). All 19 skills now have a worked example.
- [x] **Money rounding/allocation audit — REJECTED, not novel even narrowed.** Re-researched
  2026-08-23 the narrowed slice this item called for (largest-remainder allocation with a
  "sum of parts == total" invariant, aggregate-vs-line-item invoice rounding mismatch,
  rounding-mode consistency across pricing/tax/refund/reporting paths). All three sub-slices are
  already covered, not just the broad "use Decimal" framing: `majiayu000/claude-skill-registry`
  (574★) → `skills/data/financial-integrity/SKILL.md` has an explicit "Allocation Law" (sum of
  parts must equal total, watch rounding leftovers) and a named "Penny Allocate Algorithm";
  `alpacahq/alpaca-skills` (111★, official Alpaca trading-API pack) →
  `skills/broker-api/money-precision/SKILL.md` covers re-rounding-after-every-step across a
  split/allocation pipeline; `Sir-chawakorn/sanook-cli` → `skills/money-decimal-arithmetic/SKILL.md`
  covers all three sub-slices nearly verbatim (largest-remainder pseudocode with the same invariant,
  explicit round-per-line-vs-round-on-total distinction, one-rounding-mode-across-the-pipeline rule).
  Same allocation/sum-conservation pattern also independently reinvented in `zakariaf/SplitFair` and
  `aKhalid2013/HalvyECC`. Verdict: well-trodden ground reinvented 4+ times independently, closed as a
  documented non-starter — do not re-research this without a genuinely new angle.
- [ ] Researched-and-passed this run, do not re-research without a new angle: Unicode/text correctness
  (`Sir-chawakorn/sanook-cli` → `unicode-text-correctness`, 9★, near-identical seven-step method),
  read-path pagination auditing (65 hits, several dedicated; also overlaps `backfill-pilot`),
  idempotency/retry review (duplicate of `job-warden` Q1), replica-lag/read-your-writes
  (`StevenACoffman/steve-skill-market` → `replication-lag-as-correctness`, direct match), multi-tenant
  isolation (269 hits, 4+ dedicated auditors), stale feature-flag cleanup (PostHog ships it),
  backup/restore drills (443 hits), unbounded-query/OOM audit (folded into perf-review skills).

## Note for the next run (2026-08-19)
All 18 skills have now had a drift-verification pass (round 1: secret-spill; round 2: migration-guard, backfill-pilot, job-warden, portability-audit; round 3: the remaining 13). Don't re-run the same pass again next time — nothing here is stale enough to justify it. Two real directions remain open:
1. `clean-exit` — still unchecked, still not novel as scoped (see its entry above). If picked up, it needs a genuinely different angle (an *audit* of existing shutdown code, not a scaffold) or it stays a documented non-starter.
2. Fresh novelty research for new skill candidates the pack doesn't cover yet — worth a proper sweep of superpowers/awesome-lists/marketplaces rather than assuming the 18 are exhaustive. Two areas that came up while reading this round but weren't researched for novelty (do that before writing either): (a) a "worker startup/readiness audit" distinct from `clean-exit`'s shutdown focus — health-check races, migration-before-serve ordering, connection-pool warmup; (b) a "PII/data-retention audit" for code paths that log, cache, or persist sensitive fields past their legal retention window — different from `secret-spill` (credentials, not user data) and `stale-guard` (correctness, not compliance).

## Novelty sweep — round 2 (2026-08-23): 0 new candidates, both open items closed dead
Both remaining unchecked items were re-researched to their stated bar and both died (see their
entries above for citations): `clean-exit`'s audit angle is covered by
`curiositech/windags-skills` and `robotijn/ctoc`; the narrowed money-allocation/rounding scope is
covered independently by 4+ repos. With both closed, ran a broad fresh sweep (20+ targeted
`filename:SKILL.md` searches) across categories the pack hasn't touched: webhook/API delivery
reliability, N+1 query detection, retry/backoff storm prevention, CORS/cookie/SameSite specifics,
DB connection-pool exhaustion, API contract/breaking-change detection, dual-write/outbox
consistency, secret rotation without restart, event/webhook ordering, test-fixture realism vs.
production shape, distributed lock TTL vs. job duration, timeout/deadline-budget propagation,
swallowed-exception/empty-catch patterns, deadlock/lock-ordering, soft-delete correctness
(unique-index + cascade + GDPR purge), CDN/edge cache poisoning (unkeyed headers), abandoned
multipart uploads, CSV/Excel formula injection, and distributed rate-limiter per-instance counter
scoping. **Every one is already covered**, several by dedicated, well-written skills with
near-identical scope to what a fresh write would have produced (e.g.
`marquesfelip/agents-and-skills` → `distributed-locking` already cites a "customers charged 3x"
lock-TTL incident almost identical to what this pack's own grounding style would reach for; →
`soft-delete-strategy` matches the soft-delete idea point for point). The saturation is driven by
large auto-generated aggregator repos (`majiayu000/claude-skill-registry` and its `-data` mirror,
thousands of entries) that have systematically enumerated most backend/infra engineering footguns
by name, plus several smaller but sharply-written dedicated packs
(`marquesfelip/agents-and-skills`, `Sir-chawakorn/sanook-cli`, `hookdeck/webhook-skills`).

**Conclusion: the pure backend/infra engineering-pain-point space this pack has mined since
2026-07-24 is now saturated.** Do not re-run another broad sweep over that same territory without
a new angle — it will re-find the same aggregator coverage. Two honest paths forward for whoever
picks this up next:
1. A category this sweep didn't have budget for: **mobile-specific release/rollback footguns**
   (app-store review lag vs. hotfix urgency, staged-rollout percentage math, forced-upgrade vs.
   soft-nudge version gating) — unresearched, could be real or could be another saturated corner;
   check before writing.
2. Given two saturated sweeps in a row (2026-08-20 and this one) turned up one shippable skill
   (`blast-guard`) out of ~10+ candidates evaluated, this pack may be close to functionally
   complete as a curated set. If the next 1-2 runs also turn up nothing, it's reasonable to shift
   daily-agent effort toward maintenance (drift-auditing external tool-syntax claims as docs age —
   Postgres/MySQL/git/CI/k8s releases move) rather than forcing a new skill through on a technicality
   to hit "ship something today."

## `rollout-guard` — SHIPPED (2026-08-24, verified novel)
- [x] Researched path 1 from the note above (mobile-specific release/rollback footguns). Found
  general staged-rollout/rollback coverage (`addyosmani/agent-skills` → `shipping-and-launch`:
  pre-launch checklist, feature-flag lifecycle, staged rollouts, rollback) but scoped to
  backend/web deploys — no percentage-math specifics, no app-store review-queue reasoning. Found
  several App Store/Play Store *pre-submission compliance* checkers (`cruisediary/apple-app-review-skills`,
  `devsemih/appstore-review-skill`, `safaiyeh/app-store-review-skill`, mcpmarket's App Store
  Deployment/Readiness skills) — all check whether a build will pass review (privacy manifests,
  entitlements, metadata), a different problem from whether a release/rollback *strategy* is safe
  once the build is submitted. No skill combining staged-rollout halt-threshold discipline,
  review-lag-aware incident response (kill switches vs. waiting on review), and forced-vs-soft
  version-gating criteria was found across the same sources checked in the 2026-08-20/23 sweeps
  (claudskills, mcpmarket, lobehub, claudemarketplaces, `obra/superpowers`,
  `majiayu000/claude-skill-registry`). Grounded in verifiable platform mechanics rather than a
  single incident citation (two candidate secondary sources for a "40% of users stuck on a broken
  version" anecdote were egress-blocked and couldn't be confirmed as primary, so left out rather
  than cited unverified): Apple's fixed 7-day 1/2/5/10/20/50/100% phased-release schedule
  (adjustable only by pausing, not reshaping) vs. Google Play's freely-chosen percentage/pace,
  Apple's discretionary (non-SLA) expedited-review path, and the structural fact that halting a
  rollout stops new installs but can't undo the ones already shipped.
  Added `skills/rollout-guard/SKILL.md`, README skills-table row + decision-table row, intro
  paragraph updated (nineteen → twenty). `python tools/validate.py` passes 20/20.

- [x] `examples/rollout-guard.md` — added 2026-08-25: a forced-update decision walking all five
  checks against a real plan (iOS 14 background-sync bug corrupting local transaction cache,
  20%-into-phased-rollout, pause v5.1.0 + force v5.1.1 once approved) — halt-threshold is reactive
  not a standing metric (CAUTION), the pause/fix distinction is right but the plan has no repair
  step for the already-corrupted 20% (FAIL), no kill switch on the sync path so the only mitigation
  is the review clock (FAIL), forcing is the correct call for active data corruption but the
  version-gate's failure-open behavior is unconfirmed (CAUTION), and the force may not reach
  iOS-14 devices too old to take v5.1.1 (CAUTION) — linked from `examples/README.md` and the main
  README's Examples section, which now reads "every skill in the pack has one" again for all 20.
  `python tools/validate.py` passes (20/20). All 20 skills now have a worked example.

## Novelty sweep — round 3 (2026-08-26): no ship, 5 candidates researched and logged
Ran targeted `filename:SKILL.md` searches across five candidate categories the pack hasn't
covered, following up on the "functionally complete?" question the 2026-08-23 note left open.
Confirmed `security-sweep`, `blast-guard`, `stale-guard`, and `tombstone` (grepped their bodies)
don't already touch any of these five. Two died outright, three are genuinely unresolved — none
were verified enough in one session to write a skill against today, so nothing shipped; logging
all five so the next run doesn't re-walk the same ground from zero.

- [ ] **GDPR / data-deletion cascade (right-to-erasure) — likely REJECTED, saturated.** Multiple
  dedicated, actively-maintained packs already cover this in depth:
  `Sushegaad/Claude-Skills-Governance-Risk-and-Compliance` (GDPR/DSGVO among 10+ regulatory
  frameworks, claims a benchmarked accuracy delta), `alirezarezvani/claude-skills` →
  `gdpr-dsgvo-expert/SKILL.md`, and an mcpmarket `gdpr-data-handling` skill that names the exact
  mechanics a fresh skill would reach for (DSAR handling, Article 17 erasure automation,
  consent-withdrawal cascades with audit trail, retention-period cleanup jobs). Deep enough,
  cited enough, and close enough to this pack's own `tombstone` territory (evidence-based removal)
  that it isn't worth re-verifying further — treat as closed unless someone finds a narrower
  uncovered slice.
- [ ] **Terraform / IaC plan review — REJECTED, saturated.** `lgbarn/devops-skills` ships
  `terraform-plan-review` (parallel-agent plan analysis before apply) and
  `terraform-drift-detection` as named, dedicated skills; `LukasNiessen/terrashark` and
  `antonbabenko/terraform-skill` both focus specifically on grounding plan/apply review in
  HashiCorp best practices to kill hallucinated Terraform. This is a crowded, well-covered
  category — closed, do not re-research without a materially different angle (e.g. a specific
  cloud-provider footgun class none of these name).
- [ ] **LLM-integration prompt-injection review** (reviewing *product* code that feeds
  untrusted content — user input, fetched web pages, tool output — into an LLM call with
  tool-calling/agentic access, distinct from `security-sweep`'s OWASP-style SQLi/IDOR/SSRF list
  and distinct from *skill supply-chain* security auditing). Searches this round mostly surfaced
  the latter: `aisa-group/promptinject-agent-skills` and the Snyk ToxicSkills research are about
  malicious SKILL.md files attacking the agent itself, not about auditing a team's own
  LLM-integrated application code for the untrusted-content-controls-behavior pattern. Grepped
  `security-sweep/SKILL.md` directly — no mention of prompt injection, tool-call scoping, or
  untrusted-content boundaries. This looks like a real, current, and distinct gap (agentic
  features are now common in ordinary product code, not just agent frameworks), but it needs a
  proper novelty pass before writing — specifically checking `obra/superpowers`,
  `majiayu000/claude-skill-registry`, and the AI-safety-adjacent marketplaces (which weren't
  covered by the generic `filename:SKILL.md` search used here) before assuming it's uncovered.
  **Best candidate for next run — start here.**
- [ ] **Notification-preference / opt-out correctness across channels** — does an ongoing
  notification system actually honor a user's per-channel opt-outs (email vs. push vs. SMS),
  suppression lists, and frequency caps over time, as opposed to `blast-guard`'s scope (a
  one-off bulk-send review: audience query sanity, suppression-list join, env binding, stop
  mechanism, at send time). Search this round was inconclusive — returned GitHub's own
  notification-settings docs rather than any SKILL.md, positive or negative. Needs a sharper
  search (marketplace + `filename:SKILL.md "preference center"` style queries) before a novelty
  verdict can be reached either way.
- [ ] **RBAC / permission-matrix drift audit** (does the code's actual authorization logic match
  the intended role/permission matrix — stale roles still granting access, a new endpoint missing
  its permission check, admin-only fields reachable through a non-admin path) — distinct from
  generic "security review" (which flags one bug at a time, not systematic matrix-vs-code drift).
  Search this round was inconclusive: found only skill-*audit* tools (scanning SKILL.md files
  themselves for security issues) and generic IAM/RBAC references inside unrelated infra skills,
  nothing that clearly claims or clearly disclaims this specific angle. Needs a follow-up search
  before a novelty verdict can be reached either way.

Pack quality bar held: none of these five were confirmed novel and complete enough to ship in
one sitting, so none were written — per the daily-agent rules, an unverified skill is worse than
no skill. `python tools/validate.py` still passes 20/20 (no skill files touched this run).

## `pref-guard` — SHIPPED (2026-08-27, verified novel); two other round-3 candidates closed dead

Followed up on the three open candidates the 2026-08-26 sweep left unresolved, in the order that
sweep suggested.

- [x] **LLM-integration prompt-injection review — REJECTED, covered.** This was the sweep's
  named "best candidate for next run." Fetched and read the actual methodology (not just a
  marketplace blurb) of `UnitOneAI/SecuritySkills` → `skills/ai-security/prompt-injection/SKILL.md`
  (part of a 45-skill pack grounded in OWASP/NIST/MITRE, `LLM Top 10 Review` + `Agentic AI Top 10`
  siblings in the same `ai-security/` directory). It does exactly the thing this candidate
  proposed: **source-code review** (not black-box prompt testing) that maps every point untrusted
  content reaches an LLM call (chat input, fetched web pages, RAG documents, tool output), checks
  whether delimiters/boundaries between data and instructions are enforceable in code rather than
  asserted in a system-prompt comment, and evaluates instruction-hierarchy and privilege-separation
  defenses — near-exact match to the "boundary enforcement, not just SQLi/IDOR" angle this
  candidate was scoped around. Also independently confirmed `alirezarezvani/claude-skills` →
  `engineering-team/skills/ai-security/SKILL.md` explicitly scopes itself to the model/prompt layer
  (signature-scans prompts themselves) and GitHub's own `github/awesome-copilot` →
  `skills/security-review/SKILL.md` does *not* cover this angle — so the search wasn't a single
  false positive. Closed as covered; do not re-research without a materially different angle (e.g.
  a slice UnitOneAI's skill doesn't touch).
- [x] **RBAC/permission-matrix drift audit — REJECTED, substantially covered.** Two matches, read
  in full rather than trusted from a listing: `Intense-Visions/harness-engineering` →
  `security-rbac-design/SKILL.md` is design/scaffolding-focused (confirmed: "When to Use" lists
  designing-a-new-system first, auditing appears last and narrowly) so it doesn't kill the
  candidate on its own — but `utkusen/sast-skills` → `sast-missingauth` does the actual mechanic
  this candidate wanted: a three-phase **systematic sweep of the whole codebase** (recon maps every
  endpoint plus the role/permission system, then batched parallel-subagent verification checks
  *each* endpoint for both missing authentication and broken function-level authorization). That's
  the "new endpoint missing its permission check, caught systematically rather than one bug at a
  time" core of the candidate. The one piece it doesn't do — stale/orphaned roles that still grant
  access, and drift against a *documented* intended matrix rather than inferring intent from the
  code itself — is real but too thin to carry a standalone skill alone (same shape as the
  `clean-exit` rejection: a near-exact match exists, the residual gap is a one-line addendum, not a
  skill). Closed as covered; the thin residual isn't worth re-researching on its own.
- [x] **Notification-preference/opt-out correctness across channels — SHIPPED as `pref-guard`.**
  The 2026-08-26 note flagged this as needing a sharper search. Ran targeted searches this round
  (`filename:SKILL.md` + generic web search across "preference center", "suppression list",
  "opt-out audit", "per-channel"/"frequency cap" combinations, `claudskills.com`,
  `majiayu000/claude-skill-registry`, and the generic marketplaces already checked for
  `blast-guard`) — found real hits for one-off bulk-send safety (this pack's own `blast-guard`) and
  for email-deliverability/compliance reference skills (`chunkydotdev/email-skills`), but nothing
  auditing the **standing correctness property** this candidate named: does an evolving system with
  many send paths and channels keep actually checking live opt-out/suppression/frequency-cap state,
  and does provider-side unsubscribe/bounce data really sync back into the app's own suppression
  record. Verified in-pack this is genuinely distinct from `blast-guard` (single send, audience
  query + dry run + stop mechanism, reviewed once before firing) rather than an internal duplicate.
  Added `skills/pref-guard/SKILL.md`, README skills-table row + decision-table row, intro paragraph
  updated (twenty → twenty-one, rejected-candidates list extended with today's two dead ends).
  `python tools/validate.py` passes 21/21. Follow-up: `examples/pref-guard.md` still needed (same
  pattern as `blast-guard`/`rollout-guard` — skill shipped first, worked example added next).
