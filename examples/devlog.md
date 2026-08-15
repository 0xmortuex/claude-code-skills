# devlog — example

**Trigger:**

> devlog

(end of day, no other context given — the skill has to go find out what
actually happened)

**Response shape:**

Claude scans every top-level repo under REPOS_ROOT, skipping the journal
repo itself:

```
git -C shopcart log --since=midnight --author="mort" --all --oneline --no-merges
a3f9c2e fix(cart): stop double-charging on retry after gateway timeout
1b77e04 wip: idempotency key on the client (reverted this approach)

git -C infra-scripts log --since=midnight --author="mort" --all --oneline --no-merges
(no output)

git -C gitdiary  → skipped, this is the journal repo
```

`infra-scripts` had zero hits — it's dropped silently, not padded with "no
activity today" filler. `shopcart` gets the deeper look the setup calls for:

```
git -C shopcart log --since=midnight --stat
git -C shopcart status
```

The stat shows `1b77e04` touched `cart/client.js` and got reverted two
commits later in `a3f9c2e`, which took the fix server-side instead. `git
status` shows an uncommitted `metrics/retry-dashboard.json` — WIP that
won't show up in any diff but is real diary material.

**Write:**

```markdown
# 2026-08-15

**Repos touched:** shopcart

## What happened
- Fixed the cart double-charge on retry (shopcart a3f9c2e) — a gateway
  timeout was letting the client fire a second charge request before the
  first one's webhook landed.
- First tried an idempotency key generated client-side (1b77e04), but
  reverted it — a slow client could still generate two different keys
  for the same intended charge. Moved the dedup key server-side, keyed
  off the cart's pending-charge row instead.
- Started a small dashboard for retry counts, uncommitted — not shaped
  right yet.

## TIL
- The payment gateway's webhook can arrive *before* the HTTP response to
  the charge call that triggered it. Explains why the naive "charge then
  mark pending" ordering had a window at all.

## Tomorrow
- Finish the retry-count dashboard; wire it to the new server-side dedup
  key so retries are visible instead of inferred from logs.
```

`infra-scripts` never appears — nothing happened there, so nothing is
written. The reverted idempotency-key attempt stays in as a real beat
("tried X, didn't work, why, what replaced it"), not smoothed away because
the day's headline fix looks cleaner without it.

**Commit:**

```
cd gitdiary
git add entries/2026/08/2026-08-15.md
git commit -m "devlog: 2026-08-15"
git push
```

If `entries/2026/08/2026-08-15.md` already existed (a second session later
the same day), the new material would be merged into it instead of
overwritten — one entry per day, not one per session.
