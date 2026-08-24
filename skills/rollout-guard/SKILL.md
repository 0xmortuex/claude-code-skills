---
name: rollout-guard
description: Review a mobile app release, staged rollout, or forced-update decision for failure modes specific to shipping through an app store, not a backend deploy. Checks for a defined rollout halt threshold (crash-free rate, ANR rate) instead of "eyeball it," that incident response doesn't assume App Store/Play Store review turnaround is a hotfix SLA, that a forced (blocking) upgrade is reserved for genuinely critical cases rather than a default nudge, and that the backend tolerates old client versions nobody can force to update. Use for a mobile release plan, a staged/phased rollout, "should this be a forced update," an app-store hotfix under time pressure, minimum-supported-version/version-gating logic, or a kill-switch/remote-config flag standing in for a client fix. Distinct from skew-check (backend mixed-version windows in minutes) and ship-it (deploy checklists) — this is the client-binary distribution tail, in weeks to years, plus the review clock neither accounts for.
---

# rollout-guard

A backend deploy is reversible in minutes: roll back the container, the old code is live again. A mobile app release is not. Once a build is approved and a user installs it, there is no `rollback` — halting a staged rollout stops *new* installs, but everyone who already updated keeps the build you're trying to take back. And getting a fix in front of anyone requires clearing app-store review first, a queue you don't control and can't reliably time. Teams that treat a mobile release like a backend deploy — assume "we'll just hotfix it" or "we'll pause the rollout" — find out the difference during an incident, not before.

Two mechanisms make this genuinely different from `skew-check`'s mixed-version deploy window or `ship-it`'s release checklist, and both need to be reasoned about explicitly:

1. **The review clock is not your incident clock.** Apple's standard review typically clears in under 48 hours but has no guaranteed SLA; expedited review exists for genuinely critical fixes but is a discretionary favor Apple can throttle if a team leans on it routinely, not a service you can schedule around. Google Play review is usually faster but not instant either. Anything that must respond to an incident in minutes — kill a broken feature, disable a broken endpoint, change a rate limit — has to already be reachable from a server-side switch the *current* build ships with. If the plan for "what do we do when this breaks in prod" is "we'll push a fix," that plan has an unbounded, platform-controlled delay baked into it that nobody wrote down.

2. **The client-version tail is long and partly unforceable.** Some users are offline when the update is pushed, some are on an OS version too old to install the new build, some just decline. A backend serving a mobile client can't assume "everyone's on the latest version within a couple weeks" the way a web deploy can assume "everyone's on the latest JS bundle by the next page load." The compatibility window `skew-check` reasons about in minutes-to-hours, this skill reasons about in weeks-to-years, for the same underlying question: can the client version actually in the field talk to the backend version actually running.

## What to check, in order

**1. Does the rollout have a defined halt threshold, not a vibe?**
A phased rollout only limits blast radius if someone is watching a number and has already decided what value stops it. Ask for the actual metric (crash-free session rate, ANR rate, a specific error budget) and the actual threshold — "we'll keep an eye on it" is not a threshold. Note the platform mechanics matter here: iOS phased release runs a fixed 1% → 2% → 5% → 10% → 20% → 50% → 100% schedule over 7 days that you can pause but not reshape; Google Play lets you pick both the percentage and the pace yourself. A plan that assumes iOS-style fine control on iOS, or that never revisits Android's rollout percentage because "it's already increasing," is a finding.

**2. When the rollout is halted, does everyone understand what that does and doesn't do?**
Halting stops the percentage from climbing. It does not un-install the build from users who already have it, and it does not get a fix to them. The actual remedy for a bad build already in the field is always "ship a new build," which goes back through review — see check 3. If the incident plan says "pause the rollout" and stops there, that's an incomplete plan, not a mitigation.

**3. Is anything genuinely time-critical routed around the review queue?**
Feature flags, remote config, and server-side kill switches that the *already-shipped* build can read are the only way to change behavior faster than a review cycle allows. Check that the specific things likely to need a fast off-switch (a new risky feature, a payment flow, anything that could corrupt data if it misbehaves) are wired to one of these before launch — not added after the incident that proves they needed one.

**4. Is the forced-update trigger reserved for cases that actually justify blocking the user?**
A forced (blocking, can't-dismiss) upgrade should be rare: a security vulnerability, active data corruption, a legal/compliance requirement, or a backend contract break with no compatibility path left. Everything else — a nicer UI, a feature the team wants adopted, "engagement" — is a soft, dismissible nudge, not a gate. If the version-check logic can't answer "what specifically breaks if this user stays on the old version," that's the finding, not the severity level chosen. Also check the failure-open case: what happens when the version-check call itself fails (no network, backend down) — a hard gate that can't be bypassed should not turn a network hiccup into every user being locked out.

**5. Does the backend actually tolerate the client versions that are really still out there?**
Ask what the oldest client version still in meaningful use is — not what the team hopes it is. A backend change that assumes the old client is gone because "the force-update went out three weeks ago" needs the real adoption curve, not the release date, because check 4 already established that forcing isn't always possible or appropriate. If a contract change breaks an old client that can't be forced off it, that's `skew-check`'s compatibility-direction reasoning applied to a tail measured in months, not minutes.

## Report

```
## Release: v4.2.0 — payment retry logic
1. Rollout threshold: FAIL — Android staged rollout is live at 20% with no
   documented halt metric; team is "watching Crashlytics" with no threshold.
2. Halt semantics: CAUTION — incident doc says "pause rollout" as the fix for
   a bad build; doesn't mention the ~14% of users already on it need a new
   build, not a pause.
3. Time-critical path: FAIL — the new retry logic has no feature flag; a bug
   in it can only be disabled by shipping a new build through review.
4. Forced-update trigger: SAFE — this release uses a soft nudge, correctly;
   nothing in the diff breaks old clients.
5. Backend tail: CAUTION — API still accepts the v3.x retry-count field, but
   nobody could say how many users are still on v3.x — get the real number
   before assuming it's safe to drop next release.
```

One line per check, including the SAFE ones — the point is showing every angle was actually considered, not just listing what's wrong.

## Boundaries

- Doesn't replace `skew-check`: a mobile release that also has a backend API change goes through both — this skill covers the client-binary distribution and review-queue mechanics, `skew-check` covers the wire-format compatibility once you've established which client versions are still out there.
- Doesn't replace `ship-it`: this isn't a test/lint/typecheck checklist, and it doesn't apply to backend or web deploys that don't go through app-store review at all.
- Not an App Store/Play Store review-guideline compliance check (privacy manifests, entitlements, metadata rejections) — that's a distinct pre-submission problem several dedicated tools already cover; this skill is about release/rollback *strategy*, not passing review.
- Can't see the team's actual App Store Connect or Play Console dashboards — ask for the real current rollout percentage, the real crash-free rate, and the real client-version distribution rather than assuming; if nobody has those numbers on hand, that absence is itself the finding.
