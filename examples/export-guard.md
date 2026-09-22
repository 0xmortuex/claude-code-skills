# export-guard — example

**Trigger:**

> finance keeps saying our monthly "export all orders" CSV feels short —
> they think we have way more orders than the file shows. separately, a
> couple of the order-number and phone columns look garbled when they open
> it in Excel, like the numbers changed. here's the export handler:
>
> ```js
> // api/admin/orders/export.js
> export async function exportOrders(req, res) {
>   const orders = await prisma.order.findMany({
>     take: 20000,
>     orderBy: { createdAt: 'asc' },
>     select: { id: true, orderNumber: true, customerPhone: true, total: true, createdAt: true },
>   });
>   const rows = orders.map(o =>
>     `${o.id},${o.orderNumber},${o.customerPhone},${o.total},${o.createdAt}`);
>   const csv = ['id,orderNumber,customerPhone,total,createdAt', ...rows].join('\n');
>   res.setHeader('Content-Type', 'text/csv');
>   res.status(200).send(csv);
> }
> ```

**Response shape:**

Step 1 finds the completeness boundary before anything else:

```
Step 1: completeness boundary
`findMany({ take: 20000, ... })` — a hard cap with no check for whether
the order table actually has more rows than that. No pagination, no
streaming, no follow-up query. This is the exact shape of a real fixed
bug (a production admin export capped at 20,000 rows and silently
dropping everything past it, replaced with an unbounded keyset-paginated
stream) — not a hypothetical failure mode.
```

Step 2 checks whether hitting that boundary is reported honestly:

```
Step 2: what's reported when the cap is hit
`res.status(200).send(csv)` — unconditional 200 regardless of whether
`orders.length === 20000` (cap hit, more rows exist) or the table
genuinely has fewer orders than that. No `truncated` flag, no
total-vs-returned count, no warning in the filename or a response
header. Finance's "feels short" complaint is exactly what this predicts:
once order volume crossed 20,000, every export since has silently been
missing however many rows exceed the cap, with nothing in the response
to tell them.
```

Step 3 checks whether the identifier columns survive being opened:

```
Step 3: identifier-column fidelity
`orderNumber` and `customerPhone` are interpolated directly into the CSV
row string — no quoting, no text-format hint, no Excel `="..."` wrapper.
Both are exactly the column shape this skill flags: `orderNumber` values
like "007182" lose the leading zero the moment Excel opens the file
(reads as the integer 7182), and `customerPhone` values stored as bare
national-format digits without a leading `+` are read as a number,
which either drops a leading zero the same way or, for a longer
E.164-style value, risks Excel's >15-digit scientific-notation
conversion. This matches the second half of the report exactly ("order
numbers look garbled") and is not a display quirk — the value written
to the cell is actually altered, and reformatting the cell afterward
does not recover the original digits.
```

Step 4 checks whether any existing test would have caught either bug:

```
Step 4: test coverage past the boundary
The only export test seeds 5 fake orders and asserts on the returned
row count and a couple of field values — nowhere near the 20,000-row
cap, so step 1's bug is untested by construction. The test also
re-parses its own output with the same `csv-parse` call the app uses
elsewhere with `columns: true` (default type inference off, so it
happens to preserve strings) — it never opens the file in a spreadsheet
tool or with a plain `dtype`-inferring reader, so step 3's corruption is
invisible to this test even though it's real in Excel.
```

Report matches the skill's lead-with-the-trust-breaking-finding order:

```
## export-guard review: api/admin/orders/export.js::exportOrders

1. Silent truncation past 20,000 rows (BLOCK — confirmed root cause of
   finance's "feels short" report): `take: 20000` with no bound check
   and no signal when the cap is hit. Fix: replace with a keyset-paginated
   stream (`(createdAt, id)` cursor, batched fetch, write CSV
   incrementally) with no upper bound, the same pattern used to fix the
   real production case this finding is grounded in.

2. Identifier columns corrupt on open (BLOCK — confirmed root cause of
   the "order numbers look garbled" report): `orderNumber` and
   `customerPhone` are written as bare unquoted numeric-looking strings.
   Fix: wrap both in an Excel text-formula (`="007182"`) or switch the
   export to real XLSX with those columns' number format explicitly set
   to text — plain CSV quoting alone does not stop Excel's type
   inference.

3. No completeness signal in the response (CAUTION, subsumed by fixing
   finding 1 but worth calling out separately): even after removing the
   hard cap, add a way for the caller to confirm an export is complete
   (a row-count total, or at minimum confirm the new streaming path has
   no other implicit limit) rather than trusting file size alone.

4. Test coverage doesn't exercise either failure mode (CAUTION): add a
   test at a row count that crosses whatever boundary remains after
   fixing finding 1, and a fixture-based check (or a documented manual
   verification) that a leading-zero `orderNumber` actually round-trips
   through a real spreadsheet open, not just the app's own CSV parser.

## Verdict: BLOCK
Findings 1 and 2 independently confirm both halves of the original
report — the export has been silently incomplete since order volume
passed 20,000, and the columns finance actually looks at by eye are
corrupted the moment the file is opened, not just theoretically at
risk. Fix both before this export is used for another finance cycle;
neither is a cosmetic issue, and the whole value of an admin export is
that it can be trusted without re-checking against the source data.
```
