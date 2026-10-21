# rotation-guard — example

**Trigger:**

> we rotate the RDS password every 30 days through a Secrets Manager Lambda.
> last night's rotation caused ~4 minutes of 500s on about a third of our
> API pods — the other two thirds never even blipped. now we're about to
> add a *second* rotation for the third-party billing API key and I don't
> want a repeat. can you check why only some pods broke and whether the new
> rotation will have the same problem?
>
> ```hcl
> # infra/secrets-manager.tf
> resource "aws_secretsmanager_secret_rotation" "rds" {
>   secret_id           = aws_secretsmanager_secret.rds.id
>   rotation_lambda_arn = aws_lambda_function.rotate_rds.arn
>   rotation_rules { automatically_after_days = 30 }
> }
> # rotate_rds.py uses the AWS-provided "single user" rotation template —
> # one DB user, password changed in place, old password invalidated
> # as soon as the new one is confirmed working.
> ```
>
> ```yaml
> # k8s/api-deployment.yaml
> env:
>   - name: DB_PASSWORD
>     valueFrom:
>       secretKeyRef: { name: rds-secret, key: password }
> ```
>
> ```js
> // db.js — built once at module load, reused for the process lifetime
> const pool = new Pool({ host, user, password: process.env.DB_PASSWORD, max: 20 });
> // no idleTimeoutMillis / max connection lifetime configured
> ```

**Response shape:**

Step 1 separates the rotation mechanism from its two consumers:

```
Step 1: mechanism and consumers
Rotation mechanism: AWS Secrets Manager "single user" rotation template —
one RDS user, password changed in place. Consumers: (a) every API pod's
`pg.Pool`, built once at module load from `process.env.DB_PASSWORD`, no
max connection lifetime set; (b) the pod's own env var, sourced via
`secretKeyRef`. Two independent gaps to check, not one.
```

Step 2 identifies the mechanism has no overlap window at all:

```
Step 2: overlap window
The single-user template is the no-overlap shape: it changes the one live
password and the old one stops working as soon as the Lambda confirms the
new one connects — there's no second credential staying valid during a
transition. AWS's own alternating-users template exists specifically to
avoid this (two DB users trading "current" status so the previous one
stays valid through the cycle), and isn't what's deployed here.
```

Step 3 finds the specific consumer-side reasons the failure was partial, not total:

```
Step 3: consumer behavior
(a) `pg.Pool` has no `idleTimeoutMillis`/max-lifetime — a connection
opened at any point before rotation stays open and keeps authenticating
successfully until something else closes it (a deploy, a crash, the pool
hitting `max` and cycling). The ~1/3 of pods that failed were the ones
whose connections happened to cycle (an idle timeout under load, a pod
restart from an unrelated deploy) in the window right after rotation and
tried to open a *new* connection with the stale env var — the other 2/3
simply hadn't opened a new connection since rotation, so they were quietly
still running on an old password that, per Step 2, should already be dead.
(b) `DB_PASSWORD` via `secretKeyRef` is resolved once at container start
and never updates when the underlying Secret object changes — confirmed
Kubernetes behavior, not pod-specific. Nothing restarts these pods as part
of the rotation pipeline, so every pod is holding the pre-rotation value
in its env indefinitely; it's only moot right now because pg.Pool doesn't
re-read the env var either except when opening a fresh connection.
```

Step 4 calls out that nothing actually verified the cutover either direction:

```
Step 4: cutover verification
No post-rotation check exists for either direction. Nothing confirms the
old password is actually rejected (it should be, per the single-user
template, but that's an assumption, not a checked fact) — and nothing
confirms which pods are still authenticating on it. The partial outage is
the only evidence either way, and it's consistent with a worse story than
"rotation worked, a few pods had bad timing": it's equally consistent with
some pods still holding a working old credential right now.
```

Report:

```
## rotation-guard review: RDS rotation incident + planned billing-key rotation

1. No overlap window: single-user rotation template revokes the old
   password the instant the new one is confirmed — any consumer not yet
   on the new value breaks immediately, by design (BLOCK).

2. `pg.Pool` has no max connection lifetime, so a connection opened before
   rotation can run indefinitely on the old password; the 1/3-of-pods
   pattern matches connections that happened to cycle right after cutover,
   not a random blip (BLOCK — this is what caused last night's incident).

3. `DB_PASSWORD` via `secretKeyRef` never updates after rotation, and
   nothing restarts the deployment as part of the rotation pipeline — every
   pod is holding a stale value in its env with no mechanism to refresh it
   short of an unrelated restart (BLOCK).

4. No check exists that the old credential is actually rejected, or that
   every pod has moved to the new one — the incident report is the only
   signal either way (CAUTION, becomes BLOCK if repeated for the billing
   key without adding one).

## Verdict: BLOCK — and the billing-key rotation will reproduce this exactly
Switch RDS rotation to Secrets Manager's alternating-users template so a
previous credential stays valid through a real overlap window. Set
`idleTimeoutMillis`/max lifetime on `pg.Pool` shorter than that window, so
every connection is guaranteed to cycle onto the new credential within it.
Wire the rotation pipeline to trigger a rollout restart (or move
`DB_PASSWORD` to a volume-mounted Secret the app re-reads, not an env var)
so pods stop running on stale env vars indefinitely. Before shipping the
billing-key rotation, size its overlap window against that API client's
actual connection/cache lifetime instead of reusing the RDS mechanism's
timing by default — a third-party HTTP client may cache the key
differently than `pg.Pool` does. Add one check after every rotation: a
deliberate failed-auth attempt against the old credential, so "rotated"
stops being an assumption.
```
