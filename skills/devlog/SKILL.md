---
name: devlog
description: Turn today's REAL coding activity into a short dev-diary entry and commit it to a journal repo. Use when the user says "devlog", "write today's entry", "log today", "update my diary/journal", or wraps up a session with "note down what we did today". Also handles "devlog week", "weekly rollup", or "summarize this week", which distills the week's already-written daily entries into one summary instead of re-reading git history. Grounded in actual git history and past entries — never invented; if nothing happened, it writes nothing. Great for learning-in-public, TIL streaks, and future-you archaeology ("when did I fix that and why?").
---

# devlog

A dev diary is only worth keeping if it's true and cheap. This skill makes it both: it reads what *actually happened* in git today across the user's repos and distills it into a short entry a human would enjoy rereading in six months. The entry is evidence-backed prose, not ceremony — and the daily commit it produces is a real contribution, because the diary content is real.

## Setup (first run only)

Two paths, configured by editing this file — defaults:

- **JOURNAL_REPO**: `~/Documents/GitHub/gitdiary` — the repo entries are committed to, as `entries/YYYY/MM/YYYY-MM-DD.md`
- **REPOS_ROOT**: `~/Documents/GitHub` — the directory scanned for today's activity

If JOURNAL_REPO doesn't exist on first run, offer to create it (a bare README + `entries/` is enough).

## Gather — evidence before prose

For each git repo under REPOS_ROOT (top-level dirs; skip the journal repo itself):

```bash
git -C <repo> log --since=midnight --author="$(git config user.name)" \
    --all --oneline --no-merges
```

For repos with hits, go deeper: `git log --since=midnight --stat` for shape, and read the most significant diffs enough to describe them truthfully. Also worth capturing when present: current uncommitted work (`git status` — "WIP: half-done X" is honest diary material), and anything notable from the current session's own context (a bug chased for two hours that ended in a one-line fix is the *best* diary material and may not show in any diff).

## Write — the entry format

`entries/YYYY/MM/YYYY-MM-DD.md`, target length 10–25 lines. Voice: first person, plain, specific — written for future-you, not an audience you're performing for.

```markdown
# 2026-07-24

**Repos touched:** mortnet, Mort

## What happened
- Landed the RTL8139 RX ring (mortnet 9b66698) — the CAPR-minus-16
  quirk cost an hour; the datasheet buries it in a footnote.
- Started on ICMP replies; checksum folding works, dispatch is WIP.

## TIL
- QEMU's SLIRP answers ARP for 10.0.2.2 itself — you never see a
  real gateway MAC. Explains yesterday's "wrong" capture.

## Tomorrow
- Wire net_handle_frame into the kernel main loop first — everything
  else is blocked on it.
```

Sections are optional except the first — drop TIL/Tomorrow when there's nothing real to put in them. Every claim traces to a commit, diff, or this session's transcript. Commit refs like `(repo abc1234)` make entries greppable archaeology later.

**The anti-slop rules:**
- Nothing happened today → no entry. Say so; don't manufacture one. (A genuinely quiet day with one real thought is fine as two lines; padding is not.)
- Never inflate: "tried X, didn't work, reverted" is a *good* entry. Failed approaches and dead ends are the most valuable thing a diary captures, because they're exactly what future-you forgets.
- Don't restate commit messages — the diary adds what the log can't: why, what fought back, what was learned.

## Commit

In JOURNAL_REPO: `git add` the entry, commit as `devlog: YYYY-MM-DD`, and push if a remote exists. One entry per day — if today's already exists, *append/merge* into it rather than overwriting (sessions happen more than once a day).

## Weekly rollup (`devlog week`)

Triggered by "devlog week", "weekly rollup", "summarize this week", or similar. This is a *synthesis* of entries already written, not a fresh git dig — the daily entries are the source of truth, so read those, not the repos again.

1. **Gather.** Find the daily entries for the last 7 days (today back through 6 days ago), which may span two `entries/YYYY/MM/` folders if the week crosses a month boundary. Skip missing days silently — a devlog streak has gaps, and that's fine.
2. **If zero entries exist for the window**, say so and write nothing — same anti-invention rule as the daily entry.
3. **Write** to `entries/weekly/YYYY-Www.md` (ISO week number, e.g. `entries/weekly/2026-W30.md`) — a separate top-level folder, not `entries/YYYY/MM/`, so the week's file never collides with a day and never has to pick one of two months when the week spans a boundary.

```markdown
# Week 2026-W30 (Jul 21–27)

**Days logged:** 4/7 · **Repos touched:** mortnet, Mort

## Threads
- RTL8139 RX ring landed Mon, ICMP replies started Wed — still WIP Fri
  ("dispatch is WIP" carried over three days running).

## TIL, worth keeping
- QEMU's SLIRP answers ARP for 10.0.2.2 itself (Wed).

## Open into next week
- <pulled from the last daily entry's "Tomorrow" section, if present>
```

Group by theme/thread across the week rather than re-listing each day verbatim — the value of a rollup is compression, not concatenation. A thread mentioned in multiple days' entries (like a WIP feature) becomes one line noting progression, not three repeated bullets. Commit as `devlog: week of YYYY-MM-DD` (Monday's date) in the same JOURNAL_REPO commit/push flow as the daily entry.

## Boundaries

- Only the user's own commits (`--author` filter) — a shared-repo teammate's work is not your diary.
- Private things stay private: if the journal repo is public, don't quote secrets, tokens, or client names from diffs into entries.
- This skill never rewrites history or touches the scanned repos — it reads them, and writes only to JOURNAL_REPO.
