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

## Drift-audit: `email-guard` fact-check, due on schedule (2026-11-27)

Git hygiene first: clone's `HEAD` was detached at `7522d97` (yesterday's `digest-guard` drift-audit
commit) while the local `main` ref was stale at `ef3a390`, three commits behind. `git fetch origin
main` confirmed `origin/main` was already at `7522d97` — the prior three days' commits had all
pushed fine, only the local `main` ref hadn't been fast-forwarded (same recurring issue the last two
rounds hit). Fixed with `git checkout main && git merge --ff-only 7522d97` (clean fast-forward, no
conflict). `python tools/validate.py` passed (`OK: 57 skills valid and consistent with README.`)
before this round.

Confirmed zero unchecked items (`grep -n '^- \[ \]' BACKLOG.md` → no matches) and that `email-guard`
(shipped 2026-11-13) was the next drift-audit due per yesterday's own follow-up note — due
~2026-11-27, today, exactly on schedule.

Delegated independent re-verification of `email-guard`'s two grounding claims to a subagent (kept the
WebSearch output out of context), instructed to check primary sources rather than secondary
summaries. **Both held up — nothing drifted:**

- **GitLab CVE-2018-19580** (gitlab-org/gitlab-ce#39809) — REAL-AND-MATCHES. Confirmed via NVD,
  Ubuntu Security, Debian Security Tracker, and GitLab's own 11.5.1 security-release notes. GitLab
  changed a user's email with no notification sent to the *old* address, letting a session-hijack
  account-takeover go unnoticed by the real owner. Fix versions confirmed exactly: 11.5.1 / 11.4.8 /
  11.3.11. CVSS 5.3 medium (Ubuntu) is consistent with a missing-signal bug rather than a
  direct-exploit one, matching how the skill frames it.
- **Flowise GHSA-x39m-3393-3qp4** — REAL-AND-MATCHES, with one useful nuance to record: this advisory
  is now also tracked as **CVE-2025-71337** (CWE-620, Unverified Password Change), confirmed via NVD,
  VulnCheck, and the GitHub advisory itself. Mechanic matches exactly: an authenticated user could
  change the account email with no verification step, and since email doubles as login/recovery
  address, that's a direct account-takeover path. Affected versions converge on Flowise < 3.0.10. No
  dispute or retraction found on either claim. Noting the CVE cross-reference here so a future audit
  round searching by CVE number rather than GHSA ID doesn't wonder if it's a different issue — it
  isn't.

No change needed to `skills/email-guard/SKILL.md`. `python tools/validate.py` →
`OK: 57 skills valid and consistent with README.` (unchanged — this round touched no skill files,
only `BACKLOG.md`).

Follow-up for the next run: with `email-guard` checked off the due-dates list, the next drift-audit
due is `revoke-guard` (shipped 2026-11-16) ~2026-11-30 — still 3 days out, too soon for tomorrow. No
unchecked new-skill candidates remain, so if no audit is due tomorrow (2026-11-28), the next round
should run a fresh novelty/research pass rather than force a pick or invent busywork. Remaining
due-dates queue after `revoke-guard`: `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard`
(2026-11-18) ~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04, `payout-guard` (2026-11-21)
~2026-12-05, `disconnect-guard` (2026-11-22) ~2026-12-06, `lockscreen-guard` (2026-11-24) ~2026-12-08,
`elevate-guard` (2026-11-25) ~2026-12-09.

## Drift-audit: `digest-guard` fact-check, due on schedule (2026-11-26)

Git hygiene first: clone's `HEAD` was detached 2 commits ahead of the local `main` branch ref — at
`7f0a4af` (`elevate-guard`, 2026-11-25) with `7c83405` (`lockscreen-guard`, 2026-11-24) in between —
while local `main` was stale at `ef3a390`. `git fetch origin main` confirmed `origin/main` was
already at `7f0a4af`, i.e. both prior days' commits had pushed fine; only the local `main` ref
hadn't been fast-forwarded. Fixed with `git checkout main && git merge --ff-only 7f0a4af` (clean
fast-forward, no conflict, nothing to push for that step alone). `python tools/validate.py` passed
(`OK: 57 skills valid and consistent with README.`) before this round.

Confirmed zero unchecked items anywhere in this file (`grep -n '^- \[ \]' BACKLOG.md` → no matches),
so per process checked the drift-audit due-dates list instead of forcing a pick or inventing
busywork: `digest-guard` (shipped 2026-11-12) was due ~2026-11-26 — today, exactly on schedule, not
early like the last several audits — so ran its fact-check rather than starting a fresh
novelty-research pass.

Delegated independent re-verification of `digest-guard`'s three grounding claims to a subagent
(kept the WebSearch output out of context), instructed to check primary sources (NVD/GHSA, the
vendor's own docs) rather than secondary summaries. **All three held up — nothing drifted:**

- **Metabase CVE-2023-23629** (GHSA-ch8f-hhq9-7gv5) — REAL-AND-MATCHES. NVD/GHSA confirm a
  lower-privileged user viewing a dashboard could add themselves as a recipient of another user's
  existing subscription and receive the creator's unfiltered data by email; fix versions
  (0.43.7.1/0.44.6.1/0.45.2.1 and the 1.x equivalents) match exactly.
- **Metabase CVE-2023-23628** (GHSA-492f-qxr3-9rrv) — REAL-AND-MATCHES. Confirmed as the sibling
  advisory: a sandboxed user could see the recipient list of someone else's dashboard subscription.
- **Splunk's own documentation** on scheduled report/alert permissions
  (`docs.splunk.com`/`help.splunk.com`, Report/Managereportpermissions, mirrored current across
  9.0–10.6) — REAL-AND-MATCHES, still live at the same page: changing a scheduled report's
  permissions applies only to future-generated jobs, already-queued jobs keep their old grant until
  changed separately via the job manager, and scheduled reports/alerts can only run as Owner —
  matches the skill's framing exactly, no version has changed this behavior since.

No change needed to `skills/digest-guard/SKILL.md`. `python tools/validate.py` →
`OK: 57 skills valid and consistent with README.` (unchanged — this round touched no skill files,
only `BACKLOG.md`).

Follow-up for the next run: with `digest-guard` checked off the due-dates list, the next drift-audit
due is `email-guard` (shipped 2026-11-13) ~2026-11-27 — due tomorrow. After that: `revoke-guard`
(2026-11-16) ~2026-11-30, `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard`
(2026-11-18) ~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04, `payout-guard` (2026-11-21)
~2026-12-05, `disconnect-guard` (2026-11-22) ~2026-12-06, `lockscreen-guard` (2026-11-24)
~2026-12-08, `elevate-guard` (2026-11-25) ~2026-12-09. No unchecked new-skill candidates remain —
if `email-guard`'s audit turns out too soon to run tomorrow, the next round should do a fresh
novelty/research pass rather than invent busywork, per standing process.

## Shipped `elevate-guard`, resolving the distinctness call left open since 2026-11-23 (2026-11-25)

Git hygiene first: `HEAD` was detached one commit ahead of the local `main` branch ref, at `7c83405`
(yesterday's `lockscreen-guard` commit) — but `git fetch origin main` showed `origin/main` was
already at `7c83405` too, so the commit itself had been pushed fine; only the local `main` ref was
stale. Fixed with `git checkout main && git merge --ff-only 7c83405` (clean fast-forward, no
conflict, nothing to push for that step). `python tools/validate.py` passed (`OK: 56 skills valid
and consistent with README.`) before this round. Confirmed via `grep -n '^- \[ \]' BACKLOG.md` that
zero items use the unchecked-box marker — this pack's checkbox marks "cleared the research bar," not
"shipped," so the real signal is prose: `elevate-guard` was the one candidate still described as "not
yet drafted" (see 2026-11-23's and 2026-11-24's follow-up notes), carried since 2026-11-23 specifically
because it needed a deliberate distinctness call against `revoke-guard`/`rotation-guard`/
`disconnect-guard` before drafting rather than an assumed one. No drift-audit is due yet: the earliest,
`digest-guard` (2026-11-12), comes due ~2026-11-26, still 1 day out.

Delegated independent re-verification of both grounding claims and a fresh novelty check to a
subagent (kept the WebSearch/`gh api search/code` output out of context), explicitly withholding the
ship/reject call from it so the distinctness judgment stayed mine rather than inherited. Both
grounding sources held up as REAL-AND-MATCHES, not just loose shape-matches: **CVE-2024-1764**
(Devolutions Server ≤2023.3.14.0, DEVO-2024-0002, CWE-269 improper privilege management, published
2024-03-05) — NVD's own description: the JIT elevation module could "allow a user to keep elevated
privileges after they expire, under specific circumstances," confirmed verbatim against NVD (severity
sources disagree slightly, Tenable CVSS 8.8 vs. PT Security 7.6, which doesn't affect the mechanic
match). And AWS's own Security Blog post on implementing JIT privileged access via Microsoft Entra
PIM + AWS IAM Identity Center — the subagent surfaced the exact sentence via WebSearch (couldn't
`WebFetch` aws.amazon.com directly, host not in this session's network allowlist): "active sessions
are not terminated when the Entra PIM activation maximum duration has been reached," an exact quote
match, not a paraphrase. Fresh novelty check (`gh api search/code`, five phrasings) found no dedicated
audit skill: only JIT/PIM/break-glass *build/setup* skills (confirmed by reading
`implementing-just-in-time-access-provisioning` in full — explicitly framed around designing and
deploying JIT, not auditing an existing deployment) and bulk-generated generic IAM/PAM checklists.
Read two of the closest checklist hits (`UnitOneAI/SecuritySkills` → `privileged-access` and
`iam-review`) in full, not just their snippets: each contains one generic row naming the symptom
("no automatic revocation — elevated access persists after timeout") but neither asks whether expiry
is enforced at the authorization-check layer or demands evidence the revocation job actually runs —
the same "a templated checklist names the symptom generically, doesn't address the mechanic" pattern
`lockscreen-guard`'s round already judged as not blocking a ship, applied consistently here.

Resolved the distinctness call myself (the one thing withheld from the subagent) by reading
`revoke-guard`, `rotation-guard`, and `disconnect-guard`'s full `SKILL.md` text, not just their shared
CWE-613-adjacent vocabulary: `revoke-guard` audits an *already-open, continuous* WebSocket session's
authorization staying current while connected — its object is a live connection, and the trigger is
someone else's revoking action. `disconnect-guard` audits a *permanent*, user-initiated revocation of
a third-party OAuth grant with no expiry designed into it at all — the only question is whether the
kill switch is wired to anything. `rotation-guard` audits propagating an operational credential to a
*new value* across consumers with a sized overlap window — there's no new value here and nothing to
propagate. `elevate-guard`'s object is none of these: a grant that is designed to end *on its own*, by
a clock, checked on ordinary (often stateless, per-request) authorization calls rather than a
persistent connection, with no revoke click and no new value — only a deadline and a job that has to
notice it. Also checked `seat-guard`, the one other skill using "just-in-time" in-pack: its JIT refers
to SSO *account provisioning* on first login, an unrelated meaning with no overlap. Wrote this
reasoning directly into the `SKILL.md`'s Boundaries section rather than leaving it implicit, matching
the precedent `disconnect-guard`'s round set for exactly this kind of objection.

Added `skills/elevate-guard/SKILL.md` and `examples/elevate-guard.md`; wired into `README.md`'s
skills table, decision table, Examples list, and intro "survived" sentence, and `examples/README.md`.
Bumped the 56→57 skill-count mentions (prose word and the "copying all fifty-six/fifty-seven" tip).
`python tools/validate.py` → `OK: 57 skills valid and consistent with README.` Checked the
one-directional cross-reference convention other recent skills follow (`grep -n "elevate-guard"
skills/*/SKILL.md` outside its own file returns nothing) and matched it — this skill's own Boundaries
section names `revoke-guard`, `disconnect-guard`, and `rotation-guard`; none of theirs needs to name
it back.

Follow-up for the next run: the backlog has no other real open candidate right now — this was the
last one carried from the 2026-11-23 research pass. Per process, next round should do a fresh
novelty/research pass rather than invent busywork, unless a drift-audit comes due first. Next
drift-audit due dates: `digest-guard` (2026-11-12) ~2026-11-26 (1 day out — likely due next round),
`email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16) ~2026-11-30, `subscription-guard`
(2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18) ~2026-12-02, `mention-guard` (2026-11-20)
~2026-12-04, `payout-guard` (2026-11-21) ~2026-12-05, `disconnect-guard` (2026-11-22) ~2026-12-06,
`lockscreen-guard` (2026-11-24) ~2026-12-08.

## Shipped `lockscreen-guard`, the readier of yesterday's two candidates (2026-11-24)

Git hygiene first: `git status`/`git log --oneline -10` showed `main` already at `ef3a390`
(yesterday's novelty-pass commit) with a clean working tree and nothing to fast-forward — no
detached-HEAD or stale-branch issue this round. `python tools/validate.py` passed (`OK: 55 skills
valid and consistent with README.`) before this round. No drift-audit is due yet: the earliest,
`digest-guard` (2026-11-12), comes due ~2026-11-26, still 2 days out — so this round picked from
yesterday's two open candidates rather than a drift-audit.

Two unchecked candidates were open from 2026-11-23: `lockscreen-guard` (clean grounding/novelty,
no distinctness risk) and `elevate-guard` (moderate confidence, explicitly flagged as needing a
deliberate distinctness argument against `revoke-guard`/`rotation-guard`/`disconnect-guard` before
it ships). Picked `lockscreen-guard` as the readier one, per yesterday's own follow-up note —
`elevate-guard` still needs that hard call made deliberately rather than on autopilot, and this
round's budget was better spent re-verifying and drafting the cleaner candidate than forcing the
harder one. Left `elevate-guard` open below rather than deciding it today.

Re-verified rather than trusting yesterday's research pass at face value. Re-checked the two
riskiest-looking claims independently via WebSearch: **CVE-2026-0012** confirmed real and matching
via Tenable/SentinelOne/VulDB/INCIBE mirrors (Android 14/15/16, `ExpandableNotificationRow.java`'s
`setHideSensitive`, a logic error that can leak contact names on the lock screen, CWE-284 improper
access control, fixed in the March 2026 Android Security Bulletin — correcting one detail from
yesterday's note, which didn't specify the CWE: it's improper access control, not CWE-613); and
**CVE-2026-28965** confirmed real and matching via NVD's own description ("a privacy issue was
addressed with improved checks... fixed in iOS 26.5 and iPadOS 26.5," an unauthenticated local user
can view restricted content that should only be accessible after unlocking the device — exact
match for the claimed mechanic) and Apple's own advisory page at `support.apple.com/127110`.

Ran one more independent novelty check before writing anything, specifically re-probing with
tighter `gh api search/code` phrasings than yesterday's broad ones (yesterday's `"lock screen"
"notification" "sensitive"` query returned 334 unfiltered hits — GitHub code search doesn't AND
multi-phrase queries reliably, so a wide query alone isn't a clean novelty signal). The tighter
`"VISIBILITY_PRIVATE" OR "setPublicVersion" filename:SKILL.md` query (5 hits) confirmed yesterday's
finding: all five are mirrors of the same general `android-notification-builder` reference skill,
redaction shown once as an example snippet, no audit checklist. A separate, broader phrasing
(`"lock screen" "redact" notification filename:SKILL.md`) surfaced something yesterday's pass
missed and worth recording honestly rather than silently matching the prior "zero dedicated hits"
framing: `pruthuraut/BB-skill` ships `ios-notification-audit` and `android-notification-audit`,
two auto-generated pentest checklists (50 rows each, explicitly machine-generated from a template —
"This skill is generated from the \[...\] checklist source... Edit the source and rerun \[...\],
not this file") that do each contain a few generic rows naming lock-screen content exposure
("Test if push notifications contain sensitive data visible on lock screen," "Verify if
notification content does not leak information via preview text"). Fetched and read both
checklists' full tables directly (not just the SKILL.md) before judging: every row across both
50-item lists repeats the identical tool description verbatim regardless of topic (VPN handling,
Focus mode, biometric confirmation, and lock-screen exposure all cite the same boilerplate
"`ios_static.py` ...; lock-screen review on the test device" string) — this is a bulk-generated
mass pentest checklist mill, not a reasoned audit methodology, and none of its rows name or address
this candidate's actual root cause (a *specific* notification type bypassing redaction because it
was built by copying an older, unredacted call site while a different type in the same codebase
stays correctly redacted). Judgment call: this doesn't block shipping — a single generic checklist
bullet among 50 templated, identically-worded rows isn't "already covered" in the sense this pack's
bar cares about — but it's recorded honestly here rather than repeating yesterday's cleaner "zero
hits" framing, since a future round re-checking this candidate's novelty should know these two
exist and why they didn't change the call.

Added `skills/lockscreen-guard/SKILL.md` and `examples/lockscreen-guard.md`; wired into
`README.md`'s skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 55→56 skill-count mentions (prose word and the "copying all
fifty-five/fifty-six" tip). `python tools/validate.py` → `OK: 56 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "lockscreen-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched
it — this skill's own Boundaries section names `push-guard`, `recall-guard`, `pref-guard`, and
`clipboard-guard`; none of theirs needs to name it back.

Follow-up for the next run: `elevate-guard` is the one remaining open candidate below, not yet
drafted — it still needs the hard call on whether a self-expiring JIT/break-glass privilege grant
with an unenforced auto-revocation job is a genuinely distinct artifact from `revoke-guard`,
`rotation-guard`, and `disconnect-guard`, or a fourth slice of the same CWE-613-adjacent family,
flagged moderate-confidence since 2026-11-23. No drift-audit is due yet: `digest-guard`
(2026-11-12) ~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16)
~2026-11-30, `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18)
~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04, `payout-guard` (2026-11-21) ~2026-12-05,
`disconnect-guard` (2026-11-22) ~2026-12-06.

## Research pass (2026-11-23): backlog fully checked off, no shippable item today — 2 new items added

Git hygiene first: clone's `HEAD` was detached at `214875d` (the real tip of `main`, yesterday's
`disconnect-guard` commit) while the local `main` branch ref was stale 5 commits behind at
`bf29e10`. `git fetch origin main` confirmed `origin/main` really is at `214875d` with nothing
unpushed; fixed with `git checkout main && git merge --ff-only origin/main` (fast-forward, no
conflict). `python tools/validate.py` passed (`OK: 55 skills valid and consistent with README.`)
before this round. Confirmed zero unchecked items anywhere in this file (`grep -n '^- \[ \]'
BACKLOG.md` → no matches) and no drift-audit is due yet: the earliest, `digest-guard`
(2026-11-12), comes due ~2026-11-26, 3 days out, longer than this queue's one-day-early
precedent — so per the daily-agent process for a fully checked-off backlog with no drift-audit
due, this round researches and logs new candidates (delegated to a subagent to keep the
WebSearch/`gh api search/code` output out of context) rather than forcing a pick or inventing
busywork.

The subagent checked the roughly 80 already-rejected/saturated topics accumulated across this
file and both archives before brainstorming, to avoid re-spending search budget. Of six candidate
mechanics taken through full grounding/novelty/in-pack-overlap checks, four were rejected
(one — OTP/magic-link single-use enforcement — turned out to be an exact re-hash of an item
already closed in `docs/backlog-archive-2026-q4.md`) and only two cleared the bar. Reporting two
honestly rather than padding to a round number, per this pack's own "quality over count" rule.
Independently re-verified the three riskiest-looking claims myself via WebSearch (not just taken
on the subagent's word) before writing anything, since 2026-dated CVEs are this pack's
known-highest hallucination-risk pattern: **CVE-2026-0012** (Android, `ExpandableNotificationRow
.java`'s `setHideSensitive`, fixed in the March 2026 Android Security Bulletin) — confirmed
real and matching via NVD plus Tenable/SentinelOne/Wiz entries; **CVE-2026-28965** (Apple
iOS/iPadOS, fixed in 26.5) — confirmed real and matching via NVD and Apple's own advisory at
`support.apple.com/127110`; **CVE-2024-1764** (Devolutions Server JIT elevation module, DEVO-2024-0002)
— confirmed real and matching via NVD, published 2024-03-05, CWE-269 improper privilege
management, elevated rights persisting past their own expiration under specific circumstances.

- [x] **New-skill candidate: `lockscreen-guard`? — a notification type a codebase sends doesn't
  participate in the OS's lock-screen sensitive-content redaction mechanism, so it shows full
  content on a locked device regardless of the user's "hide sensitive notifications" setting.**
  An app correctly redacts its *first* notification type (Android's `VISIBILITY_PRIVATE` +
  `setPublicVersion()`, or iOS's notification-content-extension/restricted-content gating) — then
  a second, third, or Nth notification type gets added later by someone who copies an older,
  unredacted send call, or never learned the redaction API exists, and it ships showing full
  message/content on the lock screen to anyone with physical access, independent of the device's
  own privacy setting. Grounded in six independently-dated CVEs spanning 2014–2026 across both
  major platforms — the strongest recurrence signal found this round, confirming this isn't a
  one-off but a mechanic that keeps reappearing because redaction has to be wired per-notification
  -type and nothing forces that: **CVE-2020-0092** and **CVE-2026-0012** (Android, both in
  `ExpandableNotificationRow.java`'s `setHideSensitive`, the latter re-verified above, affects
  Android 14/15/16, fixed March 2026 bulletin); **CVE-2025-22421** (Android, notification content
  descriptions exposed on lock screen bypassing visibility controls); **CVE-2026-28965** (Apple
  iOS/iPadOS, re-verified above, fixed 26.5, 2026-05-11); **CVE-2014-4356** (iOS <8, text-message
  lock-screen preview ignored the configured setting); **CVE-2015-7000** (iOS <9.1 Notification
  Center mishandled "Show on Lock Screen" setting changes, notification could still show after the
  setting was turned off). Novelty check: `gh api search/code` across five phrasings (`"lock
  screen" "notification" "sensitive"`, `"setPublicVersion" OR "VISIBILITY_PRIVATE"`, `"notification"
  "redact" "lock screen"`, `"hide sensitive" "notification"`, `"lockscreen" "preview" "notification"`,
  all `filename:SKILL.md`) found no dedicated audit skill — only build/reference skills showing the
  redaction API as one snippet. Fetched and read in full: `diegosouzapw/awesome-omni-skill` →
  `skills/development/android-notification-builder/SKILL.md` (a general Android-notification-
  building reference skill; redaction appears once under a "Security" best-practices section, its
  own example notifications don't set visibility, no audit checklist) and `Abdo453/HunterAI`'s
  mirror of the OWASP Mobile Application Security Cheat Sheet (does not mention notification
  lock-screen redaction at all — it covers the adjacent-but-distinct case of lock-screen *widgets*
  exposing data, confirming the gap is real enough that even a ~50-item mobile-security checklist
  missed the notification case). In-pack overlap checked by reading the actual text of every
  plausibly-related skill, not just grepping for a shared word: `push-guard`'s own Boundaries
  section explicitly disclaims this exact territory — *"Doesn't cover push payload encryption,
  lock-screen content redaction, or notification-permission-prompt UX — those are client-security
  or UX concerns, not token-lifecycle ones"*; `mention-guard` audits a different question (does the
  *recipient* have authorization to see the *subject* at all — cross-user) from this candidate's
  (does the *authorized* recipient's own *locked device* leak content to someone with physical
  access — same recipient, local-exposure); `pref-guard` is opt-out preferences, not content
  visibility; `clipboard-guard` is clipboard-specific; `recall-guard` mentions "lock-screen preview"
  once only as a given constraint on recall, not an audit of whether the preview should have shown
  full content in the first place.
- [x] **New-skill candidate: `elevate-guard`? — a time-boxed/just-in-time elevated-privilege grant
  (break-glass admin access, a PAM "temporary admin" session, a time-bound PIM role activation) is
  checked for existence at authorization time but never re-checked against its own stated expiry,
  and the scheduled job responsible for auto-revoking it at the deadline isn't confirmed to actually
  run — so a UI countdown showing "0:00 remaining" has no effect on the authorization check behind
  it.** Grounded in **CVE-2024-1764** (Devolutions Server ≤2023.3.14.0, DEVO-2024-0002, re-verified
  above via NVD) — *"a user can continue using the elevated privilege even after the expiration
  under specific circumstances"*, an exact match in a real, named PAM product; corroborated by a
  second, independently-sourced case in a different vendor combination: AWS's own Security Blog
  post on implementing JIT privileged access with Microsoft Entra PIM and AWS IAM Identity Center
  documents, as AWS's own admitted limitation, *"active sessions are not terminated when the Entra
  PIM activation maximum duration has been reached"* — the identical shape in a completely
  different, named integration. Novelty check: `gh api search/code` for the JIT-elevation-expiry
  phrasings found no dedicated audit skill — only generic IAM/PAM how-to-set-up content and vendor
  blog/FAQ commentary (Wiz, Cloud Security Alliance, the `nhimg.org` network) making the same
  observation in prose, never as a code-reviewable checklist skill. **Flagging this one at moderate
  confidence rather than a clean recommend**: `revoke-guard`, `rotation-guard`, and `disconnect-guard`
  are three already-shipped skills in the same general "something is supposed to stop working at a
  deadline/signal but the enforcement point isn't wired" family (all CWE-613-adjacent), and this
  pack has previously declined a fourth skill in an earlier, narrower cluster (the WS/SSE heartbeat
  angle, 2026-11-13) as likely scope-splitting — `disconnect-guard` itself needed a deliberate "hard
  call" before shipping as the *third* skill in that family. This candidate's object (a
  self-expiring privilege *grant*, enforced by a time comparison plus a scheduled revocation job) is
  genuinely different from all three existing skills' objects (a live WebSocket session's cached
  role; an operational credential rotated to a new value across consumers; a user-revoked
  third-party OAuth token/webhook) — but a reviewer's first question will be "why isn't this a
  bullet in `rotation-guard` or `disconnect-guard` instead of a fifth skill in this family," and
  that argument needs to be made explicitly and well in the `SKILL.md`'s Boundaries section, not
  assumed. Whoever picks this up next should weigh that distinctness question deliberately, the
  same way the `disconnect-guard` round did, rather than draft it on autopilot.

Candidates tried and rejected this round, logged so a future round doesn't re-spend search budget:
OTP/magic-link single-use enforcement and revocation races — **already closed**, not a fresh
rejection: `docs/backlog-archive-2026-q4.md` already shows this exact category ("OTP/email-link
single-use and rate-limit correctness") researched and rejected as saturated in a prior round,
naming `himself65/auth-spec`, `tyroneross/build-loop`, and `diegosouzapw/awesome-omni-skills`'
dedicated coverage of single-use/invalidate-on-resend/rate-limit invariants, magic links named
explicitly; usage-based/metered billing double-counted via non-idempotent webhook retries —
REJECTED, insufficient grounding (only unsourced developer-blog postmortems and vendor guidance, no
verified named incident/CVE/advisory, unlike this pack's existing billing skills which rest on a
court case or an FBI PSA); admin-editable/deletable audit log defeating its own immutability
promise — REJECTED, insufficient grounding (the closest CVE, Axis Camera Station Pro CVE-2024-7696,
is a log-*creation*-path tampering bug, not an admin bypassing an already-written log's
immutability; everything else was vendor marketing, not a dated incident); step-up/reauthentication
token reused across different sensitive actions without being scoped to the specific action —
REJECTED, insufficient grounding (one GHSA about a different bypass, one vendor's own documented
deliberate design trade-off, not an exploited bug); bulk export leaking another user's/tenant's
data via insufficiently-scoped joins — REJECTED, already routed elsewhere by this pack's own text
(`export-guard`'s Boundaries section explicitly assigns exactly this question to `security-sweep`);
time-limited share-link expiry enforced only at creation/display time, not the serving endpoint —
pulled back after initial check (real CVEs exist — Filebrowser CVE-2026-35604/CVE-2026-82237,
Vikunja CVE-2026-35594 — but it's the same CWE-613 "revocation state never reaches the validator"
shape already shipped three times in-pack, with weaker distinctness than `elevate-guard` above for
higher scope-splitting risk).

Follow-up for the next run: two real unchecked candidates now exist above — `lockscreen-guard`
(strong, six independent CVEs across both mobile platforms, cleanest novelty signal) and
`elevate-guard` (moderate confidence, needs the same kind of deliberate distinctness argument
against `revoke-guard`/`rotation-guard`/`disconnect-guard` that `disconnect-guard` itself needed
before it ships or gets rejected as a fourth slice of that family). No skill shipped this round —
research-and-log only, per the daily-agent process for a fully checked-off backlog. Next
drift-audit due dates: `digest-guard` (2026-11-12) ~2026-11-26, `email-guard` (2026-11-13)
~2026-11-27, `revoke-guard` (2026-11-16) ~2026-11-30, `subscription-guard` (2026-11-17)
~2026-12-01, `recycle-guard` (2026-11-18) ~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04,
`payout-guard` (2026-11-21) ~2026-12-05, `disconnect-guard` (2026-11-22) ~2026-12-06.

## Shipped `disconnect-guard`, the last open candidate and the hard call it needed (2026-11-22)

Git hygiene first: clone's `HEAD` was detached at `c7cafe5` (the real tip of `main`, yesterday's
`payout-guard` commit) while the local `main` branch ref was stale 4 commits behind at `bf29e10`.
`git fetch origin main` confirmed `origin/main` really is at `c7cafe5` with nothing unpushed;
fixed with `git fetch origin main && git branch -f main origin/main && git checkout main`
(fast-forward, no conflict). `python tools/validate.py` passed (`OK: 54 skills valid and
consistent with README.`) before this round.

`disconnect-guard` was the only unchecked backlog item (confirmed via `grep -n '^- \[ \]'
BACKLOG.md`) — the one left open since 2026-11-19, flagged lower-confidence specifically because
it needed a hard call on whether "user-initiated third-party integration disconnect not actually
revoking tokens/webhooks" is a genuinely distinct artifact from this pack's own `revoke-guard` and
`rotation-guard`, or a third slice of the same CWE-613 mechanic under a new name. No drift-audit
was due yet (earliest is `digest-guard`, ~2026-11-26, 4 days out), so this round could spend its
full budget on that one open candidate rather than splitting it against a drift-audit.

Delegated independent re-verification and the distinctness call itself to a subagent (kept the
WebSearch/`gh api search/code` output out of context), with explicit instructions to read
`revoke-guard` and `rotation-guard` in full before judging overlap, not just grep for shared
vocabulary. Both grounding CVEs held up exactly as the 2026-11-19 candidate stated: Rocket.Chat's
CVE-2026-49277 (GHSA-39hg-492f-3c4f, CWE-613) — deactivating a user never revoked their already-
issued OAuth access/refresh tokens, so the deactivated account could keep using the live access
token and mint fresh ones from the refresh token until the tokens' own unrelated expiry, fixed in
8.5.0/8.4.2/8.3.4/8.2.4/8.1.5/8.0.6/7.13.8/7.10.12; and OpenClaw's CVE-2026-53830
(GHSA-275c-xpvc-jgfw) — a `secrets.reload` operation wrote a new Slack/Zalo webhook secret to the
store, but the webhook-signature-verification path kept accepting requests signed with the old
one. The non-CVE Zoom/Dropbox/Twitch forum reports from the original candidate were explicitly
*not* re-verified and are treated as uncorroborated color, not load-bearing grounding — the two
CVEs alone carry the candidate. Fresh novelty check (five `gh api search/code` phrasings,
`filename:SKILL.md`) found only integration-*setup* skills (OAuth connect flows for Zoom/Google/
monday), one unrelated multi-tenancy build skill, and a personal end-user security-hygiene
how-to (`JiayiV/question_mixing`, a checklist for a *person* to click "Revoke" in their own
account settings) — pulled and read the two closest hits directly, neither audits whether a
backend's disconnect action actually propagates to token-validation or webhook-delivery code.
Archive grep (`docs/backlog-archive-2026-q3.md`, `docs/backlog-archive-2026-q4.md`) found no prior
round had considered this exact mechanic.

Resolved the distinctness question the backlog flagged as the main risk, by reading both
existing skills' own text rather than assuming from the shared CWE: `revoke-guard`'s own
Boundaries section explicitly disclaims this exact territory ("doesn't cover HTTP/REST session or
token revocation... this skill exists for the case where [the realtime layer] doesn't" re-validate
via the same store) — it *assumes* the token-revocation path already works and only audits
whether a live WebSocket connection re-checks it continuously. `disconnect-guard` audits precisely
the thing `revoke-guard` takes for granted: whether disconnect's write reaches the validator,
refresh exchange, or webhook verifier at all. `rotation-guard` is a different artifact entirely —
rotating *your own* operational credential to a *new* value across consumers, with a propagation/
overlap-window design question that doesn't exist here: `disconnect-guard`'s action is a
*permanent* revocation with no new value and no overlap window to size, only a kill switch to
confirm is wired to anything. Wrote the SKILL.md's Boundaries section to state both distinctions
explicitly rather than leave them implicit, since that's exactly the objection a reviewer would
raise first.

Added `skills/disconnect-guard/SKILL.md` and `examples/disconnect-guard.md`; wired into
`README.md`'s skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 54→55 skill-count mentions (prose word and the "copying all
fifty-four/fifty-five" tip). `python tools/validate.py` → `OK: 55 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "disconnect-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched
it — this skill's own Boundaries section names `revoke-guard` and `rotation-guard`; neither of
theirs needs to name it back.

Follow-up for the next run: the backlog is now fully checked off again (this was the last open
candidate) — per process, next round should do a fresh novelty/research pass rather than invent
busywork, unless a drift-audit comes due first. Next drift-audit due dates: `digest-guard`
(2026-11-12) ~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16)
~2026-11-30, `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18)
~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04, `payout-guard` (2026-11-21) ~2026-12-05.

## Shipped `payout-guard`, the readier of the two open candidates (2026-11-21)

Git hygiene first: clone's `HEAD` was detached at `939476d` (the real tip of `main`, yesterday's
`mention-guard` commit) while the local `main` branch ref was stale 3 commits behind at `bf29e10`.
`git fetch origin main` confirmed `origin/main` really is at `939476d` with nothing unpushed;
fixed with `git checkout main && git merge --ff-only origin/main` (fast-forward, no conflict).
`python tools/validate.py` passed (`OK: 53 skills valid and consistent with README.`) before this
round. No drift-audit is due yet (earliest is `digest-guard`, ~2026-11-26, 5 days out), so this
round picked from the two open backlog candidates rather than re-checking a shipped skill.

Two unchecked candidates were open from 2026-11-19/20: `payout-guard` and `disconnect-guard`.
Picked `payout-guard` as the readier one, per the standing assessment in this file: it has two
independent, well-grounded sources (an FBI IC3 PSA with hard numbers, and a named, multiply-
corroborated 2025 Microsoft campaign) versus `disconnect-guard`'s self-flagged lower confidence
and open question of whether it's a genuinely distinct artifact from `revoke-guard`/`rotation-guard`
or a third slice of the same CWE-613 mechanic — that call is still better made with a fresh look
than carried over by assumption, so left it open rather than forcing it today.

Delegated independent re-verification to a subagent (kept the WebSearch/`gh api search/code`
output out of context) rather than trust the 2026-11-19 research pass's own numbers at face value,
per this pack's standing practice. Both grounding sources held up exactly as claimed: FBI IC3 PSA
I-091019-PSA's 1,053 complaints / $8,323,354 losses / 815% direct-deposit-request increase (Jan
2018–June 2019) confirmed accurate against ic3.gov; Microsoft's "Storm-2657"/"Payroll Pirate"
campaign (Oct 2025) confirmed real and matching — AiTM-phished/no-MFA SSO credentials into Workday,
attacker enrolls their own MFA device, changes payment-election details, hides Workday's own
notification email behind an inbox rule set up in the same compromised session — corroborated by
The Register, The Hacker News, BleepingComputer, TechRadar, ITPro, CPO Magazine, and SC World.
Novelty re-check (five `gh api search/code` phrasings, `filename:SKILL.md`) found no dedicated
audit skill for this mechanic anywhere, only payroll-prep/tax-compliance build skills and unrelated
generic offensive-hunt skills. In-pack overlap re-check (read `email-guard`, `rotation-guard`,
`push-guard` in full; pack-wide grep for payout/direct-deposit/bank-account/payroll) found only one
incidental, unrelated hit (`clipboard-guard` lists "bank account number" as an example sensitive
clipboard value) — no skill already audits this flow.

Confirmed the distinct-artifact question the backlog flagged as the main risk: `email-guard`
shares the step-up/notify-old-channel/hold *shape*, but its safety net assumes the old-address
mailbox is a priori independent of whatever hijacked the session (a stolen cookie or XSS pop isn't
also a mailbox compromise). `payout-guard`'s realistic attacker path — a phished SSO session — often
*is* already standing inside the mailbox a naive port of that same notification would use, which is
exactly the Storm-2657 campaign's own move (hiding Workday's notice via an inbox rule under the
same compromised identity). Wrote the SKILL.md's Step 2 and Boundaries section to make that
distinction explicit rather than silently reusing `email-guard`'s framing, since that's the part a
reviewer would most likely push back on.

Added `skills/payout-guard/SKILL.md` and `examples/payout-guard.md`; wired into `README.md`'s
skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 53→54 skill-count mentions (prose word and the "copying all
fifty-three/fifty-four" tip). `python tools/validate.py` → `OK: 54 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "payout-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it —
this skill's own Boundaries section names `email-guard` and `rotation-guard`; neither of theirs
needs to name it back.

Follow-up for the next run: `disconnect-guard` is still the one open candidate below, not yet
drafted — it still needs the hard call on whether "user-initiated third-party integration
disconnect not actually revoking tokens/webhooks" is a genuinely distinct artifact from
`revoke-guard`/`rotation-guard` or a third slice of the same CWE-613 mechanic, flagged
lower-confidence since 2026-11-19 and not yet resolved by any round since. No drift-audit is due
yet: `digest-guard` (2026-11-12) ~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard`
(2026-11-16) ~2026-11-30, `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard`
(2026-11-18) ~2026-12-02, `mention-guard` (2026-11-20) ~2026-12-04.

## Shipped `mention-guard`, the readiest of yesterday's three candidates (2026-11-20)

Git hygiene first: clone's `HEAD` was detached at `b31c964` (the real tip of `main`, yesterday's
novelty-pass commit) while the local `main` branch ref was stale 2 commits behind at `bf29e10`.
`git fetch origin main` confirmed `origin/main` really is at `b31c964` with nothing unpushed;
fixed with `git checkout main && git merge --ff-only b31c964` (fast-forward, no conflict).
`python tools/validate.py` passed (`OK: 52 skills valid and consistent with README.`) before this
round.

Three unchecked candidates were open from 2026-11-19: `payout-guard`, `mention-guard`, and
`disconnect-guard`. Yesterday's own follow-up note flagged `mention-guard` as readiest — cleanest
novelty signal, four independent CVEs, least in-pack-overlap ambiguity — so re-verified that one
specifically rather than re-opening all three from scratch. Delegated the re-verification to a
subagent (kept the WebSearch/`gh api search/code` output out of context) with explicit instructions
to treat the 2026-dated `CVE-2026-1629` as the highest-risk-of-hallucination claim and check it
hardest, per this pack's standing practice after `subscription-guard`'s round flagged the same
pattern.

All four CVEs held up as REAL-AND-MATCHES against NVD/GHSA/vendor-advisory primary sources, not
just loose shape-matches: Confluence CVE-2017-9505 (CONFSERVER-52560, fixed 6.2.1), Flarum
CVE-2023-22488 (GHSA-8gcg-vwmw-rxj4, fixed core 1.6.3), Mattermost CVE-2023-2792 (MMSA-2023-00161,
ephemeral-message content leaking through permalink previews), and Mattermost CVE-2026-1629
(MMSA-2026-00580, confirmed via NVD + Red Hat Bugzilla #2448239, published 2026-03-16, fixed
10.11.11/11.4.0 — genuinely real despite the 2026 date, not a repeat of a prior round's hallucination
scare). Fresh novelty check (five `gh api search/code` queries, top-20 results pulled per query since
GitHub code search doesn't reliably AND multi-phrase queries) found no dedicated audit skill for the
mechanic — only unrelated Discord-bot/Slack-integration/compliance/generic-agent-tooling
`SKILL.md` hits.

Picked `mention-guard` over the other two per yesterday's own assessment: `payout-guard` still needs
its SKILL.md to work harder to distinguish from `email-guard`'s shape, and `disconnect-guard` is
flagged lower-confidence pending a harder look at whether it's scope-splitting
`revoke-guard`/`rotation-guard`. Left both open below rather than deciding them today.

Added `skills/mention-guard/SKILL.md` and `examples/mention-guard.md`; wired into `README.md`'s
skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 52→53 skill-count mentions (prose word and the "copying all
fifty-two/fifty-three" tip). `python tools/validate.py` → `OK: 53 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "mention-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it —
this skill's own Boundaries section names `revoke-guard`, `digest-guard`, `pref-guard`, and
`subscription-guard`; none of theirs needs to name it back.

Follow-up for the next run: `payout-guard` and `disconnect-guard` are still open candidates below,
neither drafted yet. `disconnect-guard` in particular needs a hard call on whether it's a genuinely
distinct artifact from `revoke-guard`/`rotation-guard` or just a third slice of the same CWE-613
mechanic before it ships or gets rejected. No drift-audit is due yet: `digest-guard` (2026-11-12)
~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16) ~2026-11-30,
`subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18) ~2026-12-02.

## Research pass (2026-11-19): backlog fully checked off, no shippable item today — 3 new items added

Git hygiene first: clone's `HEAD` was already on branch `main`, detached at `99d9d7e` (the
`recycle-guard` commit) but one commit behind `origin/main`. `git fetch origin` confirmed
`origin/main` was identical at `99d9d7e` with nothing unpushed; fixed with `git checkout main &&
git pull --ff-only` (clean fast-forward, no conflict). `python tools/validate.py` passed (`OK: 52
skills valid and consistent with README.`) before this round. Confirmed zero unchecked items
anywhere in this file (`grep -n '^- \[ \]' BACKLOG.md` → no matches) and the earliest drift-audit
(`digest-guard`, due ~2026-11-26) is still a week out — so per the daily-agent process for a fully
checked-off backlog, this round researches and logs new candidates (delegated to a subagent to
keep the search/WebSearch output out of context) rather than forcing a pick or inventing busywork.

Candidates tried and rejected this round (reasons logged so a future round doesn't re-spend search
budget): SAML/OIDC single-logout not propagating to relying parties and SCIM deprovisioning not
revoking live sessions/tokens — both saturated, `UnboundCompute/security-agent-skills` →
`auditing-sso-logout-and-session-revocation/SKILL.md` and `auditing-scim-provisioning-trust/
SKILL.md` cover each verbatim (read in full, not just grepped); GraphQL query batching/aliasing
bypassing rate limits — saturated, a dedicated `graphql-batching-attacks` skill is duplicated
across several offensive-security repos; coupon/promo-code redemption race conditions —
saturated, one of the most heavily templated topics in the "race-condition hunting" offensive-skill
space; "remember me" cookie surviving a password reset — real (CVE-2021-41268 Symfony) but
saturated by multiple dedicated skills; PDF/document redaction leaving selectable underlying text —
saturated by a dedicated `redaction-reviewer` skill mirrored across several legal-AI repos; OAuth
mobile custom-URL-scheme/redirect-URI hijacking — saturated by many dedicated offensive OAuth-hunt
skills; Supabase/Postgres RLS bypass via a service-role key in background jobs — extremely
saturated (a dozen+ dedicated `rls-*`/`supabase-security-*` skills); GDPR erasure undone by a
backup/DR restore reintroducing deleted users — in-pack overlap, `erasure-guard`'s own Step 3
already names this exactly; instant payout against a pending/disputable balance followed by a
chargeback creating an unrecoverable negative balance, and Stripe Connect destination-charge
refunds not reversing the platform application fee — both real-sounding but rejected for
insufficient grounding (no verified named incident or CVE/advisory matching the specific mechanic,
only routine vendor risk/API docs); location-sharing not stopping after expiry/block/unfriend —
insufficiently grounded (only conflicting user-forum anecdotes about Apple Find My, no CVE or
vendor-confirmed bug).

Three candidates cleared the bar — real, dated, independently re-verified (not just taken on the
research subagent's word: re-ran WebSearch myself against the two riskiest-looking 2026-dated CVE
numbers plus the named 2025 incident below before writing anything) and confirmed not already
covered in-pack or by a prominent external skill:

- [x] **New-skill candidate: `payout-guard`? — payout/direct-deposit destination change treated as
  an ordinary profile edit instead of a sensitive financial action.** A payroll, vendor-payment, or
  marketplace-payout system's "update my bank account" flow is gated only by an active session —
  no step-up re-auth on *this specific action*, no hold/cooling-off period before the new
  destination starts receiving money, and no out-of-band notification to the employee/vendor when
  it changes. An attacker who compromises a session (phished credentials + MFA bypass via
  adversary-in-the-middle, not a stolen password) redirects future payouts to an account they
  control. Grounded in: **FBI IC3 PSA I-091019-PSA** ("Business Email Compromise: The $26 Billion
  Scam," Sept 2019) — 1,053 complaints of this exact payroll-diversion pattern Jan 2018–June 2019,
  ~$8.3M in losses, direct-deposit change requests up over 800% in that window; and Microsoft's
  Oct 2025 "Storm-2657"/"Payroll Pirate" writeup (re-verified independently via WebSearch today,
  not just the subagent's summary — confirmed real and matching: AiTM-phished SSO credentials used
  to log into Workday and change payment-election details, concealed with inbox rules hiding
  Workday's own notification emails; corroborated independently by The Register, BleepingComputer,
  The Hacker News, ITPro). Novelty check: `gh api search/code` (`"payroll diversion"`, `"direct
  deposit" "change" "bank account" "verify"`, `"banking details" "change" "hold period"` — zero
  hits on the last one — all `filename:SKILL.md`) found only state-specific payroll-compliance
  build skills and generic phishing-simulation skills, never a dedicated audit of this flow's
  hijack-resistance. In-pack overlap checked against `email-guard` (shares the "settings-change →
  takeover vector → step-up/notify-old-channel/hold" shape, but a different artifact — payout
  destination vs. login email — and a different attacker path — AiTM-phished SSO vs.
  stolen-session/XSS); also checked `recycle-guard`, `rotation-guard`, `push-guard`, `seat-guard` —
  none touch a payout/bank-detail-change flow. Flag for whoever writes this up: lean hard on the
  distinct artifact and distinct grounding in the SKILL.md, since the shape-overlap with
  `email-guard` is real enough that a reviewer could ask why this isn't just a bullet there.
- [x] **New-skill candidate: `mention-guard`? — a notification/mention/permalink-preview pipeline
  runs through its own code path and leaks a restricted resource's existence or content to a user
  who can't access it directly.** A notification-sender (e.g. @-mention alerts, "someone commented"
  emails) never checks whether the *recipient* can see the *subject* before notifying them, or a
  cached link/permalink preview isn't invalidated when the viewer's permission to the underlying
  resource is later revoked. Grounded in four independent CVEs across three unrelated products:
  **CVE-2017-9505** (Confluence) — watch/comment notifications didn't check recipient permission on
  the page; **CVE-2023-22488** (Flarum) — notification-sending doesn't check the subject is visible
  to the receiver before sending; **CVE-2026-1629** (Mattermost, MMSA-2026-00580, CVSS 4.3,
  published 2026-03-16, fixed in 10.11.11 — re-verified independently via WebSearch today: real,
  matches claim exactly) — cached permalink previews keep exposing private-channel content after
  the viewer loses channel access, until the cache expires or is reset; **CVE-2023-2792**
  (Mattermost, earlier/related) — ephemeral messages' content leaked back through permalink
  previews. Novelty check: `gh api search/code` (`"mention" "notification" "permission" "leak"`,
  `"@mention" "restricted" "content" "notification"`, `"permalink preview" "permission" "cache"`,
  two more variations, all `filename:SKILL.md`) found zero dedicated hits — only unrelated
  multi-agent/LLM-tooling skills and broad OSINT catch-alls. In-pack overlap checked against
  `revoke-guard` (live WS collaboration session authorization — continuous connections, a different
  transport than a one-shot notification/preview send), `digest-guard` (recurring scheduled-report
  stale permissions, not an ad-hoc mention/preview), `pref-guard` (notification *opt-out*
  preferences, not content authorization), `subscription-guard` (GraphQL subscription transport
  split); none audit whether the notification/mention/preview pipeline itself re-checks or caches
  around the resource's access control. Best-grounded and cleanest-novelty of the three candidates
  this round.
- [x] **New-skill candidate: `disconnect-guard`? — a user-facing "disconnect this integration /
  revoke this app's access" action doesn't actually invalidate the OAuth tokens already issued, or
  doesn't stop an already-registered webhook from continuing to deliver.** Revocation is a UI/DB
  flag that was never wired into the token-validation or event-delivery code path, so a
  disconnected integration keeps working until its token happens to expire on its own. Grounded in:
  **CVE-2026-49277** (Rocket.Chat, CWE-613, GHSA-39hg-492f-3c4f, published 2026-06-24 — re-verified
  independently via WebSearch today: real, matches claim — deactivating a user doesn't revoke
  their OAuth access/refresh tokens; a deactivated user can keep using the access token and mint
  new ones from the refresh token; fixed in 8.5.0/8.4.2/8.3.4/8.2.4/8.1.5/8.0.6/7.13.8/7.10.12); and
  **CVE-2026-53830** (OpenClaw, GHSA-275c-xpvc-jgfw, fixed 2026.4.22) — old Slack/Zalo webhook
  secrets stay accepted after a secrets-reload/rotation operation; corroborated by non-CVE
  developer-forum reports of the identical gap at Zoom, Dropbox, and Twitch. Novelty check: `gh api
  search/code` across several OAuth-revoke/webhook-persistence phrasings found no dedicated audit
  skill for this exact combination. **Flagged lower-confidence than the other two**: both grounding
  CVEs share the same CWE-613 root cause already cited for this pack's own `revoke-guard`, and the
  "does revocation/rotation actually propagate everywhere" shape is already covered from two other
  angles in-pack (`rotation-guard` for ops credentials, `revoke-guard` for live WS sessions) — this
  pack has previously declined a 4th skill in an adjacent cluster (the WS/SSE heartbeat angle,
  2026-11-13) as likely scope-splitting. Novel and real externally, but whoever picks this up next
  should weigh hard whether "user-initiated third-party integration disconnect" is a genuinely
  distinct artifact or just a third slice of the same mechanic under a new name before drafting a
  `SKILL.md`.

Follow-up for the next run: `mention-guard` shipped 2026-11-20 (see that day's section above) —
`payout-guard` and `disconnect-guard` are still open below, neither drafted yet. No skill shipped
*this* round — this was a research-and-log pass, not an implementation one, per the daily-agent
process for a fully checked-off backlog. No drift-audit is due yet: `digest-guard` (2026-11-12)
~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16) ~2026-11-30,
`subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18) ~2026-12-02.

## Shipped `recycle-guard`, the last open candidate from 2026-11-15 (2026-11-18)

Git hygiene first: `git status`/`git log --oneline -10` showed `main` already at `bf29e10`
(yesterday's `subscription-guard` commit) with a clean working tree and nothing to fast-forward —
no detached-HEAD or stale-branch issue this round. `python tools/validate.py` passed (`OK: 51
skills valid and consistent with README.`) before this round.

`recycle-guard` was the only unchecked backlog item (confirmed via `grep -n '^- \[ \]'
BACKLOG.md`), carried over from the 2026-11-15 research pass and already independently
re-verified once (2026-11-17's `subscription-guard` round, which chose the other candidate but
left this one's grounding and novelty check unchallenged). Ran one more independent novelty check
before writing anything rather than trusting the two-and-three-day-old passes alone: `gh api
search/code` for `"recycled phone number"`, `"phone number recycling"`, and `"SMS 2FA"
"reassigned"` (all `filename:SKILL.md`) turned up only an `identity-graph-operator` skill (a
generic marketing/ad identity-resolution tool, not a security audit) and a generic
`offensive-business-logic` red-team checklist repeated across many mirrors — neither is a dedicated
audit of this mechanic. Read `skills/dormancy-guard/SKILL.md`, `skills/email-guard/SKILL.md`, and
`skills/push-guard/SKILL.md` in full: `email-guard` explicitly carves out carrier-side SIM swapping
as out of its scope ("doesn't extend to telecom-side SIM swapping or carrier account takeover...
the phone network the OTP rides over"), which is adjacent to but distinct from `recycle-guard`'s
mechanic (a carrier *legitimately* reassigning a dormant number to a new subscriber, no fraud
involved on the carrier's side) — confirming the boundary rather than finding overlap. Pack-wide
`grep -li 'phone\|SMS\|recycl' skills/*/SKILL.md` turned up nothing else on point.

Also caught and fixed, while writing up the candidate, the stat-attribution imprecision the
2026-11-17 re-verification round had already flagged but not yet corrected in this file: the
original candidate text tied Lee & Narayanan's 83% figure to six specific services
(Amazon/AOL/Facebook/Google/PayPal/Yahoo), which conflates two different sub-stats in the paper.
Corrected in place above to "83% vulnerable to account hijack or PII exposure" (the general stat)
plus the separate "100 of 259 tied to breach-dump credentials" stat, matching how Krebs and The
Hacker News report it independently rather than the original's merged framing. The `SKILL.md` and
example below use the corrected framing throughout.

Added `skills/recycle-guard/SKILL.md` and `examples/recycle-guard.md`; wired into `README.md`'s
skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 51→52 skill-count mentions (prose word and the "copying all
fifty-one/fifty-two" tip). `python tools/validate.py` → `OK: 52 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "recycle-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it —
this skill's own Boundaries section names `dormancy-guard`, `email-guard`, and `push-guard`; none
of theirs needs to name it back.

Follow-up for the next run: the backlog is now fully checked off again (last unchecked item was
this one) — per process, next round should do a fresh novelty/research pass rather than invent
busywork, unless a drift-audit comes due first. Next drift-audit due dates: `digest-guard`
(2026-11-12) ~2026-11-26, `email-guard` (2026-11-13) ~2026-11-27, `revoke-guard` (2026-11-16)
~2026-11-30, `subscription-guard` (2026-11-17) ~2026-12-01, `recycle-guard` (2026-11-18)
~2026-12-02 — none due yet.

## Shipped `subscription-guard` from the two open candidates (2026-11-17)

Git hygiene first: clone's `HEAD` was detached at `32d8bc3` (the real tip of `main`, yesterday's
`revoke-guard` commit) while the local `main` branch ref was stale 4 commits behind. `git fetch
origin main` confirmed `origin/main` really is at `32d8bc3` with nothing unpushed; fixed with
`git checkout main && git merge --ff-only origin/main` (fast-forward, no conflict).
`python tools/validate.py` passed (`OK: 50 skills valid and consistent with README.`) before this
round.

Two unchecked candidates were open from 2026-11-15: `recycle-guard` (recycled phone number still
trusted for SMS 2FA/recovery) and `subscription-guard` (GraphQL subscriptions bypassing the
authorization layer HTTP queries/mutations go through). Delegated an independent re-verification
of both to a subagent (kept the search/WebSearch output out of context) rather than trust the
2026-11-15 research pass's own summary — specifically flagged `subscription-guard`'s three CVE
numbers for extra scrutiny, since "2026-dated CVEs for GraphQL libraries" looked like a plausible
hallucination shape to check hard before committing to either candidate.

Both held up under re-verification. `recycle-guard`'s grounding (Lee & Narayanan, IEEE eCrime
2021, recyclednumbers.cs.princeton.edu) checked out as solid, with one minor imprecision worth
fixing before it ships: the "83% tied to an existing Amazon/AOL/Facebook/Google/PayPal/Yahoo
account" framing conflates two different sub-stats in the paper (83% = vulnerable to
hijack-or-PII-indexing generally; tying to those six specific services is a separate, smaller
number that Krebs and The Hacker News even report differently from each other, at 171 vs. a
different figure) — not fabricated, just needs tighter attribution when written up.
`subscription-guard`'s three CVEs (Strawberry GraphQL CVE-2026-35523/GHSA-vpwc-v33q-mq89, Parse
Server CVE-2026-32594/GHSA-p2x3-8689-cwpg, Neo4j GraphQL library CVE-2026-5423/GHSA-fcpg-3fw5-vc65)
all verified real via NVD/GHSA/vendor advisories and matched the claimed mechanic closely (one
precision note: Neo4j's actual defect is an unverified JWT signature on `connectionParams`, not
literally "forwarded into resolver context" — same bypass class, worded slightly loosely in the
original candidate). Novelty and in-pack-overlap re-checks (`gh api search/code`, grep across
`skills/*/SKILL.md` and both archive files) independently confirmed both candidates' 2026-11-15
findings: no dedicated audit skill for either mechanic anywhere searched, and no in-pack overlap
(GraphQL mentioned only incidentally by `overwrite-guard`/`pagination-guard`/`reaccept-guard`/
`sunset-guard`/`throttle-guard`/`trail-guard`; phone/SMS/2FA mentioned only incidentally by
`blast-guard`/`clipboard-guard`/`export-guard`/`pref-guard`/`residency-guard`).

Picked `subscription-guard` over `recycle-guard`: three independent CVEs across three unrelated
frameworks/ecosystems (Python/Strawberry, Node/Parse Server, Neo4j's GraphQL library) is a
stronger recurring-pattern signal than `recycle-guard`'s single (if excellent) 2021 academic paper,
and the mechanic maps more directly onto a code-reviewable "does the WS/subscription auth path
wire into the same check as the HTTP path" audit — closer to this pack's existing code-review
shape than `recycle-guard`'s more product-policy-shaped "re-verify phone ownership periodically"
angle. Kept `recycle-guard` as the next open candidate below rather than dropping it; its stat
attribution needs a light fix when it's written up but the grounding itself is sound.

Added `skills/subscription-guard/SKILL.md` and `examples/subscription-guard.md`; wired into
`README.md`'s skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`. Bumped the 50→51 skill-count mentions (prose word and the "copying all
fifty/fifty-one" tip). `python tools/validate.py` → `OK: 51 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "subscription-guard" skills/*/SKILL.md` outside its own file returns nothing) and
matched it — this skill's own Boundaries section names `overwrite-guard`, `pagination-guard`,
`reaccept-guard`, `sunset-guard`, `throttle-guard`, `trail-guard`, and `revoke-guard`; none of
theirs needs to name it back.

Follow-up for the next run: `recycle-guard` is the one remaining open candidate below — real,
grounded, not yet drafted as a `SKILL.md`. When it's written up, state its headline stat as "83%
of sampled recycled numbers were vulnerable to account hijack or PII exposure" rather than tying
that figure to the six named services specifically (that's the imprecision this round's
re-verification caught). No drift-audit is currently due: `email-guard` (2026-11-13) comes due
~2026-11-27, `digest-guard` (2026-11-12) ~2026-11-26, `revoke-guard` (2026-11-16) ~2026-11-30 —
all more than a week out.

## Shipped `revoke-guard` from yesterday's research-pass candidates (2026-11-16)

Git hygiene first: clone's `HEAD` was detached at `836ad0d` (the real tip of `main`, yesterday's
novelty-pass commit) while the local `main` branch ref was stale 4 commits behind at `cb51363`.
`git fetch origin main` confirmed `origin/main` really is at `836ad0d` with nothing unpushed;
fixed with `git checkout main && git merge --ff-only origin/main` (fast-forward, no conflict).
`python tools/validate.py` passed (`OK: 49 skills valid and consistent with README.`) before this
round.

Picked `revoke-guard` (real-time collaboration permission revocation doesn't close the live
WebSocket/Socket.IO session) from the three unchecked candidates logged yesterday — it had the
strongest independent grounding of the three (three separate, dated 2026 CVEs sharing the same
CWE-613 root cause across three different products/frameworks, not just one source) and fit
cleanly into the pack's existing realtime-collaboration cluster (`resync-guard`,
`backpressure-guard`, `storm-guard`, `overwrite-guard`) without overlapping any of them — each of
those audits a different axis (missed-message replay, slow-consumer fan-out, mass-reconnect
survival, concurrent-edit version checks), none audits whether a connection's *authorization*
itself stays current while it's open.

Re-ran the novelty check independently before writing anything (not just trusting yesterday's
research subagent): `gh api search/code` for `"websocket" "permission" "revoked" "disconnect"
filename:SKILL.md`, `"revoke" "websocket" "still connected" filename:SKILL.md`, and `"stale
session" "collaboration" "access revoked" filename:SKILL.md` — all three came back with only
generic/unrelated hits (broad realtime-systems or websocket-setup skills, one offensive
CSWSH/replay skill already checked and ruled out yesterday); no dedicated audit skill for this
specific "authorization checked once at connect, never again" mechanic. Left `recycle-guard`
(recycled phone number / SMS 2FA) and `subscription-guard` (GraphQL subscriptions bypass HTTP-path
auth) unchecked below for a future round — both still look real and ungrounded-elsewhere, just
didn't have as many independent sources backing them as `revoke-guard`'s three CVEs.

Added `skills/revoke-guard/SKILL.md` and `examples/revoke-guard.md`; wired into `README.md`'s
skills table, decision table, Examples list, and intro "survived" sentence, and
`examples/README.md`; bumped the 49→50 skill-count mentions (prose word and the "copying all
forty-nine/fifty" tip). `python tools/validate.py` → `OK: 50 skills valid and consistent with
README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "revoke-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it —
this skill's own Boundaries section names `storm-guard`, `backpressure-guard`, `resync-guard`, and
`overwrite-guard`; none of theirs needs to name it back.

Follow-up for the next run: `recycle-guard` and `subscription-guard` are still open candidates
below, neither has a `SKILL.md` drafted yet — pick whichever one's research holds up best under a
second look. `recall-guard`'s drift-audit fact-check already ran (2026-11-15, logged in the
section below) and found nothing wrong, so no drift-audit is currently due.

## Research pass (2026-11-15): backlog fully checked off, no shippable item today — 3 new items added

Git hygiene first: clone started with `HEAD` detached at `4255f1a` (the real tip of `main`, the
`recall-guard` drift-audit commit) while the local `main` branch ref was stale 2 commits behind at
`cb51363`. `git fetch origin main` confirmed `origin/main` really is at `4255f1a` with nothing
unpushed; fixed with `git checkout main && git merge --ff-only origin/main` (fast-forward, no
conflict). `python tools/validate.py` passed (`OK: 49 skills valid and consistent with README.`)
before this round. Confirmed zero unchecked items anywhere in this file (`grep -n '^- \[ \]'
BACKLOG.md` → no matches), and the next drift-audit (per yesterday's note) doesn't come due until a
future skill ages two weeks — so per the daily-agent process for a fully-checked-off backlog, this
round researches and logs new candidates (delegated to a subagent to keep the search output out of
context) rather than forcing a pick or inventing busywork.

Three candidates cleared the bar this round — real, dated, independently-grounded, and confirmed
not already covered in-pack or by a prominent external skill (`gh api search/code` plus WebSearch
for each, re-verified rather than taken on the subagent's word alone):

- [x] **New-skill candidate: `recycle-guard`? — recycled phone number still trusted for SMS 2FA /
  account recovery.** An app binds SMS-based 2FA or account-recovery to a phone number at signup
  and never re-verifies ownership later. Carriers recycle dormant numbers to new subscribers, who
  can then receive the previous owner's OTP/recovery codes and take over the account — especially
  potent when the previous owner's password is already in a breach dump, since the attacker only
  needs the number back. Grounded in Lee & Narayanan (Princeton), *"Security and Privacy Risks of
  Number Recycling at Mobile Carriers,"* IEEE eCrime 2021: 259 sampled recycled numbers from
  T-Mobile/Verizon, 83% vulnerable to account hijack or PII exposure through at least one online
  service still bound to the number, 100 of the 259 independently tied to credentials already
  circulating in breach dumps, and carrier reverse-lookup UIs with no query limits making targeting
  trivial (primary source `recyclednumbers.cs.princeton.edu`; corroborated by The Hacker News's 2021
  coverage). Novelty check: `gh api search/code` (`"recycled phone number"`, `"phone number
  recycling"`, `"SMS 2FA" "reassigned"` filename:SKILL.md) found zero on-point hits — only unrelated
  identity-graph-operator and offensive-business-logic skills. No in-pack overlap: `dormancy-guard`,
  `email-guard`, and `push-guard` each audit a different artifact (inactivity sweeps, email-change
  flows, device tokens), none touch phone-number ownership drift.
- [x] **New-skill candidate: `revoke-guard`? — real-time collaboration permission revocation doesn't
  close the live WebSocket session.** An app correctly revokes a user's document/resource access at
  the HTTP/REST layer, but an already-open WebSocket/Socket.IO collaboration session (or a role
  cached inside that session's connection pool) keeps delivering live edits/data, because the
  realtime layer only checks authorization at connect time rather than continuously or on
  revocation. Grounded in three independent, dated CVEs sharing the same CWE-613 root cause: a Docs
  product's CVE-2026-92800 (<5.4.1, CVSS 7.6 — revoking a parent doc didn't close existing WS
  connections to its sub-documents; VulnCheck advisory); Open WebUI's GHSA-45m8-cpm2-3v65 /
  CVE-2026-44553 (Yjs collaborative-doc handlers checked a cached role in the Socket.IO session pool
  instead of the DB, so a de-adminned user kept admin rights over the live socket as long as
  heartbeats kept it alive); and Outline's CVE-2025-68663 (<1.1.0 — suspended users could keep or
  establish WS connections and kept receiving updates). Novelty check: `gh api search/code`
  (`"websocket" "permission" "revoked" "disconnect"`, `"revoke" "websocket" "still connected"`,
  `"stale session" "collaboration" "access revoked"`) found no dedicated audit skill — the closest
  hit (`Ambiguous-Interactive/signal-fish-server` → `websocket-session-security`) was fetched and
  read in full and covers CSWSH/replay/full-logout-closes-sockets for a game server, not
  per-resource permission-change propagation to an already-open socket. In-pack, `resync-guard`
  (missed-message resync), `backpressure-guard` (slow-consumer fan-out), `storm-guard` (reconnect
  storms), and `overwrite-guard` (optimistic-lock version checks) each mention "collaborative
  editing" only as an example payload type — none address authorization revocation on a live
  connection, confirmed by reading the actual matching lines, not just grep presence.
- [x] **New-skill candidate: `subscription-guard`? — GraphQL subscriptions bypass the authorization
  layer that protects queries/mutations.** GraphQL subscriptions run over a separate
  WebSocket transport/execution path from HTTP queries and mutations; auth middleware, decorators,
  or framework-level checks wired for the HTTP path can silently not apply to the subscription
  handshake or resolver context, letting a user receive via a live subscription a field or row they
  can't query directly. Grounded in three independent, dated 2026 CVEs: Strawberry GraphQL's
  CVE-2026-35523 (GHSA-vpwc-v33q-mq89 — auth could be skipped entirely on WS subscriptions via the
  legacy `graphql-ws` subprotocol, bypassing the `on_ws_connect` auth hook; fixed in 0.312.3); Parse
  Server's CVE-2026-32594 (the subscription WS endpoint skipped the Express middleware chain
  enforcing auth/introspection/complexity limits); and the Neo4j GraphQL library's CVE-2026-5423
  (`graphql-ws` forwarded WS `connectionParams` straight into the resolver context even with
  authorization enabled, bypassing the intended check). Novelty check: `gh api search/code`
  (`"GraphQL subscription" "authorization" "bypass"`, `"subscription" "resolver" "auth" "context"
  GraphQL`) found only generic GraphQL build skills and broad offensive pentest checklists — no
  dedicated audit skill for this specific authz-layer-split mechanic. In-pack, `grep -l -i graphql
  skills/*/SKILL.md` hits (`overwrite-guard`, `pagination-guard`, `reaccept-guard`, `sunset-guard`,
  `throttle-guard`, `trail-guard`) each mention GraphQL only incidentally as one API surface among
  several, not this mechanic.

Leads tried and rejected this round, logged so a future round doesn't re-spend search budget on
them: Kubernetes admission-webhook `failurePolicy: Ignore` fail-open (real, but every dedicated
k8s-security/Gatekeeper/Kyverno skill already names it generically); Apollo GraphQL APQ cache
poisoning (covered by `bedkillerspacex-boop/codex-skill-library` →
`graphql-apollo-persisted/SKILL.md`); chargeback/dispute evidence-deadline tracking (saturated with
multiple dedicated `stripe-dispute`/`chargeback-*` skills); Chrome MV3 service-worker ephemeral-state
loss (covered verbatim as Mandatory Rule #7 in `GoogleChrome/modern-web-guidance`'s
`chrome-extensions/SKILL.md`); Flyway/Liquibase checksum-mismatch drift (covered in depth by
`selvarajmurugesan90/ops-engineering-skills` → `database-schema-migration-with-liquibase-and-flyway/
SKILL.md`); "Sign in with Apple" email-only-on-first-authorization causing duplicate accounts (real
pain, but only anecdotal forum/issue reports, no CVE/vendor-advisory grounding); biometric
re-enrollment not invalidating a cached auth bypass (saturated across a dozen+ dedicated iOS/Swift
security skills); webhook SSRF via DNS rebinding / registration-time-only validation (already a named
`security-sweep` example category, and covered externally by dedicated SSRF-defense skills); MFA
backup-code reuse / non-atomic invalidation (two good 2026 CVEs found — Parse Server
CVE-2026-31875, Filament CVE-2026-48505 — but already a named checklist item in
`xalgorix/xalgorix` → `bypassing-two-factor-and-otp/SKILL.md`); and client-side DNS-TTL caching
outliving a cutover (a dedicated ops-procedure skill covers the infra side; the app-runtime angle
sits too close to `failover-guard`'s existing DNS/VIP-cutover material to justify a new skill today
— parked as borderline, not a clean reject).

Follow-up for the next run: three real unchecked candidates now exist above — pick whichever one's
research holds up best under a second look and is ready to write (none have had `SKILL.md` drafted
yet, so expect to spend some of the next round finishing due diligence before shipping, same as
`clipboard-guard` took two rounds). No skill shipped this round — this was a research-and-log pass,
not an implementation one, per the daily-agent process for a fully-checked-off backlog.

## Shipped `email-guard` after a fresh novelty pass (2026-11-13)

Git hygiene first: `git fetch origin main` showed local `main` and `origin/main` already identical at
`cb51363` — nothing to reconcile. `python tools/validate.py` passed (`OK: 48 skills valid and consistent
with README.`) before this round.

The only unchecked item in this file — `recall-guard`'s drift-audit — comes due ~2026-11-15, two days out.
Every prior drift-audit in this queue was run at most one day early (`throttle-guard`, `quote-guard`); two
days is a longer lead than that precedent, so left it for a future round and ran a fresh novelty-research
pass instead (delegated to a subagent to keep the search output out of context).

Six candidates were tried this round, four rejected as saturated and re-verified independently rather than
taken on the subagent's word alone:

- **Presigned/signed-URL revocation lifecycle** — REJECTED. `fozagtx/BuildOS-workflow` →
  `skills/presigned-urls-security/SKILL.md` already covers this almost verbatim (scope, TTL, "individual
  URLs cannot be revoked," blast-radius via key rotation).
- **Inventory oversell / stock-reservation race** — REJECTED. `ggrace519/claude-code-dev-studio` →
  `skills/ecom-inventory/SKILL.md` covers atomic decrement vs. read-then-write, reservation TTLs, and the
  exact "tests never run two concurrent checkouts against the last unit" pitfall. Also
  `finsilabs/awesome-ecommerce-skills` → `.../inventory-tracking/SKILL.md`.
- **CCPA/GPC "Do Not Sell" opt-out signal handling** — REJECTED, saturated by several dedicated
  `global-privacy-control`/`cpra-opt-out-signals` skills (`mukul975/Privacy-Data-Protection-Skills`,
  `ThomasMoreAI/legal-skills-open`, `aibot88/sec_skill_store`, `bhubbard/skills`).
- **Search-index ACL lag / tenant leak via stale indexing** — REJECTED. `0disoft/mustflow` →
  `search-index-integrity-review/SKILL.md` explicitly lists tenant leak, stale delete, and visibility-lag
  as symptoms it already audits.
- **Zip Slip (archive path traversal) and ReDoS** — REJECTED, both heavily saturated with dedicated skills
  across many repos.
- **Subdomain takeover / dangling DNS** — REJECTED, saturated with dozens of dedicated offensive-recon
  skills.

A seventh angle (WebSocket/SSE heartbeat interval shorter than an intermediary's idle timeout, producing a
silent "zombie" connection neither side detects as closed) came back flagged novel-but-adjacent rather than
a clean reject: real and grounded (AWS ALB's default 60s idle timeout silently dropping WS connections with
no FIN/RST; websocket.org's heartbeat guide naming ping/pong deadlines as the only reliable detection), but
this pack already has three WS/SSE-adjacent skills (`resync-guard`, `storm-guard`, `backpressure-guard`),
and `backpressure-guard` already name-checks a heartbeat that detects a dead-but-still-open socket as a
mitigation it looks for. Logging it rather than shipping a fourth skill in that cluster today — worth a
closer look only if a future round confirms it's a genuinely distinct check, not scope-splitting.

**Shipped `email-guard`**, the one candidate that cleared the bar outright: whether a self-service "change
my email" account-settings flow can be used by a hijacked session (stolen cookie, XSS, unattended device)
to make the hijack permanent — no re-authentication required beyond an existing session, no notification
to the *old* address when the change happens, and the new address going live before it confirms it's
reachable by anyone but whoever typed it. `gh api search/code` (`"email change" "old email" "notified"
"account takeover" filename:SKILL.md"`, `"email change verification race hijack" filename:SKILL.md`) found
only generic OSINT/bug-bounty catch-alls, no dedicated skill; nothing in `anthropics/skills` or `org:obra`;
nothing in-pack (`grep -i "email.change" skills/*/SKILL.md` hits only `sunset-guard`'s unrelated "email
blast" mention). Not on this pack's rejected list (checked against the admin-impersonation and
reaccept-guard/rotation-guard angles directly — different actor, different object, no overlap).

Grounded independently (re-verified via WebSearch today, not just taken from the research subagent's
report) in two real, dated, vendor-confirmed cases: **CVE-2018-19580** (GitLab ≤11.3.11/11.4.8/11.5.1,
tracked as `gitlab-org/gitlab-ce#39809`) — changing a user's email sent no notification to the *old*
address, fixed in 11.5.1 and the matching 11.4.x/11.3.x point releases; and **GHSA-x39m-3393-3qp4**
(Flowise) — an unverified new email address became the account's live login/recovery address outright, an
unverified change *being* the takeover. The OWASP Authentication Cheat Sheet's standard fix (require
current password/MFA before the change, notify both old and new addresses, hold the change until the new
one confirms) is the structure the skill's three steps follow.

Added `skills/email-guard/SKILL.md` and `examples/email-guard.md`; wired into `README.md`'s skills table,
decision table, Examples list, and intro "survived" sentence, and `examples/README.md`; bumped the 48→49
skill-count mentions (prose word and the "copying all forty-eight/forty-nine" tip). `python
tools/validate.py` → `OK: 49 skills valid and consistent with README.` Checked the one-directional
cross-reference convention other recent skills follow (`grep -n "email-guard" skills/*/SKILL.md` outside
its own file returns nothing) and matched it — this skill's own Boundaries section names `reaccept-guard`,
`rotation-guard`, and `push-guard`; none of theirs needs to name it back.

Follow-up for the next run: `recall-guard`'s drift-audit is now due in ~2 days (~2026-11-15) — per the
one-day-early precedent this should land next round or the one after. The WS/SSE heartbeat-vs-idle-timeout
angle (flagged novel-but-adjacent above) is logged but not resolved either way — worth a dedicated pass to
decide if it's genuinely distinct from `backpressure-guard`'s existing heartbeat mention before it ships or
gets rejected as scope-splitting.

## Shipped `digest-guard` after a fresh novelty pass (2026-11-12)

Git hygiene first: clone's `HEAD` was detached at `63ead0d` (the real tip of `main`, already
carrying the `quote-guard` drift-audit) while the local `main` branch ref was stale 5 commits
behind at `e2c8e4c`. `git fetch origin main` confirmed `origin/main` really is at `63ead0d` with
nothing unpushed; fixed with `git checkout main && git merge --ff-only origin/main`.
`python tools/validate.py` passed (`OK: 47 skills valid and consistent with README.`) before this
round, with no skill files touched by the sync.

The only unchecked item in this file — `recall-guard`'s drift-audit, due ~2026-11-15 — is still
3 days out, same "too soon" situation the last several rounds hit with `throttle-guard`/
`quote-guard`. Per the standing follow-up, ran a fresh novelty-research pass instead (delegated to
a subagent to keep the search output out of context).

Tried the most promising-looking lead first: **admin "login as user" / support impersonation
session audit** (does impersonation write a distinct audit entry, time-bound the session, restrict
what it can do, and surface it to the real user). **REJECTED — already closed, twice.** This exact
candidate is in `docs/backlog-archive-2026-q4.md` under two separate rounds: `AS-FOSS/aegis-skills`
→ `skills/code/authz-access-control/SKILL.md` has a dedicated "Delegation & Impersonation" section
naming scope-limits/time-boxing, an immutable actor+target+reason audit log, termination on
password change, and no-identity-dropping token minting — nearly verbatim this lead. Also
`0disoft/mustflow` → `session-management-review/SKILL.md`, `bedkillerspacex-boop/codex-skill-library`
→ `account-takeover-methodology/SKILL.md`, `claudskills.com` → `auth-isolation`, and
`trannhatbuilder/evvo-vapt-ai` → `shield_engine/skills/support-override-and-backoffice-admin-abuse/
SKILL.md` (a dedicated "Impersonation (Login-As) Trap" hunt step). No new sub-mechanic found to
justify a third look.

**Backup candidate cleared the bar: scheduled report / dashboard subscription stale-permission
audit.** The mechanic: does a scheduled/recurring report, dashboard subscription, or saved-query
digest re-check the recipient's and owner's *current* access before every send, instead of
permanently serving data under the permission snapshot taken when the schedule was created.
`gh api search/code` across four targeted queries ("scheduled report"+permission, "dashboard
subscription", "row-level security"+scheduled, "stale permission"+scheduled) found no dedicated
hit — only noise (Salesforce report-building skills) and two near-misses checked directly and
ruled out: `claudskills.com/skills/reports-and-dashboards` (generic Salesforce report build/audit,
not this mechanic) and `clawhub.ai`'s "scheduled-reports" family (agent-automation-safety audits —
approve sources/schedule/destination, cron persistence, API-key storage — a different concern).

Grounded in two real, verified mechanisms (re-verified independently via WebSearch, not just taken
from the research subagent's report): **Metabase CVE-2023-23629** — a sandboxed/restricted user
could add themselves as a recipient of another user's existing dashboard subscription and receive
the creator's unfiltered data by email (fixed in 0.43.7.1/0.44.6.1/0.45.2.1 and the 1.x
equivalents, advisory GHSA-ch8f-hhq9-7gv5); the related **CVE-2023-23628** let a sandboxed user see
the recipient list of someone else's subscription (GHSA-492f-qxr3-9rrv). And **Splunk's own
documentation** (`docs.splunk.com`, Report/Managereportpermissions): scheduled reports and alerts
only ever run as the owner, and changing an existing schedule's permissions applies only to
*future* runs — jobs already queued keep running on the old grant until someone manually
intervenes through the job manager. Checked this doesn't overlap any in-pack skill: `trail-guard`
audits whether mutations get logged at all (not schedule output correctness), `pref-guard` audits
notification opt-outs (not content access), `export-guard` audits one-off export completeness (not
a recurring schedule's access over its running lifetime), and `seat-guard`/`residency-guard` are
unrelated axes (license counts, data location).

Added `skills/digest-guard/SKILL.md` and `examples/digest-guard.md`; wired into `README.md`'s
skills table, decision table, intro "survived" sentence, and Examples list, and `examples/
README.md`; bumped the 47→48 skill-count mentions (prose word and the "copying all forty-
seven/forty-eight" tip). `python tools/validate.py` → `OK: 48 skills valid and consistent with
README.`

Follow-up for the next run: `recall-guard`'s drift-audit is now due in ~3 days (~2026-11-15) — if
still too soon, the admin-impersonation rejection above doesn't need re-checking again, but a fresh
novelty pass on new territory is fine.

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

One promising lead found, **shipped 2026-11-05 — see that day's section below for the full novelty
sweep and what was built**:

- [x] **New-skill candidate: `clipboard-guard`? — sensitive-data clipboard exposure audit.** Does the app
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
- [x] **Drift-audit queue has due dates only in prose, not as checkable items.** `reaccept-guard` (shipped
  2026-10-26), `throttle-guard` (2026-10-28), `quote-guard` (2026-10-29), and `recall-guard` (2026-11-01)
  are each meant to get a fact-check pass "once a couple of weeks have passed" — but that's only ever been
  written as a prose reminder at the bottom of each day's section, never as a trackable item, which is why
  this file has gone from 2026-07-24 to today with **zero** literal `- [ ]` lines anywhere until this round.
  **Converted 2026-11-09**: real due-dated checkbox items now exist below for each remaining skill instead
  of carrying this forward as prose — `reaccept-guard`'s own item is checked off the same day, see that
  section.
- [x] **Drift-audit due: `throttle-guard`** (shipped 2026-10-28) — fact-check its grounding ~2026-11-11.
  Done one day early, 2026-11-10 — see that day's section below.
- [x] **Drift-audit due: `quote-guard`** (shipped 2026-10-29) — fact-check its grounding ~2026-11-12.
  Done one day early, 2026-11-11 — see that day's section below.
- [x] **Drift-audit due: `recall-guard`** (shipped 2026-11-01) — fact-check its grounding ~2026-11-15.
  Done one day early, 2026-11-14 — see that day's section below.

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

## Shipped `clipboard-guard` after finishing the novelty sweep (2026-11-05)

Git hygiene first: the clone started with `HEAD` detached at `51823dd` (the actual tip of `main`), while
the local `main` branch ref and this session's `origin/main` tracking ref were both stale at `7f56de5`
(5 commits behind). `git fetch origin main` confirmed `origin/main` really is at `51823dd` with nothing
to lose (`git log main..origin/main` showed those same 5 commits, `origin/main..main` showed nothing);
fixed with `git checkout main && git merge --ff-only origin/main`. `python tools/validate.py` passed
(`OK: 43 skills valid and consistent with README.`) before starting.

Picked up the `clipboard-guard` lead logged 2026-11-03/04 and finished the novelty sweep it was waiting
on before it could ship:

- `gh api search/code` across four targeted queries (`"clipboard" "autoclear" filename:SKILL.md`,
  `"clipboard-guard"`, `"clipboard history" "leak" filename:SKILL.md`, `"OTP" "clipboard" "retention"
  filename:SKILL.md`) found only unrelated hits — UI component libraries, a literal `clipboard-guard.sh`
  hotkey script, generic broad security-audit catch-alls — no dedicated "does the app leak sensitive data
  via the clipboard" review skill.
- `gh api search/code repo:anthropics/skills` (both a `clipboard` term search and a full `filename:SKILL.md`
  listing) confirmed the official pack has no clipboard-related skill at all — its skills are
  document/office/design-tool focused (pdf, docx, xlsx, pptx, canvas-design, etc.), a different topic area
  entirely.
- `gh api search/code org:obra` for `clipboard` across the whole `obra` org (superpowers, superpowers-skills,
  superpowers-chrome, macMCP, dotfiles, etc.) turned up only unrelated utilities (a clipboard URL helper, a
  Windows clipboard interop shim, a clipboard-management MCP tool) — no audit-style skill.
- WebSearch (two queries, "standard" mode) across the community marketplaces (claudskills.com, skills.sh,
  clawhub.ai, awesomeskills.dev, skillsdirectory.com, claudemarketplaces.com) turned up only third-party
  *meta*-security scanners that audit whether a Claude *skill itself* is safe to install (data exfil,
  prompt injection) — a completely different "is this skill malicious" concern, not an "audit my app's
  clipboard handling" skill. One hit (a `clipmem` clipboard-history skill) is a feature, not an audit.
- This confirms the 2026-11-03 finding stands: the closest real coverage anywhere is a single MASVS-STORAGE
  checklist bullet inside broad mobile-pentest skills (`Masriyan/Claude-Code-CyberSecurity-Skill`,
  `jd-opensource/JoySafeter`) — not a dedicated skill. Per the pack's own house style (fold a thin,
  bullet-sized finding into an existing skill rather than add a 44th standalone one), weighed whether this
  belongs in `security-sweep` or `secret-spill` instead: rejected folding it in — `security-sweep`'s
  sensitive-data-exposure line is a generic one-liner inside a broad diff review and would stay a one-liner
  there, and `secret-spill` is incident response for a credential *already* leaked into git/CI, a different
  problem shape (remediation vs. pre-emptive audit of a live write/read path). The four-step
  enumerate-write/read → check-clear-and-platform-flag → check-read-is-paste-gated → name-the-sync-boundary
  structure has real depth, matching the bar other narrow `-guard` skills in this pack (`recall-guard`,
  `push-guard`, `pref-guard`) were held to — so it earns its own skill.

Grounded the skill in three real, dated mechanisms rather than a generic "don't leak secrets" angle: the
2020 iOS 14 clipboard-access-notification rollout (publicly caught TikTok/LinkedIn/Reddit/others reading
the pasteboard on nearly every keystroke or foreground event, not just on paste), Android/Samsung
cross-device clipboard sync and Windows Cloud Clipboard (Win+V history, roams via a Microsoft account)
both persisting a copied secret to a second device or a visible history list, and the real platform APIs
that exist specifically to opt out of that (`UIPasteboard.expirationDate`/`localOnly` on iOS,
`ClipDescription.EXTRA_IS_SENSITIVE` on Android) so the gap is named as fixable, not an unavoidable
platform limitation.

Added `skills/clipboard-guard/SKILL.md` and `examples/clipboard-guard.md`; wired into `README.md`'s skills
table, decision table, Examples list, and intro "survived" summary; bumped the 43→44 skill-count mentions
(prose word and the "copying all forty-three/forty-four" tip). `python tools/validate.py` →
`OK: 44 skills valid and consistent with README.` Checked the one-directional cross-reference convention
other recent `-guard` skills follow (`grep -n "recall-guard" skills/*/SKILL.md` shows no other skill
mentions it back) and matched it — `clipboard-guard`'s own Boundaries section names `security-sweep` and
`secret-spill`, neither of theirs needs to name it back.

Follow-up for the next run: the drift-audit-due-dates item (logged 2026-11-03) still isn't due — earliest
is `reaccept-guard` ~2026-11-09. No other unchecked items remain in this file as of this round.

## Shipped `dormancy-guard` after a fresh novelty pass (2026-11-06)

Git hygiene first: the clone started with `HEAD` detached at `8cda287` (the real tip of `main`), while the
local `main` branch ref was stale at `7f56de5` (6 commits behind, matching `origin/main`). `git fetch origin
main` confirmed `origin/main` is at `8cda287` with nothing to lose; fixed with `git checkout main && git
merge --ff-only origin/main`. `python tools/validate.py` passed (`OK: 44 skills valid and consistent with
README.`) before starting.

The only unchecked item in this file — the drift-audit-due-dates item logged 2026-11-03 — still isn't
actionable: `grep -c '\[ \]' BACKLOG.md` showed exactly one unchecked line, and its earliest due sub-item
(`reaccept-guard`, ~2026-11-09) hasn't arrived yet (today is 2026-11-06). Per the daily-agent process for a
backlog with nothing actionable, ran a fresh research pass for new-skill candidates instead of forcing a
pick or inventing busywork.

Three candidates researched this round:

1. **Cross-tenant/multi-tenant data-isolation audit (shared-schema SaaS missing a `tenant_id` filter
   somewhere in the query path).** REJECTED, saturated. `gh api search/code` for `"tenant_id"
   "cross-tenant"` and `"row-level security" "tenant"` under `filename:SKILL.md` turned up a `saas-multi-
   tenant` skill copy-pasted across dozens of repos/collections (clearly a popular shared template:
   `sickn33/agentic-awesome-skills`, `FrancoStino/opencode-skills-collection`, `TheLobbi/claude`,
   `marwan562/agents-skills`, `boisenoise/skills-collections`, `aibot88/sec_skill_store`, and ~15 more hits
   in a single search page), plus dedicated ones under different names (`lopadova/AskMyDocs` →
   `cross-tenant-isolation/SKILL.md`, `OpenAEV-Platform/openaev` → `review-multi-tenancy/SKILL.md`). Not a
   close call — this mechanic already has multiple named, dedicated skills in wide circulation.
2. **OAuth/JWT refresh-token rotation race (concurrent refresh requests triggering false-positive reuse-
   detection and a spurious full-session logout).** REJECTED for now, but on a build/audit distinction
   rather than clear saturation. Found real coverage (`lauren-framework/lauren-framework` →
   `jwt-refresh-rotation/SKILL.md`, `bedkillerspacex-boop/codex-skill-library` → `jwt-refresh-token-
   patterns/SKILL.md`, both fetched and read in full) — but both are *build* skills (how to implement
   rotation/reuse-detection/family-revocation from scratch), not an *audit* of an existing implementation's
   concurrent-refresh race specifically. Possibly still a real gap, but didn't find a strong enough grounding
   (no named, dated incident the way `dormancy-guard` below has three) to justify the research time today;
   logging the angle rather than dropping it — worth a proper pass if a future round has spare research
   budget and no better lead.
3. **Inactivity/dormancy-sweep blind to non-interactive activity (API keys, webhooks, OAuth apps, service
   accounts) — shipped, see below.** `gh api search/code` for `"dormant account"`, `"inactivity" "last_login"
   "service account"`, and `"account reaping" OR "license reclamation"` under `filename:SKILL.md` found zero
   dedicated coverage (only tangential hits: IAM/RBAC review skills that mention dormancy as one bullet, a
   Microsoft Entra guest/inactive-account audit skill that's platform-specific and read-only, not a general
   app-level policy audit). Checked in-pack too: `grep` across `skills/*/SKILL.md` for "dormant", "inactiv",
   "service account", "last_login" found only tangential mentions (`blast-guard`'s audience-query example
   uses a `last_login` cohort for email sends — a different mechanism; `reaccept-guard` names "webhook/service
   account" as a surface for ToS re-acceptance gates, not inactivity measurement; `seat-guard` audits seat
   enforcement being too *loose*, the mirror-opposite of this skill's "reclamation too blind" angle). WebSearch
   (two queries, "standard" mode) confirmed the problem is real with three concrete, dated anchors: Atlassian
   community support explicitly confirms Jira Cloud's inactivity-based site suspension counts only interactive
   login, not API traffic (`SUSPENDED_INACTIVITY` hitting automation accounts that were making calls the whole
   time); a Broadcom/CloudHealth doc describes a deactivated account losing the API access it needs to keep
   its own linked assets' status current, so those assets silently go stale; and a July 2025 fintech-vendor
   (Maxsight) postmortem describes active institutional accounts having users deactivated and API keys removed
   during routine inactivity-based offboarding, requiring incident response to restore.

Added `skills/dormancy-guard/SKILL.md` and `examples/dormancy-guard.md`; wired into `README.md`'s skills
table, decision table, Examples list, and intro "survived" summary; bumped the 44→45 skill-count mentions
(prose word and the "copying all forty-four/forty-five" tip). Had to trim the first description draft from
1173 to under the 1024-char validator ceiling. `python tools/validate.py` → `OK: 45 skills valid and
consistent with README.` Checked the one-directional cross-reference convention other recent skills follow
(`grep -n "dormancy-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it — this
skill's own Boundaries section names `seat-guard`, `reaccept-guard`, and `push-guard`; none of theirs needs
to name it back.

Follow-up for the next run: the drift-audit-due-dates item (2026-11-03) still isn't due — earliest is
`reaccept-guard` ~2026-11-09. The refresh-token-rotation-race angle (candidate 2 above) is logged but not
yet researched enough to ship or reject — worth a real grounding pass (named incidents, not just build-skill
coverage) before deciding either way.

## Shipped `pagination-guard`; closed out the refresh-token-rotation-race lead as covered (2026-11-07)

Git hygiene first: `git fetch origin main` showed local `main` and `origin/main` already identical at
`e2c8e4c` — nothing to reconcile. `python tools/validate.py` passed (`OK: 45 skills valid and consistent
with README.`) before starting. The only unchecked item in this file (drift-audit-due-dates, 2026-11-03)
still isn't due — earliest is `reaccept-guard` ~2026-11-09 — so this round picked up the open research
thread from 2026-11-06 instead of forcing a pick or inventing busywork.

**Closed candidate 2 from 2026-11-06 (refresh-token concurrent-refresh race / false-positive reuse
detection) — REJECTED, covered.** Last round found only *build* skills (implement rotation from scratch)
and flagged it as possibly still a real audit-side gap pending a grounding pass. This round's grounding
pass found a dedicated, generic *audit* skill that names the exact mechanic: `Lucas-Belucci-Bellini/
All-Skills-for-the-claude-code` → `auth-refresh-token-replay-boundaries/SKILL.md` (mirrored twice in the
same repo) — its workflow explicitly tests "parallel refresh races," its verification checklist literally
reads "Parallel refresh behavior is deterministic and tested," and its positive trigger example is "Two
browser requests refresh the same session at nearly the same time" — i.e. exactly this candidate, generically
framed, not tied to one codebase. `vomatt/vomatt-web` → `.claude/skills/verify-refresh-rotation/SKILL.md`
independently confirms the mechanic is real and worth a dedicated check (a from-scratch TLA+-style model
checker proving concurrent page loads can't make the backend see a spent token and sign the user out) —
repo-specific rather than generic, but corroborating evidence the failure mode is a known, named thing people
build dedicated tooling for, not a novel angle. Between those two plus the two build-skills found last round,
this mechanic has real, independent, dedicated coverage from more than one direction — closing it rather than
carrying it forward again.

**New candidate tried and also REJECTED, covered:** idempotency-key audit for payment/order/webhook endpoints
(key-scoping bugs, TTL-driven double-execution, non-atomic check-then-insert of the idempotency record itself
racing two concurrent retries). `gh api search/code` for `"idempotency" "double charge" filename:SKILL.md`
found a dedicated `idempotency-audit` skill duplicated across four agent-tool variants in one repo
(`1arley/volibear` → `.claude/`, `.codex/`, `.agents/`, `.opencode/skills/idempotency-audit/SKILL.md`) whose
own text names this round's exact angle: "key verified before effect," request→request→request and
request→response-lost→retry as the two test shapes, and payments/rewards/creation/webhooks/notifications/
counters as the areas it's built for — plus independent coverage elsewhere (`j4flmao/agent-skills` →
`idempotency`, `dykyi-roman/awesome-claude-code` → `check-idempotency`, `sigistry/marketplace` →
`idempotency-patterns`, `knarayanareddy/Vibecode-like-a-dev` → `idempotency-and-retries`,
`aws/agent-toolkit-for-aws` → `agents-pay`). Saturated from several independent directions — not a close
call, rejected without needing a deeper read.

**Shipped `pagination-guard`** after the above two rejections, on a third angle that held up under the same
sweep: whether a multi-page listing/export/incremental-sync stays correct while the underlying rows are
inserted/deleted/updated between page fetches, rather than only ever tested against a table that holds
still. Two distinct bug shapes, both real and separately filed, not a hypothetical: an `ORDER BY` with no
unique tiebreaker letting tied rows land on either side of a page boundary (Strapi `#18727`, GitLab `#1952`
and `#37078` — all independently reproduce "item appears on two pages, another never appears," root-caused
to a non-unique sort key), and offset (`LIMIT`/`OFFSET`) pagination where a delete/insert ahead of the
current page shifts every later row and skips or re-shows one on the next fetch (`SeaQL/seaography #19`).
Checked in-pack first: `selectall-guard` audits a bulk *action's* filter re-resolution once it starts
writing, `export-guard` audits silent row-count caps/timeouts and spreadsheet ID-mangling, `stale-guard`
audits cache invalidation — none of the three cover whether the underlying read-only pagination itself is
correct under concurrent mutation, which is a different failure shape from all three. External sweep: `gh
api search/code` across four queries (`"pagination" "tiebreaker"`, `"cursor pagination" "stable" "unique
key"`, literal `pagination-guard`, `"deep pagination" audit`, all `filename:SKILL.md`) found many *build*
skills ("how to design/implement pagination" — api-design, pagination-and-filtering, pagination-performance,
etc., scattered across dozens of repos) but zero dedicated *audit* skill checking whether an existing
implementation stays correct once concurrent writes happen during the scan; a literal `pagination-guard`
name search returned no SKILL.md hits at all. Checked `anthropics/skills` and `org:obra` directly — neither
has anything pagination-related. WebSearch (two "standard" queries) supplied the four named GitHub issues
above as the real-incident grounding this pack's bar asks for.

Added `skills/pagination-guard/SKILL.md` and `examples/pagination-guard.md`; wired into `README.md`'s skills
table, decision table, Examples list, and intro "survived" summary; bumped the 45→46 skill-count mentions
(prose word and the "copying all forty-five/forty-six" tip). First description draft was 1218 chars, over
the 1024-char validator ceiling — trimmed twice to fit. `python tools/validate.py` → `OK: 46 skills valid
and consistent with README.` Checked the one-directional cross-reference convention other recent skills
follow (`grep -n "pagination-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it
— this skill's own Boundaries section names `selectall-guard`, `export-guard`, and `stale-guard`; none of
theirs needs to name it back.

Follow-up for the next run: the drift-audit-due-dates item (2026-11-03) still isn't due — earliest is
`reaccept-guard` ~2026-11-09, so it should finally be actionable in ~2 days. No other unchecked items or
open research leads remain in this file as of this round.

## Shipped `failover-guard` after a fresh novelty pass (2026-11-08)

Git hygiene first: the clone's `HEAD` was detached at `2374d08` (`pagination-guard`, the real tip of
`main`) while the session's cached `origin/main` tracking ref was stale one commit behind at `e2c8e4c` —
`git fetch origin main` showed the ref update to `2374d08` with nothing actually unpushed (a prior round's
commit had already landed on the real remote; the local clone's ref cache was just stale), confirmed with
`git log origin/main..HEAD` / `..main` both empty after `git checkout -B main 2374d08`. `python
tools/validate.py` passed (`OK: 46 skills valid and consistent with README.`) before starting. The only
unchecked item in this file (drift-audit-due-dates, 2026-11-03) still isn't due — today is 2026-11-08,
earliest is `reaccept-guard` ~2026-11-09 — so this round ran a fresh novelty-research pass instead of
forcing a pick or inventing busywork, per the daily-agent process for a backlog with nothing actionable.

Delegated the research to a subagent to keep the (large) search output out of the main context; it
checked three candidates:

1. **Async malware/virus-scan race on uploads** (file served/downloadable/processed while a background
   scan is still pending, with no fail-open/fail-closed decision and no re-check if the verdict comes back
   positive after the file was already downloaded). REJECTED, saturated. `gh api search/code` for
   `"virus scan" "race"`, `"quarantine" "upload" "scan"`, `"malware scan" "upload"`, `"async" "virus"
   "quarantine"` (all `filename:SKILL.md`) found a dedicated `file-upload-virus-scanning` skill duplicated
   across many independent repos/collections, plus independently named siblings (`file-upload-virus-scan-
   hook`, a `file-upload-security` family across half a dozen more repos). Fetched the Salesforce-targeted
   copy directly — it already names this candidate's exact mechanic (a `Scan_Pending` window, async preview
   generation exposing infected files before the scan completes, the fail-open/fail-closed timeout decision,
   scheduled rescanning for new signatures). Not a close call.
2. **Inbound webhook duplicate-delivery/replay/out-of-order audit**, as a narrower thing than `job-warden`'s
   existing generic "non-idempotent handler under at-least-once delivery" coverage. REJECTED, saturated —
   one of the most commonly templated skill topics found this session: `"webhook" "event id" "idempotency"`,
   `"webhook" "out of order"`, `"webhook" "replay" "timestamp"`, `"webhook signature verification" "retry"`
   (all `filename:SKILL.md`) each returned 1,300–7,600 hits with dedicated skills on point
   (`payment-webhook-idempotency`, `webhook-handler-patterns`, `webhook-handling`, `add-webhook-handler`,
   plus dozens of per-vendor `-webhooks-events` skills for Stripe/Twilio/Adobe/Ramp/etc.).
3. **`failover-guard` — shipped.** Audits whether an automatic database primary failover can silently lose
   a write already acknowledged to the caller as durable: async/semi-sync replication lag between the last-
   acknowledged write and the promoted replica's actual position; a split-brain window where the old primary
   keeps accepting writes after a new one is promoted elsewhere because fencing never reached the very node a
   partition isolated, producing two divergent write histories; and no caller-visible signal that either
   happened — the app just resumes serving the new primary as if nothing was at risk. External sweep
   (`"split-brain" "promoted" "acknowledged"`, `"failover" "write loss"`, `"synchronous replication"
   "acknowledged" "lost"`, all `filename:SKILL.md`, plus `repo:anthropics/skills` and `org:obra`, both empty)
   found only build/ops skills (HA-topology setup, DBRE-persona skills, a DDIA-book chapter skill) — fetched
   the closest-looking one (`bookforge-ai/bookforge-skills` → `replication-failure-analyzer`) directly via
   its raw URL and confirmed it's a symptom-driven incident-diagnosis skill spanning three broad failure
   classes (leader failover, replication lag, quorum edge cases), not a proactive audit of whether an
   existing app's write-acknowledgment contract specifically survives failover — a real but different framing
   from this candidate's narrower, code-review-shaped angle. In-pack: only `residency-guard` mentions
   "failover" at all, and strictly as "does the failover *target* satisfy the geographic/residency boundary"
   — a compliance question, not this skill's durability question; confirmed via `grep` directly, no overlap.
   Grounded in GitHub's October 21, 2018 public postmortem (a ~43-second network partition during routine
   maintenance caused Orchestrator to promote a West Coast MySQL replica while the original East Coast
   primary, unreachable to the orchestrator but not actually dead, kept committing writes locally for several
   more seconds before anything stopped it — two divergent datasets reconciled over more than a day) as the
   canonical named/dated case for exactly this mechanic, rather than generic "replication can lag" advice.

Added `skills/failover-guard/SKILL.md` and `examples/failover-guard.md`; wired into `README.md`'s skills
table, decision table, Examples list, and intro "survived" summary; bumped the 46→47 skill-count mentions
(prose word and the "copying all forty-six/forty-seven" tip). First description draft was 1174 chars, over
the 1024-char validator ceiling — trimmed once to fit. `python tools/validate.py` → `OK: 47 skills valid
and consistent with README.` Checked the one-directional cross-reference convention other recent skills
follow (`grep -n "failover-guard" skills/*/SKILL.md` outside its own file returns nothing) and matched it —
this skill's own Boundaries section names `migration-guard`, `skew-check`, and `residency-guard`; none of
theirs needs to name it back.

Follow-up for the next run: the drift-audit-due-dates item (2026-11-03) is now due — `reaccept-guard`
turns 2 weeks old 2026-11-09 (tomorrow). Finally run that fact-check pass next: confirm `reaccept-guard`'s
grounding (ToS/EULA re-acceptance gate coverage of old mobile builds/direct API integrations) still holds,
or note what's drifted. `throttle-guard` (~2026-11-11), `quote-guard` (~2026-11-12), and `recall-guard`
(~2026-11-15) come due after that — pick them up as each date arrives rather than carrying this forward as
prose again.

## Drift-audit: `reaccept-guard` fact-check, due-dates item converted to real checkboxes (2026-11-09)

Git hygiene first: clone's `HEAD` was detached at `b76f633` (`failover-guard`, the real tip of `main`)
while the local `main` branch ref was stale 2 commits behind at `e2c8e4c`. `git fetch origin main`
confirmed `origin/main` is really at `b76f633` with nothing unpushed; fixed with `git checkout main &&
git merge --ff-only origin/main`. `python tools/validate.py` passed (`OK: 47 skills valid and consistent
with README.`) before starting, with no skill files touched by the sync.

`reaccept-guard` turned 2 weeks old today, making it the first item in the drift-audit queue logged
2026-11-03 to actually come due. Ran the fact-check pass rather than shipping a new skill this round —
no other item was more clearly finishable, and this file's own prior rounds kept deferring this exact
check.

**Fact-check result: grounding still holds, nothing drifted.**

- `reaccept-guard`'s shipped grounding (archived 2026-10-26 entry) rests on two legs: (1) Google's Zero
  Touch Enrollment customer API returning a 403 with a `TosError`/`latestTosAccepted: false` body for
  stale-ToS API requests, as a real, named example of *server-side, per-request* policy-version
  enforcement independent of any client UI. Re-fetched the live reference page
  (`developers.google.com/zero-touch/reference/customer/rest/v1/TosError`) via WebSearch today — it still
  describes exactly this: a 403 keyed off `latestTosAccepted: false`, fixable only by accepting the terms
  in the zero-touch portal, not by retrying the API call. Unchanged. (2) The claim in the skill body that
  "app-store review lag (minimum days, sometimes weeks)" leaves a real population on pre-bump mobile
  builds. A 2026-dated WebSearch on current App Store / Play Store review timelines found the claim, if
  anything, understated for iOS right now: Apple's own stated target is 90% of submissions in under 24–48
  hours, but multiple 2026 sources (gigage per mjtsai.com's March 2026 "Mac App Store Review Times
  Increasing" post, and vendor write-ups through mid-2026) describe routine updates stretching to 7–14
  days and new-app review up to 30+ days during slow periods; Google Play updates clear faster (hours),
  but a new developer account or closed-testing requirement still adds real days. Net: the skill's
  "minimum days, sometimes weeks" framing for stale-build persistence is still accurate, not drifted.
- No change needed to `skills/reaccept-guard/SKILL.md` — the audit confirms the existing text rather than
  surfacing anything to fix. Documenting that explicitly here (rather than silently doing nothing) is the
  point of having a drift-audit queue at all: a "still holds" verdict is itself the useful output of this
  check, distinct from never having checked.

**Converted the due-dates-only-in-prose item into real per-skill checkboxes**, per the standing follow-up
this file has carried since 2026-11-03: checked off that meta-item above, and added three new unchecked
`- [ ]` items — `throttle-guard` (~2026-11-11), `quote-guard` (~2026-11-12), `recall-guard`
(~2026-11-15) — so each future drift-audit is a trackable line instead of a prose reminder someone has to
remember to re-derive from dates buried in old sections.

`python tools/validate.py` → `OK: 47 skills valid and consistent with README.` (unchanged — this round
touched no skill files, only `BACKLOG.md`).

Follow-up for the next run: `throttle-guard`'s drift-audit comes due ~2026-11-11 (in ~2 days) — probably
still too soon; if so, run a fresh novelty-research pass instead of forcing either a drift-audit or a new
skill before its date arrives.

## Fresh novelty pass (6 candidates, all rejected) + `throttle-guard` drift-audit done a day early (2026-11-10)

Git hygiene first: clone's `HEAD` was detached at `9d81626` (the real tip of `main`, already carrying
`pagination-guard`, `failover-guard`, and the `reaccept-guard` drift-audit) while the local `main` branch
ref was stale 3 commits behind at `e2c8e4c`. `git fetch origin main` confirmed `origin/main` really is at
`9d81626` with nothing unpushed (`git log origin/main..HEAD` empty); fixed with `git checkout main && git
merge --ff-only origin/main`. `python tools/validate.py` passed (`OK: 47 skills valid and consistent with
README.`) before this round, with no skill files touched by the sync.

`throttle-guard`'s drift-audit comes due ~2026-11-11 — one day from today — which the prior round flagged
as "probably still too soon." Ran a fresh novelty-research pass first (delegated to a subagent to keep
the search output out of context), per that same note's fallback instruction. Six candidates were tried
and **all six rejected as saturated**, none clearing this pack's novelty bar:

1. **CSV/formula-injection in exports** — already named in-pack: `skills/security-sweep/SKILL.md:27`
   covers it directly (CVE-2026-45263, leading-quote-prefix fix). Not a gap at all.
2. **Idle-transaction-holding-a-lock-across-a-network-call / long-held-transaction lock contention** —
   saturated by dedicated ops/tuning skills (`isdaniel/pgtuner_mcp` → `pg-lock-diagnosis`,
   `pg-connection-analysis`; `SkillMedev/skills` → `connection-pool-tuner`; `jeremylongshore/
   tons-of-skills-marketplace` → `monitoring-database-transactions`; `jiayaoqijia/cryptoskill` →
   `set-query-and-lock-timeouts`).
3. **Outbox pattern / dual-write atomicity (DB commit + event publish)** — saturated by name
   (`anurag-azure/skills` → `outbox-pattern`, `curiositech/windags-skills` →
   `outbox-pattern-implementation`, plus a dozen+ broader event-driven-architecture skills).
4. **Observability-pipeline PII/secret scrubbing (Sentry et al. not redacting sensitive fields)** —
   saturated, including by the official vendor: `getsentry/sentry-for-ai` →
   `skills-legacy/sentry-elixir-sdk`; also `aibot88/sec_skill_store` → dedicated `sentry-data-handling`,
   `sentry-security-basics`, `sentry-policy-guardrails`.
5. **Stale authenticated page via bfcache after logout on a shared device** — saturated from the
   security side: `RedHatProductSecurity/prodsec-skills` → `session-management-cookies` and a direct
   OWASP-WSTG-mapped `cookie-attacks` (`wstg-athn-06`) skill. bfcache itself is otherwise only a
   *performance* topic elsewhere, but the security angle this candidate needed is already named there.
6. **Mobile screenshot/task-switcher leakage via missing `FLAG_SECURE`** — saturated: named explicitly
   across multiple *dedicated* mobile-security skills (`0x0pointer/skills` → `android-security`/
   `ios-security`; `GoldenWing-360/claude-security-skills` → `android-security`; `Amey-Thakur/AI-SKILLS`
   → `mobile-app-security`; `CyberStrikeus/CyberStrike` → MITRE ATT&CK `T1513_screen-capture`) — unlike
   `clipboard-guard`'s thin-checklist-bullet gap, this one has real dedicated coverage, not just a
   one-liner in a broad catalog.

With nothing shippable from that sweep, ran the `throttle-guard` drift-audit a day early instead of
leaving the round empty — low-risk, genuinely useful, and nothing in the backlog rules requires waiting
for the exact date rather than treating it as an earliest-due marker.

**Drift-audit result: grounding still holds, nothing drifted.**

`throttle-guard`'s novelty claim (shipped 2026-10-28) was never a single named incident — it rests on
"build-side guidance for in-memory/per-instance rate limiting is everywhere, but no dedicated *audit*
skill reviews existing code for the drift" (per-instance counter under scale-out, non-atomic
check-then-increment on a shared store, a second path that bypasses the shared counter entirely). Re-ran
four fresh `gh api search/code` queries today (`"rate limit" "per instance" "audit" filename:SKILL.md`,
`"distributed rate limit" "check-then-increment" filename:SKILL.md`, `"rate limit" "fleet-wide"
filename:SKILL.md`, plus a literal `"throttle-guard"` name check) — all hits are either unrelated (other
projects' own `throttle-guard` scripts/configs with no relation to rate-limit auditing) or, like the
original sweep found, pure *design/implementation* skills: fetched `LineLuLan/line-harness` →
`codex/skills/api-rate-design/SKILL.md` directly to confirm, and its frontmatter is explicit —
`category: backend`, outputs `"Rate limiting algorithm implementations"`, triggers `"rate limit design"`/
`"token bucket"` — a build skill, not an audit skill. No dedicated audit skill for this mechanic has
appeared since 2026-10-28; the gap this skill fills is still real. The underlying technical claims
(`INCR`/`EXPIRE` atomicity, Kubernetes `replicas > 1` meaning independent processes, most client
rate-limit libraries failing open by default) are stable platform/library facts, not the kind of thing
that drifts month to month, and nothing found today contradicts them. No change needed to
`skills/throttle-guard/SKILL.md`.

`python tools/validate.py` → `OK: 47 skills valid and consistent with README.` (unchanged — this round
touched no skill files, only `BACKLOG.md`).

Follow-up for the next run: `quote-guard`'s drift-audit comes due ~2026-11-12 (in ~2 days) — probably
still too soon; `recall-guard`'s comes due ~2026-11-15. If neither is actionable yet, run a fresh
novelty-research pass rather than forcing a pick or inventing busywork — six rejected angles already
logged above so the next round doesn't re-spend search budget on them.

## Drift-audit: `recall-guard` fact-check, done a day early (2026-11-14)

Git hygiene first: clone's `HEAD` was detached at `cb67318` (`email-guard`, the real tip of `main`) while
the local `main` branch ref was stale 1 commit behind at `cb51363`. `git fetch origin main` confirmed
`origin/main` really is at `cb67318` with nothing unpushed; fixed with `git checkout main && git merge
--ff-only origin/main`. `python tools/validate.py` passed (`OK: 49 skills valid and consistent with
README.`) before this round, with no skill files touched by the sync.

`recall-guard`'s drift-audit was the only unchecked item in this file, due ~2026-11-15 — one day from
today. Same situation the last three drift-audits (`throttle-guard`, `quote-guard`) were in when they ran
a day early with no rule against it; did the same here rather than running a full novelty-research sweep
the day before the one actionable item on the list comes due.

**Fact-check result: grounding still holds, nothing drifted.**

`recall-guard`'s shipped grounding (archived 2026-11-01 entry, restated in the skill body) rests entirely
on one named, dated case: **CVE-2026-28950**, patched in iOS 26.4.2 / iPadOS 26.4.2 and iOS 18.7.8 /
iPadOS 18.7.8, where the OS notification database retained a cached copy of message content (including
Signal previews) after the sending app's own deletion/disappearing-messages logic had already run, later
read back by forensic-extraction tooling. Re-checked via WebSearch today against Apple's own advisory
(`support.apple.com/kn-in/127002`, "About the security content of iOS 26.4.2 and iPadOS 26.4.2") and
independent reporting (SecurityWeek, Malwarebytes, The Hacker News, SOC Prime, NVD's CVE-2026-28950 entry):

- Patch versions match exactly — iOS/iPadOS 26.4.2 and 18.7.8, released April 22, 2026 (NVD and Apple's
  advisory agree; one secondary aggregator claimed May 2, trusted Apple's own dated advisory over it).
- The Signal tie-in matches — multiple outlets (404 Media as the original source, repeated by The Hacker
  News, SecurityWeek, Malwarebytes, Neowin) confirm FBI investigators extracted Signal message content
  from the OS notification store in a real case, after the app's own deletion (and in the reported case,
  after Signal had been uninstalled) — exactly the "copy made before recall could reach it" mechanic the
  skill is built around. Confirmed the bug was in iOS notification logging, not any break of Signal's
  end-to-end encryption — Signal's own statement ("no action needed... to protect Signal users on iOS")
  matches the skill's framing that this is a platform-layer copy outside the app's control, not an app bug.
- One minor imprecision, not worth editing the skill over: a single secondary outlet (not Apple's advisory)
  put the retention window at "up to a month," while the skill says content was read back "months after"
  deletion. The skill doesn't commit to an exact duration beyond "months," and the underlying point — a
  real, non-trivial gap between app-layer deletion and OS-layer purge — holds regardless of whether the
  precise figure is weeks or months. Logging the nuance here per this file's drift-audit convention rather
  than treating it as a correction.

No change needed to `skills/recall-guard/SKILL.md`. `python tools/validate.py` → `OK: 49 skills valid and
consistent with README.` (unchanged — this round touched no skill files, only `BACKLOG.md`).

Follow-up for the next run: with this checked off, **zero unchecked items remain in this file** — no
drift-audit comes due again until a future skill ships and ages two weeks. Per the daily-agent process for
a fully-checked-off backlog, the next round should run a fresh novelty-research pass for new-skill
candidates rather than inventing busywork or re-checking any of the drift-audits/rejections already
confirmed above.

## Drift-audit: `quote-guard` fact-check, done a day early (2026-11-11)

Git hygiene first: clone's `HEAD` was detached at `84bb57b` (the real tip of `main`, already carrying
`pagination-guard`, `failover-guard`, the `reaccept-guard` drift-audit, and the `throttle-guard`
drift-audit) while the local `main` branch ref was stale 4 commits behind at `e2c8e4c`. `git fetch
origin main` confirmed `origin/main` really is at `84bb57b` with nothing unpushed; fixed with `git
checkout main && git merge --ff-only origin/main`. `python tools/validate.py` passed (`OK: 47 skills
valid and consistent with README.`) before this round, with no skill files touched by the sync.

`quote-guard`'s drift-audit comes due ~2026-11-12 — one day from today. Same situation the prior round
was in with `throttle-guard` (also one day early), and that round's own note didn't rule out doing it
early again, so ran the fact-check now rather than re-running a full novelty-research sweep the day
after six candidates were already rejected — re-spending that search budget today was unlikely to turn
up a seventh.

**Fact-check result: grounding still holds, with one real nuance worth noting but not acting on.**

- `quote-guard`'s shipped grounding (archived 2026-10-29 entry) rests on two legs: (1) *Kahn v. Walmart,
  Inc.*, 7th Cir. No. 23-1751 — re-checked via WebSearch today against Justia's opinion summary and
  Bloomberg Law's coverage. Confirmed as decided July 3, 2024 (Chief Judge Sykes, Circuit Judges
  Hamilton and Lee), reversing the district court's dismissal, with the panel explicitly rejecting the
  theory that a receipt showing the price actually charged dispels the deception caused by a different
  price shown earlier ("consumers should not be required to audit their purchases to ensure they
  received the advertised prices"). Matches the skill's citation and claim exactly — unchanged, still
  good law as of today (no indication of further appeal or vacatur in any result). (2) Stripe's
  `PaymentIntents` capture API rejecting an `amount_to_capture` greater than the originally authorized
  amount — re-checked via WebSearch today against Stripe's own capture and overcapture docs. Confirmed
  as still the *default* behavior: capturing without an amount takes the full authorized amount, and
  `amount_to_capture` can go lower but not higher, under ordinary capture.
- **Nuance found, not a contradiction:** Stripe now has a separate opt-in "overcapture" feature for
  certain eligible card payments, which raises the ceiling to a `maximum_amount_capturable` field above
  the original authorization (via an issuer-granted allowance), and a distinct "incremental
  authorization" mechanism that explicitly raises the authorized amount itself before capture. Neither
  changes the skill's core claim for the *default*, unmodified capture path the skill is auditing
  against — a merchant has to deliberately opt into overcapture or request an incremental authorization;
  code that hasn't done either still gets a hard API rejection on an over-authorization capture attempt,
  exactly as the skill says. Also confirmed overcapture explicitly does not apply to partially-authorized
  transactions, so it doesn't create a silent-overcharge path there either. No change made to
  `skills/quote-guard/SKILL.md` — the audit confirms the existing text rather than surfacing a drift to
  fix; noting the nuance here is the point of a drift-audit queue (so the next person checking doesn't
  have to re-derive it), not grounds to edit a skill whose central claim is unaffected.

`python tools/validate.py` → `OK: 47 skills valid and consistent with README.` (unchanged — this round
touched no skill files, only `BACKLOG.md`).

Follow-up for the next run: `recall-guard`'s drift-audit comes due ~2026-11-15 (in ~4 days) — still too
soon. If nothing else is actionable, run a fresh novelty-research pass rather than forcing a pick or
inventing busywork; the six candidates rejected 2026-11-10 don't need re-checking again so soon.
