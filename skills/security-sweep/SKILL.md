---
name: security-sweep
description: Review the working changes (or a named set of files) for real, exploitable security problems — injection, authz gaps, secret leaks, unsafe deserialization, SSRF, path traversal, and the like — and report only findings you can justify with a concrete attack path. Use this whenever the user asks for a security review, a "security check", wants to know if a change is safe to ship, is touching auth/crypto/file-uploads/user-input/database queries, or says things like "any vulnerabilities here", "is this exploitable", "audit this endpoint". Also use before shipping code that handles untrusted input or secrets.
---

# security-sweep

Security review is valuable only when it's grounded and honest. A list of theoretical "consider using HTTPS" notes trains people to ignore security review; a single well-explained "this endpoint lets any user read any other user's invoices, here's the request" prevents a breach. Aim for the second kind. Report what's actually exploitable, prove it, and stay quiet about noise.

## Scope: review the change, not the universe

Default to the working diff (`git diff`, and staged changes) or the files the user names. You're evaluating *this change*, not auditing the whole codebase — that keeps the review focused and the findings relevant. If you notice a severe issue in adjacent code while reading, mention it separately, but don't turn a diff review into an open-ended audit unless asked.

## What to actually look for

Walk the real risk categories, tracing untrusted input to where it does damage:

- **Injection** — SQL/NoSQL built by string concatenation, shell commands from user input, `eval`/template injection. Trace: does attacker-controlled data reach an interpreter without parameterization/escaping?
- **Broken authorization** — the big one, and the most missed. Does the code check that the *current user* is allowed to touch *this specific resource*, or only that they're logged in? Object-level access control (IDOR) is where real breaches live.
- **Authentication & session** — missing checks, weak token handling, auth decisions on client-supplied values.
- **Secrets** — hardcoded keys, tokens, passwords, connection strings; secrets logged or returned in responses; a real `.env` committed.
- **Unsafe deserialization / dynamic loading** — `pickle`, `yaml.load`, `Marshal`, unsanitized reflection on untrusted data.
- **SSRF & path traversal** — user input flowing into URLs the server fetches, or into file paths without normalization/allowlisting.
- **Crypto misuse** — home-rolled crypto, ECB, static IVs, `Math.random` for tokens, missing signature verification.
- **Sensitive-data exposure** — over-broad API responses, PII in logs, stack traces to users.
- **Injection into the browser** — reflected/stored XSS where output isn't encoded for its context.

Match the categories to what the code does — file-upload code gets path-traversal and content-type scrutiny; an API endpoint gets authz and injection scrutiny. Don't run a generic checklist blind.

## The bar for reporting: a concrete failure path

Only report a finding if you can state **how it's exploited and what it costs** — specific inputs or a request, leading to a specific bad outcome. If you can't construct that path, you're guessing, and a guess dressed as a finding wastes the reader's trust. When you're unsure, say "possible, unverified" and explain what you'd need to confirm it, rather than asserting it's a vulnerability.

This is deliberately strict because the failure mode of security tools is crying wolf. A short list of real problems is worth far more than a long list of maybes.

## Report format

Order findings by severity (most severe first). For each:

```
### [SEVERITY] Short title
**File:** path:line
**What:** the flaw, in one sentence.
**Attack path:** concrete inputs/request → what an attacker achieves. This is
the part that proves it's real.
**Fix:** the specific change — parameterize this query / add an ownership check
here / move this key to an env var. Show the corrected code when it's short.
```

Severity: **Critical** (unauth remote impact, secret leak, auth bypass) · **High** (authenticated but serious, e.g. IDOR) · **Medium** (needs unusual conditions) · **Low** (defense-in-depth). Be calibrated — inflating severity is its own kind of noise.

End with a one-line verdict: is this change safe to ship, safe with the listed fixes, or not yet. If you found nothing exploitable, say that plainly — "no exploitable issues found in this diff" is a real, useful result, not a failure to find something.

## Boundaries

This is defensive review of code the user is authorized to work on. Explain flaws and their fixes clearly — including realistic attack paths, because a fix you can't justify won't get made. Don't produce weaponized exploits, and if the request shifts from "help me secure this" to "help me attack something I don't own," stop and say so.
