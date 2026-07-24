---
name: clock-sweep
description: Audit code for datetime and timezone correctness — naive/aware mixing, local-time storage, DST-unsafe arithmetic, server-timezone assumptions, date-vs-instant confusion. Use when the user reports a time-related bug ("times are off by an hour/a day", "wrong date for some users", "broke after DST"), stores or schedules anything time-based, or asks "handle timezones properly". Also use proactively when you see `datetime.now()`, `new Date()` without a zone, or epoch±86400 arithmetic in code you're already touching. Time bugs are silent — the code runs and returns plausible values for the wrong moment — so audit systematically, never spot-fix.
---

# clock-sweep

Time bugs are the quietest bug class in software: nothing crashes, tests pass on the author's machine, and the wrong answers look right — until a user in another timezone, a DST transition, or a date boundary at midnight UTC exposes them. And they're rediscovered twice a year, every year. The root cause is almost always the same category error: treating **instants** (a point on the global timeline), **wall-clock times** (what a clock on a wall in some place reads), and **calendar dates** (no time at all) as interchangeable. The audit finds every place the code blurs them.

## The three types — get this straight first

- **Instant**: "the meeting started" — a global point. Store as UTC (ISO-8601 with offset, or epoch). Timezone is a *display* concern.
- **Future wall-clock time**: "9:00 on March 14 in Istanbul" — NOT an instant, because the zone's rules can change between now and then. Store as local time + IANA zone name (`Europe/Istanbul`), never as a precomputed UTC instant and never with a fixed offset (`+03:00` is a fact about one moment, not a place).
- **Calendar date**: "born 2011-05-02" — has no timezone. Storing it as midnight-anything makes it shift a day for half the planet. Keep it a date type end-to-end.

Most bugs are one sentence long when named: "this stores a future wall-clock time as a UTC instant", "this treats a date as an instant".

## The sweep

Grep the whole surface, not the file the bug was reported in — the same mistake repeats wherever the same developer habits ran. Sweep for, per language family:

1. **Naive now**: `datetime.now()`/`datetime.utcnow()` (both naive in Python — want `datetime.now(timezone.utc)`), `new Date()` fed into date *formatting* without an explicit zone, `LocalDateTime.now()` in Java where an `Instant` is meant. Every hit inherits the *server's* timezone — code that changes behavior when the host or `TZ` env changes.
2. **DST-unsafe arithmetic**: `+ 86400`, `+ 24*60*60*1000`, `addHours(24)` used to mean "next day". A day is 23 or 25 hours twice a year in DST zones; "same time tomorrow" must be computed in the zone's calendar, not on the epoch line.
3. **Offset-as-zone**: stored `+02:00`-style offsets, `getTimezoneOffset()` captured once and reused, hardcoded offset maps. Offsets change with DST and legislation; only IANA names are stable.
4. **Serialization boundaries**: bare `YYYY-MM-DD HH:MM:SS` strings crossing APIs or landing in DB columns with no zone info — every reader guesses differently. Also DB column types: `timestamp` vs `timestamptz` in Postgres behave completely differently.
5. **Boundary logic**: "today's records" computed in UTC for a user in another zone; day/week/month bucketing in analytics; expiry checks comparing naive to aware (Python raises; JS silently coerces).
6. **Tests pinned to the developer's clock**: assertions that pass only in one zone or only outside DST transitions.

For each hit, classify against the three types and state which one the code *meant*.

## Fix patterns

- Instants: normalize to UTC at every input boundary, convert to the *user's* zone (not the server's) at every display boundary, nothing in between touches zones.
- Scheduling/recurrence: compute in the target zone with a real tz library (`zoneinfo`, `Temporal`/date-fns-tz, `java.time`), then convert to an instant at the last moment; recomputed, not stored, for far-future events.
- Dates stay dates: date columns, date types, no midnight smuggling.
- Make the fix systematic: if the sweep found the pattern 12 times, the fix is 12 edits plus (where feasible) a lint rule or a banned-API wrapper so the 13th never lands.

## Verify under hostile clocks

The suite that always passes at UTC on CI proves nothing. Run the tests (or at least the touched modules) under: `TZ=Pacific/Chatham` (+12:45, DST — breaks almost everything wrong), `TZ=America/New_York`, and with test times pinned *at* a DST transition (e.g. the missing 02:30 on a spring-forward day) and at month/year boundaries. If the harness supports frozen clocks, add a transition-crossing case to lock the fix in.

## Boundaries

- Sweep completeness is the whole point: report the total hit count and check off every one — partially-fixed time handling is often worse than untouched, because now two conventions coexist.
- Don't convert stored data (a DB full of naive local timestamps) without flagging it as a *data migration* with its own risks — that's a separate, careful operation, not a code edit.
- If requirements are genuinely ambiguous ("daily report" — whose midnight?), surface the product question instead of picking silently; the answer changes the implementation.
