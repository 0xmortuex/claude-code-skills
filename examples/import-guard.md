# import-guard — example

**Trigger:**

> we shipped CSV contact import for our CRM last month. a customer just
> emailed support: they uploaded 300 contacts, saw "23 skipped" in the
> result, fixed what they thought were the bad rows, re-uploaded the same
> file, and now has ~280 duplicate contacts. here's the endpoint:
>
> ```python
> # imports/views.py
> def import_contacts(request):
>     file = request.FILES['csv']
>     reader = csv.DictReader(io.TextIOWrapper(file))
>     imported = 0
>     skipped = 0
>     for row in reader:
>         try:
>             Contact.objects.create(
>                 email=row['email'],
>                 name=row['name'],
>                 company=row['company'],
>             )
>             imported += 1
>         except Exception:
>             skipped += 1
>     return JsonResponse({"success": True, "imported": imported, "skipped": skipped})
> ```

**Response shape:**

Step 1 locates the failure unit before judging anything else:

```
Step 1: failure unit
Contact.objects.create() runs inside the per-row loop with no surrounding
transaction — each row commits independently. This is the common case
where partial success is the normal outcome, so step 2 (what gets reported)
is where the real risk sits, not step 1 itself.
```

Step 2 is where the reported bug's other half lives — the response shape
doesn't match what the code can actually tell the user:

```
Step 2: what's reported vs. what's detectable

- `"success": True` is hardcoded — it's returned even when skipped == 300
  and imported == 0. The caller (and the UI banner reading this field) has
  no way to distinguish "clean import" from "every row failed."
- `except Exception: skipped += 1` swallows the actual error and discards
  it. The response has no per-row detail at all — not even which row
  numbers failed, let alone why. The customer's "23 skipped" is a raw
  count with nothing to act on, which is why they had to guess at which
  rows to fix rather than being told.
- Checked what actually raises inside the try: `Contact.objects.create`
  will throw on a DB-level `IntegrityError` (e.g. a NOT NULL violation if
  `company` is blank) but a malformed-but-non-null value — a row shifted
  one column to the left by a stray comma in a company name, for example
  — writes successfully with garbage data and is never counted as
  skipped at all. Silent corruption, not silent failure.
```

Step 3 checks for a safety net before the customer's only option is "just
run it and see":

```
Step 3: dry-run path
No validate-only mode found — `import_contacts` is the only entry point,
and it writes on the first call. For a contacts list in the hundreds this
is a real gap, not a nice-to-have: the customer's only way to discover a
bad row is a live import that partially commits.
```

Step 4 is where the reported bug actually confirms:

```
Step 4: re-upload behavior
`Contact.objects.create(email=row['email'], ...)` — plain INSERT, no
`get_or_create`, no unique constraint on `email` in the model or a DB
migration. Confirmed: re-running the same file a second time re-inserts
every row that succeeded the first time, including the ~277 that were
already fine. This matches the report exactly — the customer didn't
re-upload only their fixed rows, they re-uploaded the whole file (the
only option the UI gives them), and every already-good row duplicated.
```

Report matches the skill's lead-with-the-trust-breaking-bug order:

```
## import-guard review: imports/views.py::import_contacts

1. Re-upload duplicates (BLOCK — confirmed root cause of the ticket):
   no natural-key upsert and no unique constraint on `email`. Re-running
   the same file duplicates every previously-successful row. Fix: add a
   unique constraint on `email` (scoped to org/tenant if multi-tenant) and
   switch to `Contact.objects.update_or_create(email=row['email'],
   defaults={...})`.

2. Success is misreported (BLOCK — the other half of the trust gap):
   `"success": True` is unconditional and the only failure detail is a
   bare count with the actual exception discarded. Fix: return per-row
   results (row number, field values, and the real error string) instead
   of just `skipped`, and only report `success: true` when
   `skipped == 0`.

3. Silent corruption on non-null-violating bad data (CAUTION): a
   shifted-column row from a stray comma writes successfully and isn't
   counted as skipped or imported-with-warning. Recommend validating
   column count and required-field shape per row before the `create()`
   call, not relying on the DB constraint to catch it.

4. No dry-run path (CAUTION): for a customer-facing import at this scale,
   add a validate-only pass that returns the same per-row error detail
   from finding 2 without writing, so the customer can fix their file
   once instead of discovering problems 23 rows at a time across repeated
   live imports.

## Verdict: BLOCK
Findings 1 and 2 together explain the ticket: the customer was told a
false "23 skipped" summary with nothing to act on, then had no safe way to
re-submit only what was actually wrong. Fix both before this endpoint
handles another customer file — the unique constraint alone would stop
new duplicates but wouldn't fix the reporting gap that caused the
customer to re-upload the whole file in the first place.
```
