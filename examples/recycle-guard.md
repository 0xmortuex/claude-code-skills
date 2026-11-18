# recycle-guard — example

**Trigger:**

> we use phone-number-based SMS for both 2FA and password recovery. a
> support ticket came in from someone who says they got a "your password
> was reset" text for an account that isn't theirs — they just got a new
> phone number from their carrier last month. here's the relevant code:
>
> ```python
> # signup.py
> def enroll_phone_2fa(user, phone_number):
>     code = send_otp(phone_number)
>     pending_verifications[user.id] = (phone_number, code)
>
> def confirm_phone_2fa(user, submitted_code):
>     phone_number, code = pending_verifications[user.id]
>     if submitted_code == code:
>         user.phone_number = phone_number
>         user.phone_verified_at = now()
>         db.save(user)
>
> # recovery.py
> def start_password_recovery(phone_number):
>     user = db.find_by_phone(phone_number)
>     if user:
>         send_otp(phone_number)  # no re-check of phone_verified_at
>
> # phone_change.py
> def change_phone_number(user, new_phone_number):
>     existing = db.find_by_phone(new_phone_number)
>     if existing:
>         raise ConflictError("phone number already registered")
>     # otherwise: same enroll/confirm flow as signup
> ```

**Response shape:**

Step 1 checks whether ownership is ever re-verified after the initial binding:

```
Step 1: re-verification after initial binding
`phone_verified_at` is written once in `confirm_phone_2fa` and never read
anywhere else in the codebase — `start_password_recovery` looks the
account up by phone number and fires an OTP with no check on how long ago
verification happened, no carrier lookup, and no re-verification trigger
tied to account dormancy. The only proof of ownership this app ever
collects for a phone number is the single OTP at enrollment, held
indefinitely.
```

Step 2 checks what happens when a number is reassigned inside the app's own data model:

```
Step 2: re-binding conflict handling
`change_phone_number` treats an already-registered number as a hard
`ConflictError` — it blocks the new owner outright rather than offering
any path to prove ownership and take over the binding. That's a usability
bug, not the security gap: the real gap is that `start_password_recovery`
has no such conflict check at all. Nothing in `recovery.py` distinguishes
"the original verified owner" from "whoever currently holds this SIM" —
if the carrier reassigns the number outside the app entirely (the ticket's
reported case), the new legitimate holder of the number can trigger
recovery and receive the OTP with zero friction, since `find_by_phone`
only ever looks at who's on file, never when or whether that's still true.
```

Step 3 checks how easy this is for an opportunistic attacker to find and exploit:

```
Step 3: exploitability
`start_password_recovery` takes a bare phone number with no rate limit
visible in this file — worth flagging as a likely compounding issue
(someone holding a batch of recently-recycled numbers could probe all of
them against this endpoint cheaply), though confirming there's no limiter
elsewhere in the stack needs a look outside this file.
```

Report:

```
## recycle-guard review: signup.py, recovery.py, phone_change.py

1. No code path ever re-verifies phone ownership after
   `confirm_phone_2fa`'s one-time OTP (BLOCK — this is the ticket's
   reported mechanic: a recycled number's new owner can land directly
   in `start_password_recovery` and receive a reset code for an account
   that was never theirs).

2. `start_password_recovery` has no notion of binding staleness or
   reassignment at all — it trusts `db.find_by_phone` unconditionally
   (BLOCK, same root cause as #1, named separately because fixing #1
   requires giving this function something to check against).

3. `change_phone_number`'s hard conflict error (CAUTION, separate from
   the BLOCK above) blocks a legitimate new owner with no recourse, while
   contributing nothing toward re-verification since the dangerous path
   is recovery, not the explicit in-app change flow.

## Verdict: BLOCK
A phone number is trusted forever once bound, with no re-verification and
no reassignment signal anywhere in the recovery path — exactly the gap the
support ticket reports being exploited. Fix: have `start_password_recovery`
check binding age (or a carrier line-type/porting signal if available) and
require a stronger second factor or manual review past some staleness
threshold; turn `change_phone_number`'s conflict into a verified-takeover
flow that unbinds the old account's 2FA from that number and notifies the
old account by email (if one's on file) rather than just erroring out; and
confirm rate limiting on `start_password_recovery` keyed by phone number
exists somewhere in the stack even though it isn't visible in these files.
```
