# env-detective — example

**Trigger:**

> this test passes every time on my laptop but fails on every CI run, same
> commit:
>
> `expect(formatInvoiceDate(ts)).toBe('2026-03-09')` →
> `Expected: "2026-03-09", Received: "2026-03-08"`

**Response shape:**

Claude doesn't reread `formatInvoiceDate` — it confirms the commit matches
on both sides, then enumerates the delta instead of guessing:

```
Same SHA on both sides (a3f9c2e). Failure type is a date assertion, so
TZ/locale ranks first — checking the facts instead of assuming:

| Fact           | Local (macOS)     | CI (GitHub Actions)   |
|----------------|--------------------|------------------------|
| Node           | v20.11.0           | v20.11.0               |
| TZ             | America/New_York   | UTC (`TZ` unset)       |
| Lockfile       | committed, matches | `npm ci` from same lock|
| Locale         | en_US.UTF-8         | C.UTF-8                |

Toolchain and deps match — this is a timezone delta, not a version one.
`ts` is 2026-03-09T02:00:00-05:00 (10 PM EST Mar 8). In America/New_York
that's still Mar 8; in UTC it's already Mar 9 — which is what CI reports,
and it's CI that's correct. The test hardcodes the wrong expectation for
a UTC runner.
```

It proves the hypothesis with the cheapest discriminating experiment before
calling it done:

```
Confirming by toggling the one factor:

  TZ=America/New_York npx jest invoice.test.ts   → passes (the bug)
  TZ=UTC npx jest invoice.test.ts                 → fails the same way CI does

Flips cleanly on TZ alone — that's the proof, not a guess.
```

Then it fixes the class, not the one assertion:

```
The test asserts a timezone-dependent value without pinning a timezone,
so it'll pass or fail based on whoever's laptop runs it. Two options:

  1. If the app is meant to render in the invoice's own timezone, the
     test should construct the expectation from that same timezone
     explicitly, not rely on the runner's default.
  2. If the app is meant to always show UTC dates, pin `TZ=UTC` in the
     jest config (not just this file) so every date test in the suite
     stops depending on the runner's local timezone — one fix instead
     of finding this bug again in the next date test someone writes.
```

No "add `.skip` and revisit later," and no fifteen speculative CI commits —
one local experiment, TZ toggled, then the class-level fix.
