# consent-guard — example

**Trigger:**

> legal asked us to confirm the cookie banner actually blocks tracking before
> it clicks "accept" — can you check? we use GTM for most things plus a
> separate Meta Pixel and Hotjar snippet marketing added. here's the relevant
> code:
>
> ```html
> <!-- public/index.html -->
> <head>
>   <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABCD123"></script>
>   <script>
>     window.dataLayer = window.dataLayer || [];
>     function gtag(){dataLayer.push(arguments);}
>     gtag('consent', 'default', { ad_storage: 'denied', analytics_storage: 'denied' });
>   </script>
>   <!-- added by marketing last quarter, not through the analytics team -->
>   <script src="https://static.hotjar.com/c/hotjar-998877.js"></script>
> </head>
> ```
>
> ```js
> // src/consent.js
> export function hasConsent() {
>   try {
>     return JSON.parse(localStorage.getItem('cmpConsent')).analytics === true;
>   } catch {
>     return true; // don't block tracking if we can't read the cookie yet
>   }
> }
>
> // src/analytics.js
> import { hasConsent } from './consent';
> export function trackEvent(name, props) {
>   if (!hasConsent()) return;
>   gtag('event', name, props);
> }
>
> // src/components/FacebookPixel.jsx
> import { useEffect } from 'react';
> export function FacebookPixel() {
>   useEffect(() => {
>     fbq('init', '1234567890');
>     fbq('track', 'PageView');
>   }, []); // runs on every mount, no consent check
>   return null;
> }
>
> // src/App.jsx
> function App() {
>   const location = useLocation();
>   useEffect(() => {
>     trackEvent('page_view', { path: location.pathname }); // gated correctly
>   }, [location]);
>   return <><FacebookPixel /><Router /></>;
> }
> ```

**Response shape:**

Step 1 enumerates every tracking initiation point rather than starting from
the banner's own list of "configured tags," which is exactly what misses the
Hotjar snippet:

```
Step 1: tracking initiation points

- GTM container (gtm.js) — loader for however many tags are configured
  inside it; can't audit tag-level triggers from this repo, but the
  container script's own load is a code-level initiation point.
- Meta Pixel via FacebookPixel.jsx — fbq('init', ...) is the SDK bootstrap
  (fires its own automatic PageView beacon on init), fbq('track', 'PageView')
  is a second, explicit call.
- Hotjar snippet (static.hotjar.com/c/hotjar-998877.js) — unconditional
  <script src> in <head>, added by marketing outside the analytics team's
  code review. A session-replay SDK, not caught by grepping for "pixel" or
  "gtag".
- App-level custom events via analytics.js::trackEvent — the only mechanism
  that already routes through hasConsent().
```

Step 2 (invariant A) checks each against the consent check's actual location,
not whether a check exists somewhere in the codebase:

```
Step 2: invariant A — ordering and coverage at the actual load site

- GTM: gtag('consent', 'default', ...) is declared AFTER the
  <script src="...gtm.js"> tag in index.html. Google's own Consent Mode
  documentation requires the default call to run before gtm.js loads —
  as written, GTM briefly initializes under an implicit "granted" state for
  however long it takes the second <script> block to execute and the
  default call to register. FAIL — wrong order, not just "both calls exist."

- Meta Pixel: fbq('init', ...) and the automatic PageView beacon it fires
  run unconditionally in a useEffect with an empty dependency array — no
  hasConsent() check anywhere in FacebookPixel.jsx. The one place consent IS
  checked (analytics.js::trackEvent) only gates the app's own custom events,
  never this component. FAIL — the SDK bootstrap and its automatic beacon
  are completely ungated; only calls the app happens to make later would be.

- Hotjar: static <script src> in <head>, no consent check surrounds it at
  all — it's not wired into consent.js or analytics.js in any way. Loads
  and starts recording sessions on every page view regardless of banner
  state. FAIL — not partially gated, not gated.

- App-level trackEvent(): correctly checks hasConsent() before calling
  gtag('event', ...). This is the one mechanism working as intended, and
  it's also the smallest share of what's actually collecting data — GTM,
  Meta, and Hotjar are all upstream of it.

- SPA re-init: App.jsx's page-view effect re-runs trackEvent on every route
  change and re-checks hasConsent() each time, so a user who withdraws
  consent mid-session does stop generating new *custom* events. But
  FacebookPixel's effect has an empty dependency array — it never re-runs on
  navigation, so there's no repeated leak from it, though it also never gets
  a chance to start respecting consent if the visitor accepts later without
  a full page reload.
```

Step 3 (invariant B) checks the one place a consent check exists for what it
does when it can't determine an answer cleanly:

```
Step 3: invariant B — fail-open or fail-closed

hasConsent() in consent.js catches any JSON.parse failure — including the
normal case where localStorage.getItem('cmpConsent') returns null because
the banner hasn't been interacted with yet, or the CMP script itself hasn't
finished writing the cookie — and returns true. That's fail-open by
construction: the one gate the app has defaults to "tracking allowed" in
exactly the window right after page load when a real answer isn't known yet,
which is also the highest-traffic moment (first pageview, before any click).
FAIL — flagged regardless of how short that window usually is, per the
skill's rule that a fail-open default counts independent of rarity.

No expiry check found: consent.js never reads or checks a timestamp on the
stored record, so a consent decision made under an old set of tracking
categories (before Hotjar was added, per the trigger's own "added last
quarter" note) is treated as still covering categories that didn't exist
when it was given.
```

Report matches the skill's step 4 format — per mechanism, worst-first:

```
## consent-guard audit: tracking vs. consent banner

1. GTM Consent Mode ordering (BLOCK): gtag('consent', 'default', ...) is
   declared after the gtm.js <script> tag, not before. Per Google's own
   documentation this means GTM briefly runs with an implicit "granted"
   state on every page load. Move the dataLayer/gtag/consent-default block
   into its own <script> ABOVE the gtm.js tag.

2. Meta Pixel bootstrap is completely ungated (BLOCK): fbq('init', ...) and
   its automatic PageView beacon fire unconditionally in
   FacebookPixel.jsx's mount effect. The app's only consent check
   (analytics.js::trackEvent) never touches this component. Wrap the
   fbq('init', ...) call itself behind hasConsent() — not just later
   fbq('track', ...) calls the app might add — and re-run it if consent is
   granted after initial mount.

3. Hotjar snippet has no consent gating at all (BLOCK): a session-replay
   SDK loads and records unconditionally from a static <script> tag added
   outside the analytics team's review. This is arguably the most sensitive
   of the three trackers (full session capture, not just pageview beacons)
   and has zero consent coverage. Route it through the same dynamic-
   injection pattern the other two need, or remove it from the static HTML
   entirely until it is.

4. hasConsent() fails open (BLOCK): a missing or unparseable consent
   record returns true, meaning the one working gate in this codebase
   defaults to "track" during the exact window — first load, before any
   banner interaction — when the visitor hasn't answered yet. Change the
   catch/null path to return false.

5. No consent expiry check (CAUTION): consent.js doesn't check a stored
   timestamp against the CMP's documented expiry policy, so an old
   "granted" record from before Hotjar existed is being treated as if it
   covers a tracking category the visitor was never asked about.

## Verdict: BLOCK
Three of four tracking mechanisms found in this codebase (GTM, Meta Pixel,
Hotjar) fire ahead of or independent of real consent state, and the one
consent check that does exist (hasConsent()) fails toward "track anyway" in
its most common failure case. The banner is not cosmetic by intent, but in
practice only the smallest share of what's collecting data — the app's own
custom trackEvent() calls — actually respects it. Fix findings 1–4 before
telling legal this is enforced; finding 3 in particular (an unreviewed,
fully ungated session-replay SDK) is the kind of gap a marketing-side GTM
export wouldn't surface at all, since it isn't a GTM tag.
```
