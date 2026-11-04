# Backlog

Real, finishable improvements — the daily agent picks ONE and ships it end-to-end.
Rules: check items off when done, add follow-ups you discover, never do two at once.
The pack's bar for NEW skills: the problem must be real and verified uncovered by
prominent existing skills (research first, write second) — see README.

Full history before 2026-11-03 lives in two archive files, split so each stays under the
single-`Read` size limit: `docs/backlog-archive-2026-q3.md` (2026-07-24 to 2026-09-30) and
`docs/backlog-archive-2026-q4.md` (2026-10-01 to 2026-11-02). This file keeps only the rules
above, any currently unchecked items, and the most recent dated section(s). When checking
whether a candidate was already researched and rejected/shipped, `grep` across this file and
both archives.

## Research pass (2026-11-03): backlog fully checked off, no shippable item today — 3 new items added

Git hygiene check first: clone started with `main` detached 3 commits (`6740cce`, `a04950d`, `746e724`)
ahead of local `main`'s stale ref, all three already on `origin/main`. Fixed with `git checkout main &&
git merge --ff-only origin/main` (fast-forward, nothing to push for this part). `python tools/validate.py`
passed (`OK: 43 skills valid and consistent with README.`) before this pass. Confirmed every item above is
`[x]` — zero unchecked items anywhere in this file (`grep -c '\[ \]' BACKLOG.md` → 0) — so per the daily-
agent process, this round researches and logs new candidates rather than forcing a pick.

Two new-skill angles tried, both rejected:

1. **Feature-flag debt / stale-flag cleanup audit (flags left permanently on or off, dead flag branches
   never removed, flag evaluation forking behavior nobody remembers the reason for).** REJECTED, covered
   by a prominent official vendor. PostHog — not a random community repo, the actual PostHog product org —
   ships this under two names: `PostHog/posthog` → `products/signals/skills/signals-scout-unused-features/
   SKILL.md` (mirrored into `PostHog/posthog-foss`, `PostHog/ai-plugin`, `PostHog/skills`) and
   `PostHog/posthog.com` → `contents/learn/self-driving/pocket-guide/flag-debt/SKILL.md`. Both are live,
   maintained, and scoped to exactly this mechanic. Closed as covered — this is the `rollout-guard`
   mirror-image idea (that skill audits flags being *added* before launch; this would have audited them
   never being *removed* after), but the removal side is already a named, shipped skill elsewhere.
2. **"Does an unsubscribe/opt-out action actually suppress every list/sender it should" audit.** REJECTED,
   internal duplicate — not even a close call. `pref-guard`'s own description already states this exact
   mechanic almost verbatim ("does every current and future send path check live preference state, does
   provider-side unsubscribe/bounce data actually reach the app's suppression record"), down to the same
   CAN-SPAM/RFC-8058 one-click-unsubscribe-webhook-silently-stopped-firing failure mode this candidate was
   built around. No external research needed to kill this one — reading the pack's own skill table first
   would have caught it; logging the miss so the next round checks in-pack coverage before spending
   external-search budget.

One promising lead found, **not yet shippable — needs the full novelty sweep before it can ship**:

- [ ] **New-skill candidate: `clipboard-guard`? — sensitive-data clipboard exposure audit.** Does the app
  write passwords, OTPs, card numbers, API keys, or session tokens to the OS clipboard (explicit "copy"
  buttons, but also silent background reads/writes some apps do on every keystroke), and does it ever clear
  what it put there or shorten the OS's own clipboard-history retention of it. Real, dated, named incidents
  to ground it: the 2020 iOS 14 clipboard-access notification rollout publicly caught dozens of major apps
  (TikTok, LinkedIn, Reddit, and others, widely reported at the time) silently reading the clipboard on
  almost every keystroke, not just on paste; Android/Samsung cross-device clipboard sync has a documented
  OTP/password leakage path once a second device shares the same clipboard history. Partial research only:
  three targeted `gh api search/code` passes this round (`"clipboard" "sensitive" filename:SKILL.md`,
  `"clipboard" "OTP" filename:SKILL.md`, `"clipboard" "password manager" "autoclear" filename:SKILL.md`)
  found clipboard exposure mentioned only as one checklist bullet inside broad mobile-pentest skills
  (`Masriyan/Claude-Code-CyberSecurity-Skill` → `17-mobile-security`, `jd-opensource/JoySafeter` →
  `pentest-mobile-app`, both under MASVS-STORAGE) — not a dedicated audit skill the way `jwt-jti-blocklist-
  design` or `audit-monetization-iap` killed earlier candidates. That's a promising novelty signal, but this
  round did not run the full process this pack's bar requires (WebSearch across claudskills/mcpmarket/
  lobehub/crossaitools/smithery, `obra/superpowers`, `anthropics/skills`, and the awesome-claude-code lists)
  before concluding it's clear. **Next run: finish that sweep before writing `SKILL.md`; if it survives,
  check it isn't better framed as a bullet added to `security-sweep` or `secret-spill` than a 44th standalone
  skill** (this pack's own house style prefers folding a thin, single-bullet-sized finding into an existing
  skill over a kitchen-sink new one — weigh that here).

Two process/maintenance items found and logged, both real and self-contained enough to finish in one run:

- [x] **This file (`BACKLOG.md`) has outgrown a single read.** It's now 3888 lines / ~346 KB — confirmed
  directly this round: `Read` on the whole file errored with "File content (345.3KB) exceeds maximum
  allowed size (256KB)" and had to be worked around with `head`/`grep`/`tail` instead. Every future daily
  run pays this tax just to find today's `## Note for the next run` section. **Done 2026-11-04**: split
  into `docs/backlog-archive-2026-q3.md` (2026-07-24 to 2026-09-30, 176KB) and
  `docs/backlog-archive-2026-q4.md` (2026-10-01 to 2026-11-02, 178KB) — see that day's section below for
  the full writeup.
- [ ] **Drift-audit queue has due dates only in prose, not as checkable items.** `reaccept-guard` (shipped
  2026-10-26), `throttle-guard` (2026-10-28), `quote-guard` (2026-10-29), and `recall-guard` (2026-11-01)
  are each meant to get a fact-check pass "once a couple of weeks have passed" — but that's only ever been
  written as a prose reminder at the bottom of each day's section, never as a trackable item, which is why
  this file has gone from 2026-07-24 to today with **zero** literal `- [ ]` lines anywhere until this round.
  None of the four are due yet as of 2026-11-03 (earliest, `reaccept-guard`, turns 2 weeks old 2026-11-09).
  Add real due-dated checkbox items when each one actually comes due (`reaccept-guard` ~2026-11-09,
  `throttle-guard` ~2026-11-11, `quote-guard` ~2026-11-12, `recall-guard` ~2026-11-15) instead of carrying
  the reminder forward as prose again.

Follow-up for the next run: three real unchecked items now exist above for the first time in this file's
history — pick among them per the normal value-to-size rule (the `BACKLOG.md` split is the most clearly
finishable in one sitting; `clipboard-guard` needs real research time before it can ship; the drift-audit
items aren't due yet). No skill shipped this round — this was a research-and-log pass, not an implementation
one, per the daily-agent process for a fully-checked-off backlog.

## `BACKLOG.md` split into quarterly archives (2026-11-04)

Picked the file-outgrown-a-single-read item logged yesterday — it was flagged as "the most clearly
finishable in one sitting," needed no external research, and `clipboard-guard` (the other open lead)
still needs the full novelty sweep this pack requires before it can ship.

What moved: everything between the top rules paragraph and the 2026-11-03 section — i.e. `## Pack
quality` through the end of `## Maintenance pass (2026-11-02)` (original lines 8–3889) — split at the
2026-09-30/2026-10-01 boundary into `docs/backlog-archive-2026-q3.md` (176KB) and
`docs/backlog-archive-2026-q4.md` (178KB), each a straight `sed` cut-and-paste (no rewriting or
summarizing) with a one-paragraph header naming what it is and pointing back to `BACKLOG.md` and the
sibling archive. `BACKLOG.md` itself now keeps only: the rules paragraph, a pointer to both archives,
the full 2026-11-03 section (so the two items it logged stay visible and checkable), and this section.
Checked off the split item itself above rather than leaving it dangling in yesterday's section.

Why two files instead of one `docs/backlog-archive.md` (the first option the 2026-11-03 note offered):
tried the single-file version first and it came out to ~345KB — still over the 256KB `Read` limit, so
it would have just moved the same problem one file over. Splitting at the quarter boundary (the natural
seam in the dated section headers) landed both halves comfortably under the limit with no further cuts
needed.

Verification: `python tools/validate.py` → `OK: 43 skills valid and consistent with README.` (this
change touches no skill files, so this mainly confirms the validator doesn't scan `BACKLOG.md`/`docs/`
and nothing else regressed). Checked the move is lossless with `diff` directly rather than trusting a
grep count (a count can match by coincidence): `diff <(sed -n '8,1851p' <pre-split BACKLOG.md>)
<(tail -n +9 docs/backlog-archive-2026-q3.md)` and the same for the 1852–3889 range against
`backlog-archive-2026-q4.md` — both report the archive as the moved range plus only the new header's
blank/`---` lines, i.e. the historical body text is byte-for-byte unchanged. Also confirmed no other
file references `docs/backlog-archive.md` under the old undecided single-file name, and that
`README.md`'s only mention of `BACKLOG.md` is a generic "see BACKLOG.md" pointer that didn't need
updating.

Follow-up for the next run: the drift-audit-due-dates item (logged 2026-11-03, still unchecked above)
isn't due yet — earliest is `reaccept-guard` ~2026-11-09. `clipboard-guard` still needs the full
novelty sweep (WebSearch across claudskills/mcpmarket/lobehub/crossaitools/smithery, `obra/superpowers`,
`anthropics/skills`, awesome-claude-code) before it can ship or get folded into `security-sweep`/
`secret-spill`. If both of those are still not actionable next run, do a fresh novelty-research pass
per the normal fully-checked-off-backlog process rather than inventing busywork.
