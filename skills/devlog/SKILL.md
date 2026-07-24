---
name: devlog
description: Turn today's REAL coding activity into a short dev-diary entry and commit it to a journal repo. Use when the user says "devlog", "write today's entry", "log today", "update my diary/journal", or wraps up a session with "note down what we did today". Grounded in actual git history across the user's repos — never invented; if nothing happened, it writes nothing. Great for learning-in-public, TIL streaks, and future-you archaeology ("when did I fix that and why?").
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

## Boundaries

- Only the user's own commits (`--author` filter) — a shared-repo teammate's work is not your diary.
- Private things stay private: if the journal repo is public, don't quote secrets, tokens, or client names from diffs into entries.
- This skill never rewrites history or touches the scanned repos — it reads them, and writes only to JOURNAL_REPO.
