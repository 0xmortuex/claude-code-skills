# reaccept-guard — example

**Trigger:**

> we're bumping our ToS to v4 next week and requiring everyone to re-accept
> before they can keep using the app. legal signed off on the web flow —
> here's the relevant code. can you check this actually holds everywhere,
> not just the web app?
>
> ```python
> # web/middleware.py
> class ReacceptMiddleware:
>     def __call__(self, request):
>         if request.path.startswith("/app/"):
>             if request.user.accepted_tos_version < CURRENT_TOS_VERSION:
>                 return redirect("/accept-terms")
>         return self.get_response(request)
>
> # api/auth.py
> def authenticate_api_key(key):
>     client = ApiClient.objects.get(key=key)
>     if not client.is_active:
>         raise AuthError("inactive")
>     return client
> ```

**Response shape:**

Claude starts from where the check is enforced, not from the web flow legal
already approved:

```
Step 1: where is the check actually enforced?
ReacceptMiddleware only runs for request.path.startswith("/app/") — that's
the web app's own route prefix. It checks request.user.accepted_tos_version
against CURRENT_TOS_VERSION and redirects. This is route-scoped middleware,
not global request handling: any path outside /app/ never passes through
it, including the entire /api/ surface.
```

Step 2 walks each surface the backend actually serves, not just the one
legal reviewed:

```
Step 2: surface by surface
- Older mobile builds: the app calls the same backend under /app/ routes
  (confirmed against the API docs provided) — so an old build showing no
  local modal still gets redirected server-side on its next request. This
  surface is covered, despite no client-side check existing on old builds,
  because enforcement doesn't depend on the client.
- Direct API integrations: authenticate_api_key never checks
  accepted_tos_version at all — ApiClient has no such field even referenced
  here. Every API-key request goes through a code path the middleware never
  touches. A customer calling /api/ endpoints directly keeps working
  indefinitely after the v4 bump, with no record of ever being asked.
- Webhooks / service accounts: not shown in the provided code, and no
  mention of whether ApiClient rows are tied to an account owner who
  re-accepts on their behalf. Flagged as unverified rather than assumed.
- Long-lived tokens: moot for the web path since the check runs per-request
  against current DB state, not at session issuance — but moot only for the
  surface that's actually gated. The API-key path has no per-request check
  to be moot about.
```

Step 3 grounds the severity instead of treating this as a hypothetical:

```
Step 3: what the gap permits
This isn't an edge case — it's the entire API client population, for as
long as any of them keep calling in, with no mechanism that will ever force
them to stop. Legal's sign-off covered the surface that was built and
tested; the one that was neither is the one with no enforcement at all.
```

Report leads with the live gap, not the one that already works:

```
## reaccept-guard audit: ToS v4 re-acceptance enforcement

1. Web app (/app/ routes): PASS — ReacceptMiddleware checks
   accepted_tos_version per request against live DB state, server-side.
   Confirmed this also covers older mobile builds hitting the same routes.
2. Direct API integrations (/api/ routes): FAIL — authenticate_api_key has
   no policy-version check at all; ReacceptMiddleware's path filter never
   reaches this prefix. Every API-key holder keeps authenticating past the
   v4 cutover with no gate, indefinitely.
3. Webhooks / service accounts: NEEDS VERIFICATION — no evidence in the
   provided code of whether these are a deliberate exemption or simply
   unhandled. Surface to a human: has anyone actually decided how these
   accept v4, or did nobody write that code path?

## Verdict: BLOCK
The web flow legal reviewed is solid — server-side, per-request, covers old
mobile builds for free. But "requiring everyone to re-accept" is false as
stated: the entire direct-API population is unaffected by the v4 bump.
Add the same accepted_tos_version check to authenticate_api_key (or a
documented, deliberate exemption with an expiry) before calling this
rollout complete, and get an explicit answer on service accounts rather
than leaving it to default to "nobody checked."
```
