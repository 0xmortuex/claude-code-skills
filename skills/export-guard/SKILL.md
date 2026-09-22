---
name: export-guard
description: Review a bulk data export or report-generation feature (CSV/XLSX/PDF download, "export all", "download report") for two failure modes that look like success — a row-count cap, pagination limit, or request timeout that silently truncates the file while the response still reports it as complete, and identifier columns (IDs, ZIP codes, phone numbers, order numbers) silently corrupted the moment a spreadsheet tool or downstream re-import auto-infers their type, stripping leading zeros or flipping long digit strings to scientific notation. The outbound mirror of `import-guard`'s inbound bulk-upload review. Use when adding or reviewing a bulk export/download/report feature, or when asked "does this export cap out silently", "will Excel mangle our IDs", "is this export actually complete", or "can admins trust this report".
---

# export-guard

An export that returns fewer rows than exist, or mangles the rows it does return, is worse than one that errors — an error gets noticed and fixed; a quietly wrong file gets trusted and acted on. Two real, documented failure shapes recur here, and neither looks like a bug from the code's own perspective: a `findMany({ take: 20_000 })`-style row cap that was fine at launch and became a silent data-loss bug the moment the table grew past it (a real fix, not a hypothetical: a production admin financial-reporting export was found silently dropping every order past the 20,000th, replaced with a keyset-paginated stream with no upper bound), and a CSV whose numeric-looking identifier columns get corrupted the instant they're opened in Excel or re-parsed by another tool's default type inference — a real, reproduced case: a review-queue CSV round-trip where ids like `"007"` came back as the integer `7` on read-back, silently breaking every decision match (`n_applied=0` with no error). Both bugs pass every test that only checks "did the export run and produce a file." Neither is caught by re-opening the file with the same tool that wrote it, which round-trips cleanly and hides exactly the corruption a human or a different downstream tool would hit.

## Step 1: find the completeness boundary

Locate where the export's data actually gets pulled and find every place a boundary could silently cut it short:

- **A hard row cap** — `LIMIT`/`take`/`.first(N)` with no corresponding check for "were there more rows than this," the exact shape of the real bug this skill is grounded in.
- **Pagination that stops early** — a loop that fetches pages but breaks on the first empty-seeming page, a max-page-count guard that was sized for today's data volume, or an off-by-one that drops the last page.
- **A request/serverless timeout** — synchronous export handlers built for a small dataset that silently return whatever was assembled before a platform-enforced timeout (API Gateway, a load balancer's idle timeout, a worker's execution limit) kills the request; check whether the response in that case is a partial 200 or an actual error.
- **An in-memory buffer** — building the whole export as a string/array before writing it out means an OOM or a size limit on the response body silently truncates output that was otherwise complete.

The fix for a genuine completeness boundary is almost always the same shape as the real case this skill is grounded in: switch from "fetch up to N" to a keyset-paginated stream with no upper bound, written incrementally rather than buffered whole. If a stream is already in place, verify it's actually unbounded — a "streaming" implementation that still pages through a capped total iterator has the same bug with extra steps.

## Step 2: check what's reported when a boundary is hit

A row cap or timeout isn't automatically a bug — an intentionally capped export (e.g. "preview first 1,000 rows") is fine if it says so. What's not fine is silence. Check:

- Does the response, filename, or UI distinguish "here are all N rows" from "here are the first N rows"? A row count in a status message or footer isn't enough if the consumer has no way to know whether that number is the whole answer.
- Is there a way for the caller to detect truncation programmatically (a `truncated: true` flag, a total-vs-returned count, a non-200 status) rather than just a same-shaped file that happens to be short?
- For a timeout-prone synchronous export, is there an async/job-based path (generate now, download when ready) for exports likely to exceed the timeout, or does every export silently share the same time budget regardless of size?

## Step 3: check whether identifier columns survive being opened

Find every column being written that's a numeric-looking string where the value's *identity* matters more than its magnitude — ZIP codes, phone numbers, order/account/tracking numbers, anything with meaningful leading zeros or more than about 15 digits. Then check whether the write path does anything to protect that column's type once it leaves your code:

- **Plain CSV with no quoting hint**: a spreadsheet tool's default "open" behavior (not even an explicit import step) auto-infers column types per RFC 4180-agnostic heuristics — a leading-zero string becomes a stripped integer, and a long digit string (account numbers, some tracking numbers) can flip to scientific notation, both silent, both lossy, and neither reversible by reformatting the cell after the fact.
- **A downstream re-import of your own export**: even without ever touching Excel, a second tool reading the CSV with default type inference (pandas `read_csv` without `dtype=str`, for example) hits the identical corruption — this is not an Excel-specific problem, it's a "nothing marked this column as text" problem. The real case this skill is grounded in wasn't Excel at all: a review-queue CSV round-trip through a data-cleaning library's own reader lost leading-zero ids on the very next read.
- **What actually prevents it**: quoting the field so it's unambiguously a string isn't sufficient on its own for Excel specifically (Excel's type-inference runs on cell content, not CSV quoting) — the reliable fixes are a `="0501"` Excel text-formula wrapper, a real XLSX output with the column's number format explicitly set to text, or (for tools consuming the CSV programmatically rather than through a spreadsheet UI) a documented contract that the column must be read with an explicit string dtype. If the export's only claim to safety is "we quote the CSV field," that's a documented gap, not a fix — say so.

## Step 4: verify the export was actually tested past its own boundaries

Check what the export's own tests (if any) actually exercise: a test asserting on 5 rows says nothing about the cap found in step 1, and a test that only re-parses the output with the same library that wrote it says nothing about the corruption found in step 3 — that round-trip is exactly the case that hides the bug. Look for (or flag the absence of) a test at a row count that actually crosses any cap/page-size/timeout boundary found in step 1, and, for identifier columns, either a real spreadsheet-open verification or an explicit note that this wasn't tested and is a caveat, not a guarantee.

## Report

Lead with whichever applies: (a) the export can silently return an incomplete result under conditions likely to occur in production (a growing table crossing a hardcoded cap, a large customer crossing a timeout budget) with no signal that anything was cut, or (b) an identifier column with real production values (not just this run's test data) will silently corrupt on open. Both are BLOCK-level for anything used as a system of record, an admin trust surface, or financial/compliance reporting — the whole value of an export like that is that it can be trusted without re-verifying against the source. For a low-stakes or genuinely-intended-partial export (an explicit "preview" or "sample" download), the same findings are CAUTION-level as long as step 2's honesty check passes. Cite the specific line where the row limit, pagination loop, or column write happens — this skill's findings should point at exact code, not general advice.

## Boundaries

- Not `import-guard` — that skill reviews the inbound path (a user-facing bulk upload parsing untrusted files). This skill reviews the outbound path (your own code generating a file for someone to trust). If a feature does both (export a template, let the user edit it, re-import it), review each direction with its matching skill.
- Not `backfill-pilot` — that skill is for an engineer's own one-off script mutating rows already in a live table; this skill is for a repeatable feature that reads and hands data to a user.
- Doesn't cover who's allowed to run an export or what PII it exposes to that caller — that's an authorization/data-exposure question for `security-sweep`, not a completeness/fidelity question for this skill.
- Doesn't cover CSV formula injection (`=`, `+`, `-`, `@` prefixed cells executing in the opener's spreadsheet app) — that's a security finding, also `security-sweep`'s territory, distinct from the silent-corruption-on-open failure this skill targets.
- Doesn't judge whether the export's chosen columns or business logic are correct — only whether the rows it decides to include actually all make it out, and whether their values survive being opened.
- Can't verify a specific spreadsheet application's current type-inference behavior beyond what's documented and independently reproduced — if a claim about how a particular tool handles a particular column type can't be confirmed, say so rather than asserting it.
