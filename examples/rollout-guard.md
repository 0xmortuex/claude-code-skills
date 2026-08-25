# rollout-guard — example

**Trigger:**

> we found a bug in v5.1.0 — on iOS 14 devices it corrupts the locally
> cached transaction history after a background sync. it's live on Apple's
> phased release at 20% right now. v5.1.1 has the fix and is in review.
> plan is: pause the phased rollout on v5.1.0, and the second v5.1.1 clears
> review, force every device onto it. does that plan hold up?

**Response shape:**

Claude works the five checks in order against the actual plan described,
not a generic release checklist:

```
1. Rollout threshold
   No metric or number given for "pause the phased rollout" — it's
   triggered by this specific bug report, not a monitored threshold that
   would have caught it independently. Also: iOS phased release is Apple's
   fixed 1/2/5/10/20/50/100% schedule over 7 days, pauseable but not
   reshapeable — confirm the team knows pausing at 20% doesn't roll the
   percentage back down, it just stops it climbing further.
   CAUTION: no standing crash-free/ANR threshold exists for future releases;
   this pause is manual and reactive, not a trigger that would fire on its
   own next time.
```

```
2. Halt semantics
   Plan explicitly separates "pause v5.1.0" from "force v5.1.1 once
   approved" — correctly treats the pause as blast-radius containment, not
   a fix. The ~20% already on v5.1.0 still have corrupted local caches
   after the pause; nothing in the plan clears or repairs that state on
   those devices once v5.1.1 lands.
   SAFE on the halt/fix distinction, FAIL on a gap: the plan has no repair
   step for the cache damage already done to the 20% — a forced update
   stops new corruption, it doesn't undo the old rows.
```

```
3. Time-critical path
   The corrupting code path (background sync writing to the local cache)
   has no feature flag or server-side switch — the only way to stop it
   right now is the App Store review clock for v5.1.1, which is out of the
   team's control.
   FAIL: nothing about this release wires the sync path to a kill switch,
   so "we'll ship a fix" is the whole mitigation, with an unbounded
   Apple-controlled delay baked in and undocumented.
```

```
4. Forced-update trigger
   Active data corruption on-device is exactly the class of bug a forced
   (blocking) upgrade exists for — not a UI nudge or an engagement play.
   Check the failure-open case: if the force-update version check itself
   fails (offline device, backend down), does the gate fail open (user
   proceeds on the old, corrupting build) or fail closed (user is locked
   out entirely by a network hiccup)? Not specified in the plan — ask
   before shipping the gate, not after the first support ticket about it.
   SAFE on choosing to force here; CAUTION until the failure-open behavior
   is confirmed.
```

```
5. Backend tail
   Ask what fraction of the install base is actually reachable by a forced
   update — some iOS 14 devices may be on hardware that can't take a newer
   OS the next app version might require, meaning "force everyone to
   v5.1.1" is optimistic for a slice of exactly the affected population.
   CAUTION: get the real current OS/version distribution for iOS 14 users
   before assuming the force reaches all of them; a device that can't
   update needs a different remediation (server-side data repair, or
   disabling the affected feature for that OS floor).
```

One line per check, SAFE ones included — the corruption bug makes checks
2–5 land mostly CAUTION/FAIL, which is the honest read: forcing the update
is the right call, but the plan as described has no repair step for
already-corrupted devices, no kill switch that would have avoided needing
the force in the first place, and an unconfirmed failure-open behavior on
the version gate.
