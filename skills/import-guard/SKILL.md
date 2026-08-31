---
name: import-guard
description: Review a user-facing bulk import feature (CSV/XLSX/JSON upload, "import contacts", "bulk create from a spreadsheet") for the three failure modes that make bulk import untrustworthy — a single bad row aborting or corrupting the whole batch, the response lying about what actually landed (silently skipped rows counted as success), and re-uploading the same file creating duplicates instead of upserting cleanly. Distinct from `backfill-pilot` (an engineer's internal ops script against a live prod table) and `job-warden` (queue/cron idempotency) — this is a customer-facing upload endpoint ingesting untrusted, messy user files. Use when adding or reviewing a bulk/CSV/spreadsheet import feature, when asked "does this import handle bad rows right", "what happens if the upload fails halfway", or "will re-uploading duplicate everything".
---

# import-guard

A bulk import feature earns trust or loses it on the file that isn't clean — the one with a stray blank row, a date in the wrong format on row 847, or a duplicate email three rows apart. The happy-path file with 500 perfect rows tells you nothing; every import feature handles that one. What breaks in production is the file that's 95% good, because that's the one real users actually upload. Two documented, well-known failure shapes recur here: a "success" result that's actually a silent partial failure (Salesforce's Bulk API treats partial success as the *normal* case — a job can report done while individual records failed, and a caller that only checks job status instead of separately fetching the failed-records list ships that gap straight through), and row-count corruption from something as mundane as a CRLF/LF mismatch shifting every row's field alignment by one, which is exactly what happened in a real reported NetBox bug where the first field of every row got silently dropped. Neither failure looks like a crash. Both look like success, which is what makes them worth a dedicated review rather than trusting "it didn't error."

## Step 1: find the failure unit — what does one bad row take down with it

Locate where the import loop actually writes: one row at a time, in fixed-size chunks, or as a single all-or-nothing transaction around the whole file. Then find out what a single malformed or constraint-violating row does at that boundary:

- **Whole-file transaction**: one bad row anywhere in a 10,000-row file rolls back all 10,000 good ones. This is the most defensible failure mode to *report* (nothing landed, nothing lied) but the worst for the user, who now has no idea which one row to fix without re-diffing the whole file.
- **Chunked/batched commits with no per-chunk isolation**: a bad row inside a chunk can take out the whole chunk with it (this is real, documented Salesforce Bulk API behavior — a `FIELD_CUSTOM_VALIDATION_EXCEPTION` can roll back the entire chunk it's in, not just the offending record), silently punishing rows that were individually fine.
- **Per-row commits**: the common choice, and the one where step 2 matters most, because now "partial success" is the normal outcome and the question shifts entirely to whether that partial state is reported honestly.

Also check what happens to a row's *side effects* when the row itself half-succeeds — a contact row that wrote to the database but whose "send welcome email" or "sync to CRM" follow-up call failed. If the import only tracks the DB write as the row's success/fail state, a user can be told their import succeeded while a dependent action silently never happened.

## Step 2: read what's actually reported back, not what the code intends to report

Find the literal response shape returned to the caller (API response, UI success banner, summary email) and compare it against what the code can actually detect:

- A boolean `success: true` or an HTTP 200 tells you the job ran, not that every row landed — check whether the code is conflating "the import process completed" with "every row was imported," which is the exact gap that makes a Salesforce-style partial success invisible to a naive integration.
- Aggregate counts ("482 of 500 imported") are honest about *that* something failed but useless for fixing it without per-row detail — the user still can't find which 18 rows or why.
- Check specifically for rows dropped without ever being counted as attempted at all: blank/whitespace-only rows silently inserted as empty records instead of erroring, and encoding or line-ending mismatches (mixed CRLF/LF) that shift the parser's row alignment so an error reported against "row 847" doesn't correspond to line 847 in the file the user actually has open — the NetBox case above is this exact bug, not a hypothetical.
- If failures are written to a downloadable error/log file rather than surfaced inline, confirm that file is actually generated and linked on every partial-failure path, not just the ones the original author tested.

## Step 3: check for a dry-run or validate-only path

For anything beyond a trivial file size, the first real import shouldn't be where formatting problems are discovered. Look for a validation pass that parses and checks every row (types, required fields, referential lookups like "does this category ID exist") without writing, and surfaces the same per-row errors step 2 requires — before any row is committed. Its absence isn't automatically a blocking finding (a small, low-stakes import may not need one), but for anything large, recurring, or hard to undo, flag it as a real gap: the user's only way to find out row 847 is malformed is to run the actual import and see what broke.

## Step 4: check what happens when the same file comes back

Users re-upload. It happens after a partial failure (fixing a subset of rows and re-submitting the *whole* file, not just the fixed ones), after a UI timeout that leaves them unsure whether the first attempt landed, or just by mistake. Trace what the write path does on a second pass over rows it already imported:

- **Plain `INSERT` per row with no natural-key check**: every re-upload duplicates every row that succeeded the first time. This is the most common and most damaging finding this skill catches.
- **Upsert keyed on a natural field** (email, external ID, a composite key) is safe *if* that key is actually unique and stable — check it isn't something like row position or an autogenerated timestamp that changes between uploads.
- **A file-level idempotency key** (checksum of the upload, or a client-supplied import ID) that skips a whole file already processed is a valid alternative to per-row upsert, but only if it's actually enforced server-side and not just a UI-level "are you sure" prompt a re-upload trivially bypasses.

## Report

Lead with whichever of these is true, since it's the actual trust-breaking bug: (a) a partial failure gets reported as success or near-success without per-row detail, or (b) re-uploading duplicates already-imported rows. Both are BLOCK-level — they mean the feature actively misleads the user about their own data. Report the failure-unit shape from step 1 and the dry-run gap from step 3 as CAUTION findings; they're real UX and safety gaps but don't misrepresent an outcome that already happened. Cite the specific line where success is determined and the specific line (or absence of one) where the retry/upsert key is enforced — this skill's findings should point at exact code, not general advice.

## Boundaries

- Not `backfill-pilot` — that skill is for an engineer's own script fixing rows already in a live production table, run once under their control. This skill is for a *product feature* that ingests arbitrary files from real users on an ongoing basis. If the "import" in question is a one-off ops task with no UI, use `backfill-pilot` instead.
- Not `job-warden` — that skill audits whether an async job/queue consumer is idempotent and handles overlap and poison messages. If the bulk import is itself implemented as a queued job, both skills apply: `job-warden` for the job-runner correctness, this skill for the file-parsing/reporting/duplicate-on-reupload correctness.
- Doesn't judge business-logic validation rules (what makes a row "valid" is the app's call) — only whether failures in that validation are handled, reported honestly, and safe to retry.
- Can't verify a third-party bulk API's actual server-side behavior beyond what's documented (Salesforce, HubSpot, Stripe, etc.) — when the code assumes a shape for a vendor response, check that assumption against the vendor's own documented partial-success/failure semantics rather than trusting inline comments, and say so if the docs couldn't be confirmed.
- Doesn't cover malicious file content (formula injection, zip bombs, decompression attacks) — that's `security-sweep`'s territory for a file-upload attack surface, not this skill's correctness-of-partial-failure focus.
