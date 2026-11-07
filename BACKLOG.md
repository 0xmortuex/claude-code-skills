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
