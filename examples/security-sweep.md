# security-sweep — example

**Trigger:**

> pushing this today — added a `GET /api/invoices/:id` endpoint and a
> `POST /api/invoices/:id/export` that renders it to a PDF via a URL passed
> in `?logoUrl=` for letterhead branding. any vulnerabilities here before I
> ship it?

**Response shape:**

Claude scopes to the diff, not the whole codebase, then walks the two
handlers against the risk categories that actually match what this code
does — an ID in the path gets authz scrutiny, a URL parameter feeding a
fetch gets SSRF scrutiny — instead of running a generic checklist blind.

It finds the authz gap first, and proves it with a concrete request rather
than asserting "add auth here":

```
### [High] Broken object-level authorization on invoice fetch
**File:** routes/invoices.js:14
**What:** GET /api/invoices/:id checks that the requester is logged in
(`requireAuth` middleware) but never checks that the invoice belongs to
them — it loads `Invoice.findById(req.params.id)` and returns it straight.
**Attack path:** any authenticated user can read any other customer's
invoice by incrementing the id — `GET /api/invoices/1042` while logged in
as customer 88 returns customer 40's invoice (line items, billing address,
amount). No special tooling needed, just a logged-in session and sequential
IDs.
**Fix:** scope the query to the current user: `Invoice.findOne({ _id:
req.params.id, customerId: req.user.id })`, and return 404 (not 403) on a
mismatch so existence of other customers' invoice IDs isn't leaked either.
```

Then the SSRF path in the export endpoint — traced from the same
attacker-controlled parameter to where it actually fetches:

```
### [Critical] SSRF via unvalidated logoUrl in PDF export
**File:** routes/invoices.js:41
**What:** POST /api/invoices/:id/export passes `req.query.logoUrl` straight
into the PDF renderer's `fetch(logoUrl)` call with no scheme, host, or
network-range check.
**Attack path:** `POST /api/invoices/1042/export?logoUrl=http://169.254.169.254/latest/meta-data/iam/security-credentials/`
makes the server fetch the cloud metadata endpoint and embed the response
in the rendered PDF, which is then handed back to the requester —
exfiltrating the instance's IAM credentials to any authenticated user.
Internal services on the VPC (`http://10.0.x.x:PORT/...`) are reachable the
same way.
**Fix:** don't let this be an arbitrary fetch. Allowlist to a fixed set of
company-hosted logo URLs, or if user-supplied logos are a real requirement,
resolve the hostname and reject private/link-local ranges (RFC 1918,
169.254.0.0/16, ::1) before fetching, and disable redirects on the fetch
so an allowlisted host can't 302 to an internal one.
```

It checks the invoice-fetch code for injection too, but doesn't invent a
finding just to pad the list — the ORM call is parameterized, so it says so
and moves on rather than manufacturing a "low" severity filler item.

Final report, ordered by severity with a plain verdict:

```
Findings, most severe first:
1. [Critical] SSRF via unvalidated logoUrl — routes/invoices.js:41
2. [High] Broken object-level authorization on GET /invoices/:id — routes/invoices.js:14

No injection issues found — the invoice lookup uses the ORM's parameterized
query builder throughout.

Verdict: not safe to ship as-is. Both findings are reachable by any
authenticated user with no special access, and the SSRF finding can leak
instance credentials — fix both before this goes out today.
```
