# ship-it — example

**Trigger:**

> ok I think the rate-limit fix for `packages/api` is done, ship it

**Response shape:**

Claude looks for the project's own checks instead of assuming a command —
finds a pnpm workspace, so it doesn't reach for a blanket `pnpm test`:

```
This is a pnpm workspace (pnpm-workspace.yaml at the root). The diff only
touches packages/api/src/middleware/rateLimit.ts and its test file, so
I'll scope checks to that package rather than running the whole monorepo:

  pnpm --filter api... test
  pnpm --filter api... lint
  pnpm --filter api... typecheck
```

It runs them narrowest-first and hits a real failure — and fixes it instead
of reporting around it:

```
pnpm --filter api... typecheck → 1 error

  src/middleware/rateLimit.ts:42:7 - error TS2345: Argument of type
  'number | undefined' is not assignable to parameter of type 'number'.

  windowMs comes from an optional config field but is passed straight into
  setTimeout without a default. Fixing:

    -  const resetIn = windowMs;
    +  const resetIn = windowMs ?? DEFAULT_WINDOW_MS;

  Re-running: pnpm --filter api... typecheck → clean
  pnpm --filter api... test → 34 passed
  pnpm --filter api... lint → clean
```

Before writing the commit message it reads the actual staged diff — not
just what the user described — and flags something that doesn't belong:

```
One thing before I commit: there's a stray console.log(rateLimitState) on
line 58 left over from debugging. Want me to strip it, or is it intentional?
```

User confirms, Claude removes it, re-runs the affected test file, then
writes a conventional-commit message that matches the repo's existing
history (checked via `git log`, which uses `type(scope): summary`):

```
fix(api): default rate-limit window when config omits windowMs

Requests without an explicit windowMs hit setTimeout(undefined), which
silently disabled the reset timer and let the limiter never reopen for
that route. Fall back to DEFAULT_WINDOW_MS so an omitted config value
degrades to the documented default instead of wedging the limiter shut.
```

It stages and drafts but does not push — the user said "ship it," not
"push it," so committing is as far as it goes without an explicit
go-ahead — then hands back a PR-ready summary:

```
## What & why
Requests hitting the rate limiter with no explicit windowMs never got
their limit reset, effectively locking them out permanently. Falls back
to the documented default instead.

## Changes
- packages/api/src/middleware/rateLimit.ts: default windowMs via `??`
- packages/api/src/middleware/rateLimit.ts: removed a leftover debug log

## Verification
- pnpm --filter api... typecheck: clean (was 1 error, fixed)
- pnpm --filter api... test: 34 passed
- pnpm --filter api... lint: clean
- Did not run the full monorepo suite — this change doesn't touch shared
  config or a package other workspaces depend on, so it's scoped to `api`.

## Notes for the reviewer
- Didn't push; commit is staged locally pending your go-ahead.
```
