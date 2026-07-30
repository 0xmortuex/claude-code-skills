---
name: ship-it
description: Run the repo's own checks (tests, linter, type-checker, build), fix what breaks, then write a clean conventional-commit message and a review-ready summary of the diff. Use this whenever the user is about to commit, push, open a PR, or says "ship it", "commit this", "is this ready", "clean this up before I push", or otherwise signals they want work finalized — even if they don't name the individual steps. Also use it when someone asks you to verify a change is safe to land.
---

# ship-it

Turning "the code seems done" into "the code is actually ready to land" is a distinct skill, and it's the one people most often skip under time pressure. Your job here is to be the disciplined last pass: prove the change is green against the project's *own* standards, fix anything that isn't, and hand back a commit and summary a reviewer will trust.

## Why this matters

A change that passes on the author's machine but breaks CI wastes everyone's time and erodes trust in the author. The fix is not to guess — it's to run the exact checks the project already defines, because those are the checks the reviewer and CI will run. You are closing the gap between "looks done" and "is done" before anyone else sees it.

## The workflow

### 1. Discover the project's checks — don't assume them

Different projects, different commands. Look before you leap:

- **JS/TS:** read `package.json` `scripts` for `test`, `lint`, `typecheck`, `build`. Respect the lockfile (`pnpm`/`yarn`/`npm`).
- **Python:** look for `pytest`, `ruff`/`flake8`, `mypy`, and how they're wired (`pyproject.toml`, `tox.ini`, `Makefile`, `noxfile.py`).
- **Rust:** `cargo test`, `cargo clippy`, `cargo fmt --check`.
- **Go:** `go test ./...`, `go vet`, `gofmt -l`.
- **Anything:** a `Makefile`, `justfile`, `.pre-commit-config.yaml`, or a CI file (`.github/workflows/*`) is the source of truth for what "passing" means. Prefer the commands CI runs.
- **Monorepo:** look for `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, a root `package.json` with a `workspaces` field, a `go.work`, or a root `Cargo.toml` with a `[workspace]` table. Any of these means there are multiple packages, and a single top-level test/lint/build command is often either wrong (doesn't exist) or wasteful (rebuilds everything for a one-line change).

If you genuinely can't find any checks, say so rather than inventing them — running a made-up command that "passes" is worse than reporting there's nothing to run.

### 2. Run them, narrowest-relevant-scope first

Run the checks that cover the changed files first (fast feedback), then broaden. Report what you ran and the result plainly. Don't hide a failure behind optimistic phrasing.

**In a monorepo, scope to the packages you actually touched.** Running every package's suite because one file changed in one package is slow, and it's not even what most monorepo CI does — CI is usually scoped the same way. Map the changed files (`git diff --name-only` against the merge-base) to the package(s) that own them, then reach for the tool's native affected/filter mechanism instead of the blanket command:

- pnpm workspaces: `pnpm --filter <pkg>... test` (the `...` pulls in dependents)
- Nx: `nx affected -t test,lint,build`
- Turborepo: `turbo run test --filter=...[<base-branch>]`
- Lerna: `lerna run test --since <base-branch>`
- Yarn workspaces: `yarn workspaces foreach --since test`
- Cargo workspace: `cargo test -p <changed-crate>`
- Go workspace (`go.work`): `go test ./<changed-module>/...`

Broaden back to the full-repo command when the diff touches something shared — a root lint/tsconfig, a workspace-wide dependency bump, a shared package other packages depend on — since that's exactly the case where scoping to one package would miss real breakage elsewhere. If you can't confidently tell which packages are affected, say so and either run the full command or ask, rather than guessing a subset and reporting it as "checked."

### 3. Fix what breaks — then re-run

A failing test or type error is the task now. Fix it and run again. Repeat until green or until you hit something genuinely outside the change's scope (a pre-existing failure on the base branch) — in which case say exactly that, with the evidence, instead of silently ignoring it.

### 4. Review the diff before writing the message

Read the actual `git diff --staged` (or the working diff). The commit message must describe what the diff *does*, not what the user said they wanted — those can differ. Notice anything that shouldn't be in the commit: stray debug prints, a committed secret, an unrelated file, a `.env`. Flag those before committing, not after.

### 5. Write a conventional-commit message

Use the Conventional Commits format — it's the widest-adopted convention and it's what changelog tooling parses:

```
<type>(<optional scope>): <imperative summary, ≤72 chars>

<body: what changed and WHY, wrapped at ~72 cols. Explain the reasoning a
reviewer can't get from the diff itself. Reference issues if relevant.>
```

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`. Match the repo's existing history if it already uses a convention — consistency beats correctness-in-the-abstract. Check `git log` first.

**Example**
Diff: adds retry-with-backoff around the S3 upload call.
Message:
```
fix(upload): retry S3 puts with exponential backoff

Transient 503s from S3 were surfacing as hard upload failures. Wrap the
put in a 4-try backoff (1s/2s/4s) so a brief outage no longer drops a
user's file. Bounded so a real outage still fails fast enough to alert.
```

### 6. Hand back a review-ready summary

After committing, give the user a short summary they can drop into a PR:

```
## What & why
<1-3 sentences>

## Changes
- <the meaningful changes, not a file list>

## Verification
- <checks you ran and their result — e.g. "pytest: 214 passed", "ruff: clean", "tsc: no errors">

## Notes for the reviewer
- <anything worth a second look: a tradeoff, a follow-up, a deliberately-scoped-out item>
```

## Boundaries

- **Don't commit or push without the user's go-ahead** unless they've clearly asked you to. Staging and drafting the message is safe; the actual commit is theirs to trigger unless told otherwise.
- **Never** paper over a failure to reach "green." A skipped test reported as passing is a lie the reviewer inherits. If it's red, it's red — say why and either fix it or explain what's blocking.
- If checks take a long time, run the diff-relevant subset and say which broader suites you didn't run, so the user knows what CI still has to confirm.
