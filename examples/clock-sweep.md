# clock-sweep — example

**Trigger:**

> users in Sao Paulo say their "remind me in 24 hours" reminders keep
> firing an hour early or an hour late around the start of November. code
> is in `reminders/scheduler.py`. can you sort out our timezone handling?

**Response shape:**

Claude doesn't spot-fix the one report — it sweeps the whole surface for
the same developer habit, per the skill's "grep the whole surface, not the
file the bug was reported in" instruction:

```
Sweeping reminders/, api/notifications/, and workers/ for the three
category errors (naive now, DST-unsafe arithmetic, offset-as-zone):

  reminders/scheduler.py:41   fire_at = created_at + timedelta(hours=24)
  reminders/scheduler.py:88   next_daily = last_sent + timedelta(days=1)
  api/notifications/create.py:19   sent_at = datetime.now()
  workers/digest.py:33        window_start = datetime.now() - timedelta(days=7)

4 hits. All four are the same root mistake wearing different clothes:
epoch arithmetic standing in for calendar arithmetic, and the server's
local clock standing in for an explicit zone.
```

It classifies each hit against the three types before touching code —
per the skill, a fix without this step just relocates the bug:

```
scheduler.py:41 — "remind me in 24 hours" is an instant offset from
another instant (created_at). This one is actually correct as epoch
math... IF created_at is a tz-aware UTC instant. It isn't — `created_at`
is written by api/notifications/create.py:19's naive `datetime.now()`,
which silently takes the server's local zone (America/Sao_Paulo). So the
bug isn't the +24h line, it's upstream: a naive wall-clock time is being
fed into instant arithmetic, and Sao Paulo's Nov DST transition (clocks
spring forward, losing an hour) shifts what "24 hours later" means
relative to the reported reminder time.

scheduler.py:88 — different type, same wrong arithmetic. "Same time
tomorrow" for a daily reminder is a FUTURE WALL-CLOCK TIME, not an
instant — must be computed as calendar-day-plus-one in the user's zone,
then converted to an instant. `timedelta(days=1)` on an instant is wrong
by construction on any DST-transition day, independent of the naive-now
bug above.

api/notifications/create.py:19 — naive now, the root cause upstream of
scheduler.py:41.

workers/digest.py:33 — naive now again; "last 7 days" window computed in
whatever zone the host happens to be running in, not the user's.
```

The fix section matches the sweep one-for-one — no partial fixes, per the
skill's "partially-fixed time handling is often worse than untouched":

```
1. api/notifications/create.py:19
   - sent_at = datetime.now()
   + sent_at = datetime.now(timezone.utc)

2. scheduler.py:41 (fixed transitively by #1, plus made explicit)
   - fire_at = created_at + timedelta(hours=24)
   + fire_at = created_at + timedelta(hours=24)  # created_at now tz-aware UTC;
     comment left because instant+duration is correct ONLY because this is a
     relative "in N hours" reminder, not a wall-clock one — see #3 for the
     contrast case

3. scheduler.py:88 — recurrence must be computed in the user's zone
   - next_daily = last_sent + timedelta(days=1)
   + user_tz = ZoneInfo(user.timezone)
   + local_next = last_sent.astimezone(user_tz) + timedelta(days=1)
   + local_next = local_next.replace(hour=last_sent.astimezone(user_tz).hour,
                                      minute=0, second=0, microsecond=0)
   + next_daily = local_next.astimezone(timezone.utc)
   # computed at send time, not stored precomputed far in advance — the
   # zone's rules (or the user's saved zone) can still change before then

4. workers/digest.py:33
   - window_start = datetime.now() - timedelta(days=7)
   + window_start = datetime.now(timezone.utc) - timedelta(days=7)
```

Verification follows the skill's "hostile clocks" step rather than trusting
green CI at UTC:

```
Ran reminders/ and workers/digest tests under:
  TZ=America/Sao_Paulo  (the reporting user's zone, Nov 1 2026 DST start)
  TZ=Pacific/Chatham    (+12:45, DST — breaks almost anything that's wrong)
  TZ=UTC                (the CI default — the one that was hiding this)

Added one new case pinned at the Sao Paulo transition instant (2026-11-01
00:00 local, clocks jump to 01:00): a daily reminder due to fire at
00:00 local on transition day now fires at the correct 03:00 UTC instant
instead of drifting an hour, and the "in 24 hours" instant reminder is
unaffected (it was never wrong once created_at was fixed).

Data note: existing rows in `reminders.created_at` written by the old
naive datetime.now() are ambiguous — they're local time with no recorded
zone, not wrong-but-fixable in place. Flagging as a separate backfill
question (which zone was the server in when each row was written?) rather
than guessing during this fix.

## Verdict: 4/4 hits fixed. 1 fix (scheduler.py:88) required computing in
the user's zone rather than epoch arithmetic — the other 3 were the
naive-now root cause and its direct consequence. Data migration for
historical ambiguous timestamps is out of scope for this pass — surfaced,
not silently done.
```
