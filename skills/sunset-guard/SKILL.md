---
name: sunset-guard
description: Review whether a public/external-facing API version, endpoint, or field that's being deprecated or sunset actually gives real callers the notice and behavior a shutdown requires — Sunset/Deprecation headers wired into every serving path (not just the primary route), a notice window that matches what was promised, removal gated on measured caller usage rather than a calendar date alone, and a clear signal (not a silent 500/timeout) for clients still calling after the cutover. Distinct from `skew-check` (internal rolling-deploy skew between your own services) and `tombstone` (evidence that unused internal surface is safe to delete) — this is for a versioned/external contract that real third-party integrations still call. Use when adding a Sunset or Deprecation header, retiring an API version or field, planning to turn off an old endpoint, or asked "is our deprecation notice enough", "can we remove this API version yet", or "what happens to clients still calling the old endpoint".
---

# sunset-guard

A deprecation notice that only lives in a changelog or an email blast isn't a deprecation — it's a hope. The pattern that actually breaks in production isn't "we forgot to announce it," it's "we announced it correctly and shut it off anyway while callers were still depending on it," because the announcement and the enforcement are two different pieces of code that drift apart. PayPal's TLS 1.0/1.1 retirement is the textbook case: PayPal published the June 30, 2018 cutover well in advance, but a real portion of merchant integrations still hadn't updated by the deadline, and when the old protocol was actually turned off, their payment processing broke outright rather than degrading visibly or giving a last-mile warning tied to their own account's continued use of the old path. The notice existed; what was missing was anything checking, at the moment of cutover, whether the specific caller in front of you had actually acted on it. That's the gap this skill audits: not whether a deprecation was announced, but whether the code enforces the promise the announcement made.

Two IETF mechanisms exist for exactly this and are worth knowing so you can check them by name rather than judging ad hoc: RFC 8594's `Sunset` response header states the date a resource will stop responding, and the (separately drafted) `Deprecation` header signals that a resource is discouraged from use starting now, independent of when it disappears. A codebase that's actually doing this right emits both, consistently, everywhere the deprecated surface is reachable — not just on the one route someone remembered to update.

## Step 1: find every path that serves the thing being sunset — not just the one that was updated

Search for every route, SDK method, GraphQL field, and documented alias that reaches the deprecated version or endpoint, then check which of them actually carry the `Sunset`/`Deprecation` headers (or an equivalent in-body warning field for non-HTTP protocols) and which don't. The common gap: someone adds the header to the main documented route and never checks the internal alias, the mobile-only route, the bulk/batch variant, or the webhook callback shape that quietly shares the same deprecated version. A caller hitting an unheadered alias gets zero warning right up until the day it's gone.

## Step 2: check that the notice window the code enforces matches the notice window that was promised

Find where the `Sunset` date (or removal date, however it's tracked) is set and compare it against when the `Deprecation` signal first went live — or, if there's no header at all, against whatever the team's stated policy or public changelog says the notice period should be. A hardcoded date with no visible connection to when deprecation actually started is a red flag: it means the removal date was picked by calendar convenience, not by counting forward from when callers were actually told. If the code was updated to extend or shorten the date after the fact, check whether that's reflected everywhere the date is read from (a cached config, a separate docs site, a client SDK's own hardcoded expectation) — a date bumped in one place and stale in another is worse than no header, because it actively lies to a caller checking it.

## Step 3: check whether removal is gated on measured usage, or just on the calendar

A sunset date passing is not the same as the endpoint being safe to remove — it's a good default trigger, but the actual gate should be caller traffic dropping to (near) zero, or the remaining callers being ones the removal has already accounted for. Look for whether the removal step reads real traffic/usage metrics for the specific version or endpoint before the code path is deleted or the 410 is turned on, versus removal being driven purely by "the date arrived." If there's no usage check at all, that's a real gap worth flagging — not necessarily a blocker (some teams accept the risk deliberately for external-contract clarity: the date was the contract), but say so plainly rather than assuming traffic was checked. This is the same evidence-over-assumption discipline `tombstone` applies to unused internal surface, extended to a case where "unused" has to be proven against traffic from callers you don't control and can't grep.

## Step 4: check what a still-calling client actually experiences after cutover

Trace what happens to a request that hits the sunset endpoint after the removal date. The failure modes, worst to best:
- **Silent wrong behavior**: the route still exists but now does something different (redirected to a new version with an incompatible response shape, or serves stale/cached data) — the caller gets a 200 and has no idea anything changed.
- **Generic 500/timeout**: the caller sees a server error indistinguishable from an outage, with nothing telling them the endpoint is gone on purpose or where to go next.
- **404**: better — at least it's not ambiguous with a transient failure — but doesn't distinguish "never existed" from "used to work, here's why it stopped."
- **410 Gone with a `Link` header (or equivalent body field) pointing at the migration path**: the correct terminal state — unambiguous, and actionable for whoever's still integrated.

Also check that the 410 (or whatever the terminal response is) is reachable from every path found in step 1, not just the one that was actively tested — an alias route quietly falling through to a generic error handler after the primary route was properly sunset is a common way this half-finishes.

## Report

Lead with whichever of these is worst: a caller-visible silent behavior change (step 4's first case) is the most dangerous because it looks like success while corrupting data or decisions downstream, followed by an unheadered serving path (step 1) that got no warning at all, followed by a mismatched notice window (step 2). A calendar-only removal with no usage check (step 3) is a CAUTION unless the team has explicitly decided the date itself is the contract. Cite the specific route/file for every path checked in step 1 — a finding that says "the deprecation isn't consistent" without naming which paths are missing it isn't actionable.

## Boundaries

- Not `skew-check` — that skill reviews whether your *own* services can tolerate old and new code coexisting during your *own* rolling deploy. This skill is about a versioned contract that external, uncoordinated third parties depend on, where you can't just wait for a canary to finish; the notice period itself is the coordination mechanism.
- Not `tombstone` — that skill gathers evidence that internal, unreachable-from-outside surface is actually dead before deleting it. This skill assumes the surface *is* reachable by real external callers and reviews whether the shutdown process respects them; use `tombstone`'s evidence-gathering discipline (step 3 above) but expect the audience to be uncontrolled, not something you can fully instrument.
- Doesn't decide *whether* something should be deprecated — that's a product/API-design call. It only reviews whether a deprecation already decided on is executed honestly and completely.
- Doesn't verify legal or contractual notice-period obligations (an SLA or partner agreement may require a longer window than the code's own policy assumes) — if the codebase's stated policy doesn't obviously reconcile with a contractual minimum, say so as a question for the team rather than guessing at compliance.
- Can't observe real external caller traffic directly — it can only check whether the code *reads* a usage/traffic signal before gating removal, not fabricate what that signal would show. If no usage data is available at all, say that plainly instead of assuming traffic is negligible.
