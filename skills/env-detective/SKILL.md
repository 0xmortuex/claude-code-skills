---
name: env-detective
description: Diagnose "works on my machine" divergence — a test/build that passes locally but fails in CI (or on a teammate's machine, or in Docker, or in prod) with the SAME code. Use whenever the user says "passes locally but fails in CI", "works for me but not for them", "only fails in Docker/on the server", "green here, red there", or shows a CI failure they can't reproduce. The bug is in the DIFFERENCE between the two environments, and this skill finds it by diffing environments systematically instead of rereading the code for the fifth time.
---

# env-detective

When the same commit behaves differently in two places, the code is the one thing you can rule out. The bug lives in the delta between the environments — and staring harder at the code (the instinctive move) cannot find it. The method: **enumerate the delta, rank it by base rates, and binary-search it with experiments.** Never speculate when you can diff.

## Step 1: pin down the actual failure

Get the *exact* failing output from the failing environment — the full CI log for the failing step, not the user's summary of it. Confirm both sides really run the same commit (`git rev-parse HEAD` vs the sha CI checked out — "it fails on CI" regularly turns out to be "CI runs main, I'm on my branch"). Note *what kind* of failure: different test result, compile error, missing file, hang, crash. Each points at a different slice of the delta.

## Step 2: enumerate the delta — collect facts, not vibes

Gather the same facts from both sides (locally: run the commands; for CI: read the workflow file, the runner image docs, and add a debug step printing them if needed):

- **Toolchain versions**: language runtime, package manager, compiler, relevant CLIs (`node -v`, `python -V`, `rustc -V`…). Minor versions count.
- **Dependency state**: does the lockfile fully pin, and does the failing side actually install from it (`npm ci` vs `npm install`)? Any `latest` tags, floating ranges, or caches restoring stale deps?
- **The tracked-files gap**: `git status --ignored` locally. CI builds from a *clean checkout*; your machine has gitignored files CI doesn't (`.env`, local config, generated code, fixtures someone never committed) and stale build artifacts CI rebuilds fresh. This single category explains an enormous share of cases — in both directions.
- **Environment variables & secrets**: which are set where; a var that's set locally and missing in CI fails, but so does the reverse (CI=true changes the behavior of many tools — test frameworks switch reporters, warnings become errors).
- **OS & filesystem**: Linux CI vs macOS/Windows laptop → case-sensitivity (`import './Utils'` finds `utils.ts` on your Mac, not on Linux), CRLF vs LF, path separators, `/tmp` semantics.
- **Locale, timezone, clock**: CI runners are UTC + `C` locale; laptops aren't. Date-formatting and sort-order tests are the classic casualties.
- **Execution shape**: parallelism and test order (CI shards or randomizes; a test polluted by a sibling only fails in one order), resource limits (OOM-killed processes die silently), missing network access, missing services (DB not started), headless vs display.
- **User & permissions**: root in Docker vs your user; file modes lost on Windows checkouts.

## Step 3: rank, then binary-search

Order hypotheses by base rate *for the observed failure type* (missing-file error → tracked-files gap first; date assertion → TZ/locale first; flaky only under CI → order/parallelism first). Then test the cheapest discriminating experiment, not the most plausible story:

- Reproduce CI's conditions locally, one at a time: `git clean -xdf` in a scratch clone (**warn the user before suggesting it on their real tree** — it deletes the very gitignored files you're investigating), `TZ=UTC LANG=C npm test`, run the tests in CI's order/shard, `act` or the same Docker image if available.
- Or bring your conditions to CI: pin the version, print the env, upload the intermediate artifact and diff it against your local one.
- Each experiment should split the remaining delta roughly in half. "Rerun and hope" is not an experiment.

## Step 4: prove it, then fix the class

You've found it when you can flip the failure on and off by toggling one factor — state that factor in one sentence. Then fix the *class*, not just today's instance: commit the missing file, pin the version in CI *and* the docs, set `TZ=UTC` in the test harness so the whole category dies, make the test order-independent. If the fix is "make local match CI", say whether the next teammate hits it too and how the fix prevents that.

## Boundaries

- Don't guess-and-push. Fifteen "try this?" CI commits is the failure mode this skill exists to prevent; experiments should be discriminating and mostly local.
- If the two sides genuinely can't be compared (no CI log access, can't rerun), say what's missing and what to instrument, instead of theorizing.
- Flaky-but-same-environment (fails 1 in 10 runs *in the same place*) is a race, not an environment delta — different diagnosis; say so and switch approaches.
