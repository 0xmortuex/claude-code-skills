# cipher-guard — example

**Trigger:**

> we're mid-migration on `users.ssn` from unencrypted to Active Record
> Encryption. a security reviewer asked if the uniqueness constraint still
> holds during the rollout, and separately whether our "annual key rotation"
> actually protects us if a key ever leaked. can you check?
>
> ```ruby
> # app/models/user.rb
> class User < ApplicationRecord
>   encrypts :ssn, deterministic: true, previous: { deterministic: false }
>   validates :ssn, uniqueness: true
> end
> ```
>
> ```yaml
> # infra/kms-rotation.tf (comment above the resource)
> # KMS automatic key rotation is enabled on this CMK — rotates annually.
> # Satisfies our "keys are rotated at least yearly" policy requirement.
> ```

**Response shape:**

Step 1 scopes to the two application-level encryption sites in play:

```
Step 1: encryption sites found
`users.ssn` — Active Record Encryption, currently mid-migration from
unencrypted rows to `deterministic: true` with a `previous:` fallback.
Queried for uniqueness. The CMK behind it has AWS KMS "automatic key
rotation" enabled. Both are in scope; TLS/disk encryption are not.
```

Step 2 traces the uniqueness check against the actual migration state — this is the `rails/rails#51553` pattern, not a hypothetical:

```
Step 2: deterministic encryption vs. equality-query correctness
The `encrypts :ssn, deterministic: true, previous: { deterministic: false }`
declaration is the exact shape in rails/rails#51553 ("Validation Does Not
Work with Multiple Encryption Scheme"). Per that issue, Active Record's
uniqueness validator can only query against ciphertext encrypted under a
*deterministic* scheme — it has no way to issue a DB query that matches
the old, non-deterministic ciphertext still sitting in every row written
before this migration started. During the rollout window, `validates :ssn,
uniqueness: true` silently stops catching duplicates against any
pre-migration row: a new SSN that collides with an old-scheme row's
plaintext will pass validation and get inserted, because the validator
can't see the collision. This isn't a future risk — it's happening on
every row still holding old ciphertext, right now, for as long as the
migration is in progress.
```

Step 3 separates what the KMS comment claims from what it actually does:

```
Step 3: what "key rotation" actually does here
AWS KMS automatic rotation on a CMK re-wraps the key material behind the
CMK — it doesn't touch any data already encrypted under the data keys that
CMK wrapped. This is a re-wrap (KEK rotation), the cheap O(1) operation,
not a re-encrypt (DEK rotation) that would touch the actual `ssn` rows.
The infra comment's claim ("satisfies our key rotation policy") is true
for the policy's literal "rotate annually" wording, but it does not do
what a reviewer asking "does this protect us if a key leaked" is actually
asking: if the data-encryption key itself (not the CMK) were ever
extracted — e.g. from a process memory dump — automatic CMK rotation
would not re-encrypt a single existing row, and no re-encryption job
exists anywhere in this repo to do that. The annual-rotation checkbox is
real; the compromise-response capability it's being used to imply is not.
```

Step 4 is scoped out — no new KMS policy changes are in this diff, so it's reported as unchecked rather than padded:

```
Step 4: key policy scope
Not reviewed this pass — no key-policy/grant changes are in this diff.
Flagging as a separate open item: this CMK's policy hasn't been diffed
against current callers in this review and should be before relying on
"rotation" as the compromise story.
```

Report:

```
## cipher-guard review: User#ssn migration + CMK rotation claim

1. `validates :ssn, uniqueness: true` does not enforce uniqueness against
   any row still holding pre-migration, non-deterministic ciphertext —
   confirmed via rails/rails#51553, same `deterministic: true` +
   `previous: { deterministic: false }` shape (BLOCK).

2. "Automatic key rotation" on the CMK re-wraps the key only; it does not
   re-encrypt existing `ssn` ciphertext and would not help if the
   data-encryption key itself were compromised. No re-encryption job
   exists to close that gap (BLOCK on the compromise-response claim;
   the annual-rotation policy checkbox itself is satisfied).

3. Key-policy scope not reviewed — out of this diff's range, logged as an
   open follow-up rather than assumed clean.

## Verdict: BLOCK
Two independent problems, not one: the uniqueness check has a real,
currently-active gap for the duration of the migration (not just a
migration-complete-state risk), and the rotation story the team is relying
on for breach response doesn't match what the mechanism actually does.
Fix for (1): either backfill all legacy rows to the deterministic scheme
before enabling the uniqueness validator, or add an application-level
uniqueness check that decrypts and compares in Ruby for the
still-migrating window. Fix for (2): write down what "rotation" actually
covers today (KEK re-wrap only) versus what a real DEK-compromise response
would require (a batched re-encryption job, dual-key reads during the
window), and treat the policy checkbox and the compromise-response
capability as two separate things in the next security review.
```
