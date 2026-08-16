# Claude Code Skills

**A small pack of Claude Code skills for the unglamorous work that actually ships software** — finalizing a change, writing a README people read, catching the security bug before it lands, cutting release notes, and getting oriented in a strange codebase.

Every skill here is written the way the [official skill guidance](https://docs.anthropic.com/en/docs/claude-code/skills) recommends: a pushy trigger description so Claude reaches for it at the right moment, and a body that explains the *why* so Claude does the task well instead of following steps by rote. No fluff, no 40-skill kitchen sink — eighteen that earn their place.

Every skill added since the original five went through the same filter: research the existing ecosystem first (official packs, superpowers, the awesome-lists, the marketplaces) and keep only problems **no prominent skill already solves**. Candidates that turned out to be covered elsewhere — commit splitting, flaky-test fixing, session handoffs, concurrency audits, license compliance — were dropped, not duplicated. What survived: lost-git-work recovery, pre-deploy migration review, environment-delta debugging, Windows/POSIX audits, production backfills, an evidence-grounded dev diary, mixed-version deploy safety, datetime correctness, leaked-credential response, background-job correctness, cache-correctness review, crash-safe local file I/O, and evidence-based removal of externally-reachable "dead" code.

## The skills

| Skill | What it does | Triggers on |
|-------|--------------|-------------|
| **[ship-it](skills/ship-it/SKILL.md)** | Runs the repo's own tests/lint/typecheck, fixes what breaks, writes a clean conventional commit + a review-ready diff summary | "commit this", "ship it", "is this ready to push" |
| **[readme-forge](skills/readme-forge/SKILL.md)** | Writes or overhauls a README by *reading the codebase* — real commands, real entry points, a hook that earns the star | "write a README", "improve my docs", "make this repo look professional" |
| **[security-sweep](skills/security-sweep/SKILL.md)** | Reviews the working diff for *exploitable* issues (injection, IDOR, secrets, SSRF…) and reports only findings with a concrete attack path | "security review", "any vulnerabilities here", "is this safe to ship" |
| **[changelog](skills/changelog/SKILL.md)** | Turns git history since the last tag into user-facing release notes, grouped by impact, breaking changes flagged | "release notes", "what changed since v1.2", "update the changelog" |
| **[codebase-tour](skills/codebase-tour/SKILL.md)** | Orients you in an unfamiliar repo by tracing a real code path and ending at "here's where you'd make your change" | "how does this work", "where do I start", "walk me through this codebase" |
| **[git-rescue](skills/git-rescue/SKILL.md)** | Calm-paramedic recovery of "lost" work: secures the scene with backup refs, finds the commits via reflog/fsck/remote, restores with the smallest safe operation | "I lost my changes", "the rebase destroyed everything", "I committed to main by accident" |
| **[migration-guard](skills/migration-guard/SKILL.md)** | Reviews a schema migration like the database will execute it in prod: locks, deploy-order breakage, data loss, honest rollbacks — verdict BLOCK/CAUTION/SAFE | "is this migration safe", "will this lock the table", any ALTER headed for real data |
| **[env-detective](skills/env-detective/SKILL.md)** | Cracks "works on my machine": enumerates the delta between the two environments, ranks it by base rates, binary-searches it with experiments | "passes locally but fails in CI", "only fails in Docker", "green here, red there" |
| **[portability-audit](skills/portability-audit/SKILL.md)** | Sweeps a codebase for Windows/POSIX hazards — POSIX-only shell-outs, path separators, CRLF, reserved filenames, case collisions — and fixes them + adds the CI matrix | "make this work on Windows", "a Windows user says it's broken", "cross-platform" |
| **[backfill-pilot](skills/backfill-pilot/SKILL.md)** | Writes production data backfills with the seven non-negotiables: batched, keyset-paginated, resumable, undoable, dry-run-first, throttled, verified | "backfill", "fix the data in prod", "migrate existing rows" |
| **[devlog](skills/devlog/SKILL.md)** | Turns today's *real* git activity across your repos into a short, honest dev-diary entry committed to a journal repo — no activity, no entry; `devlog week` rolls up the week's entries | "devlog", "log today", "write today's entry", "devlog week" |
| **[skew-check](skills/skew-check/SKILL.md)** | Reviews a diff for mixed-version deploy hazards — can old and new code share queues, caches, sessions, and contracts during the rollout window (and survive rollback)? | "safe to roll out?", canary/rolling deploy prep, renamed fields crossing process boundaries |
| **[clock-sweep](skills/clock-sweep/SKILL.md)** | Systematic datetime/timezone audit — naive datetimes, DST-unsafe math, offset-as-zone, date-vs-instant confusion — swept across the whole codebase, verified under hostile TZs | "times are off by an hour", "broke after DST", "handle timezones properly" |
| **[secret-spill](skills/secret-spill/SKILL.md)** | Incident response for a credential in git history: rotate first, assess blast radius, purge with filter-repo, verify with scanners — in that order | "I committed my API key", "GitGuardian emailed me", scanner found a real token |
| **[job-warden](skills/job-warden/SKILL.md)** | Six-question correctness review for cron jobs, workers, and queue consumers: idempotency, overlap, schedule honesty, poison messages, batch semantics, dead-man's-switch | "add a cron job", "process this queue", duplicate/missed job runs |
| **[stale-guard](skills/stale-guard/SKILL.md)** | Proves your caches can't serve wrong data: every write path invalidates, every key contains every dimension that changes the value, stampedes and negative-caching handled | "users see old data", "shows the wrong user's data", "is this caching correct" |
| **[atomic-io](skills/atomic-io/SKILL.md)** | Finds truncate-then-write of local state files and fixes them with temp-file → fsync → atomic rename, single-writer locks, and validate-on-read recovery | "config file came back empty after a crash", "make this crash-safe", "atomic write" |
| **[tombstone](skills/tombstone/SKILL.md)** | Proves an externally-reachable endpoint, DB column/table, or infrequent job is actually unused with production evidence — not just a repo-wide grep — before you delete it | "can I delete this endpoint/column", "is this still used", "nobody calls this anymore, right?" |

## Which skill do I want?

Not sure which one fires for your situation? Match the symptom:

| If you're seeing... | Use |
|----------------------|-----|
| Tests/lint pass locally but you're not sure it's actually ready to push | [ship-it](skills/ship-it/SKILL.md) |
| Your README is thin, outdated, or embarrassing | [readme-forge](skills/readme-forge/SKILL.md) |
| A diff touches auth, user input, or secrets and you want to know if it's exploitable | [security-sweep](skills/security-sweep/SKILL.md) |
| You're cutting a release and need a changelog or release notes | [changelog](skills/changelog/SKILL.md) |
| You just cloned or inherited a repo and don't know where to start | [codebase-tour](skills/codebase-tour/SKILL.md) |
| You ran `reset --hard`, botched a rebase, or force-pushed and think work is gone | [git-rescue](skills/git-rescue/SKILL.md) |
| You're about to run an `ALTER TABLE` or migration against a table with real data | [migration-guard](skills/migration-guard/SKILL.md) |
| "Works on my machine" but the same commit fails in CI, Docker, or on a teammate's machine | [env-detective](skills/env-detective/SKILL.md) |
| A Windows user reports your CLI/tool is broken | [portability-audit](skills/portability-audit/SKILL.md) |
| You need to fix or migrate data already sitting in a live production table | [backfill-pilot](skills/backfill-pilot/SKILL.md) |
| You want an honest dev-diary entry built from today's actual git activity | [devlog](skills/devlog/SKILL.md) |
| You're about to do a rolling/canary deploy and old and new code might share state | [skew-check](skills/skew-check/SKILL.md) |
| Times are off by an hour, or something broke right after a DST change | [clock-sweep](skills/clock-sweep/SKILL.md) |
| You just committed an API key, token, or credential to git | [secret-spill](skills/secret-spill/SKILL.md) |
| A cron job or queue worker double-processes, misses runs, or dies silently | [job-warden](skills/job-warden/SKILL.md) |
| Users report seeing stale data, or someone else's data | [stale-guard](skills/stale-guard/SKILL.md) |
| A config/checkpoint/cache file came back empty or corrupted after a crash | [atomic-io](skills/atomic-io/SKILL.md) |
| You want to delete an endpoint/column/job and "static analysis says it's unused" isn't good enough | [tombstone](skills/tombstone/SKILL.md) |

## What makes these different

Most skill packs are thin wrappers — a description and three bullet points. These are written to actually change the quality of the output:

- **Grounded, not guessing.** `readme-forge` reads your `package.json` and entry points; `ship-it` discovers *your* test command instead of assuming one; `codebase-tour` traces real `file:line` paths. Skills that invent details erode trust fast.
- **Honest by design.** `security-sweep` reports only what it can prove is exploitable — a short list of real problems, not a wall of theoretical maybes. `ship-it` never dresses a failing test up as passing.
- **They explain the why.** Each skill tells Claude the reasoning behind the steps, which is what lets a capable model do the task well on *your* repo instead of pattern-matching a template.

## Install

Skills live in a `skills/` directory Claude Code reads. You have two options.

### Option A — per project (recommended to try)

Drop the ones you want into your project's `.claude/skills/`:

```bash
git clone https://github.com/0xmortuex/claude-code-skills
mkdir -p .claude/skills
cp -r claude-code-skills/skills/ship-it .claude/skills/
cp -r claude-code-skills/skills/readme-forge .claude/skills/
# ...or copy them all:
cp -r claude-code-skills/skills/* .claude/skills/
```

### Option B — globally, for every project

Copy them into your user skills directory so they're available everywhere:

```bash
git clone https://github.com/0xmortuex/claude-code-skills
mkdir -p ~/.claude/skills
cp -r claude-code-skills/skills/* ~/.claude/skills/
```

Either way, start (or restart) Claude Code and the skills are live. Claude invokes them automatically when your request matches — or call one by name, e.g. `/ship-it`. Run `/skills` to confirm they loaded.

> **Tip:** start with one or two. Skills work best when each one clearly owns its trigger; copying all seventeen at once is fine, but if you only want the security review, just take `security-sweep`.

## Using them

You mostly don't have to do anything — the descriptions are tuned to trigger on natural phrasing:

```
you:  ok I think the payment refactor is done, get it ready to push
      → ship-it runs your tests, catches a type error, fixes it,
        stages a conventional commit, hands you a PR summary

you:  this endpoint takes a user id from the query string — anything scary here?
      → security-sweep traces it, finds the missing ownership check (IDOR),
        shows the exact request that reads another user's data, gives the fix

you:  just cloned this thing and I'm lost, where do I even start
      → codebase-tour finds main, traces one request through the layers,
        tells you which file to open for what you're trying to change
```

## Examples

Want to see a skill's trigger and output shape before trying it on your own
repo? [`examples/`](examples/) has short, representative transcripts —
currently [git-rescue](examples/git-rescue.md),
[migration-guard](examples/migration-guard.md),
[env-detective](examples/env-detective.md),
[atomic-io](examples/atomic-io.md),
[tombstone](examples/tombstone.md),
[skew-check](examples/skew-check.md),
[job-warden](examples/job-warden.md),
[security-sweep](examples/security-sweep.md),
[changelog](examples/changelog.md),
[backfill-pilot](examples/backfill-pilot.md),
[stale-guard](examples/stale-guard.md),
[secret-spill](examples/secret-spill.md),
[ship-it](examples/ship-it.md),
[clock-sweep](examples/clock-sweep.md),
[codebase-tour](examples/codebase-tour.md),
[portability-audit](examples/portability-audit.md),
[devlog](examples/devlog.md), and
[readme-forge](examples/readme-forge.md) — every skill in the pack has one.

## Contributing

Got a skill that pulls its weight? Open a PR. The bar: it should be grounded (reads real state, doesn't guess), honest (no inflated output), and explain its reasoning so Claude does it well across many different repos — not just the one you tested on. One tight, well-triggered skill beats five vague ones.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the novelty-check bar, the `SKILL.md` house style, and how to test a skill locally before opening a PR.

## License

MIT — copy them, fork them, adapt them to your own workflow.
