# residency-guard — example

**Trigger:**

> our contract with an EU hospital network says "patient data never leaves
> the EU." a customer's security team asked us to prove it before renewal.
> our primary DB is in eu-central-1 — can you check the rest of the stack?
>
> ```hcl
> # infra/db.tf
> resource "aws_db_instance" "primary" {
>   identifier = "patients-eu"
>   region     = "eu-central-1"
> }
>
> resource "aws_db_instance" "replica_latency" {
>   identifier             = "patients-us-read"
>   replicate_source_db    = aws_db_instance.primary.id
>   region                 = "us-east-1"   # added 2026-04 for US support-team dashboard latency
> }
>
> resource "aws_db_instance" "dr_standby" {
>   identifier          = "patients-dr"
>   replicate_source_db = aws_db_instance.primary.id
>   region              = "us-west-2"      # DR runbook promotes this on primary-region outage
> }
> ```
>
> ```hcl
> # infra/cdn.tf
> resource "aws_cloudfront_distribution" "app" {
>   origin { domain_name = "api.example.com" }
>   restrictions { geo_restriction { restriction_type = "none" } }
> }
> ```
>
> ```html
> <!-- patient portal frontend -->
> <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
> <script>gtag('config', 'G-XXXX', { anonymize_ip: false });</script>
> ```

**Response shape:**

Step 1 enumerates every surface, not just the DB everyone already checked:

```
Step 1: surfaces touching patient data
- Primary DB: eu-central-1. Correct, and the only surface anyone
  re-verified when this contract was signed.
- replica_latency: a read replica in us-east-1, added four months ago
  for an internal support dashboard — no residency review at add time.
- dr_standby: DR promotion target in us-west-2. Not reviewed against
  the residency commitment because DR is normally reviewed for RTO/RPO,
  not jurisdiction.
- CloudFront distribution: geo_restriction is "none" — no edge
  restriction at all, so any edge location worldwide can cache and log
  patient-portal responses.
- Google Analytics (gtag.js) on the patient portal, with
  anonymize_ip: false — sends full IP + page data to Google's global
  infrastructure on every page view, including from EU patients.
```

Step 2 checks whether each surface is enforced by config or just holds by convention:

```
Step 2: config-level enforcement vs. convention
- Primary DB: enforced — region is hardcoded in the resource, and
  provisioning any resource outside eu-central-1 for this workload
  would be a visible Terraform diff.
- replica_latency, dr_standby: NOT enforced. Nothing in the Terraform,
  IAM, or CI stops a future `replicate_source_db` from landing in any
  region — the current us-east-1/us-west-2 placement is just where
  whoever added them happened to put them.
- CloudFront: NOT enforced — geo_restriction is explicitly set to
  "none," the opposite of a restriction.
- gtag.js: NOT enforced and can't be, from this codebase alone — it's
  Google's infrastructure, not ours; anonymize_ip: false makes it
  worse by keeping the full IP in what Google receives.
```

Step 3 separates the write path (already reviewed) from read/failover/async paths (never reviewed):

```
Step 3: write vs. read vs. failover
- Write path: patient records are written to patients-eu only.
  Correct.
- Read path: the support dashboard's queries are routed to
  replica_latency in us-east-1 — patient data is being read out of the
  EU today, continuously, not just in a disaster scenario.
- Failover path: the DR runbook promotes patients-dr (us-west-2) on
  primary-region outage — the exact scenario the contract's residency
  promise most needs to hold, and the one path nobody re-checks
  because DR reviews focus on RTO/RPO, not jurisdiction.
```

Step 4 traces actual destinations rather than trusting the privacy policy:

```
Step 4: evidence
- replica_latency and dr_standby: confirmed directly from the
  Terraform region attributes — no live trace needed, the
  infra-as-code is the source of truth here.
- gtag.js: this is the noyb.eu/Google Analytics shape exactly — the
  portal's own privacy policy says "EU-hosted," but the script ships
  full IP and page data to Google's global infrastructure regardless
  of hosting region. Confirming where Google actually processes it
  needs Google's own DPA/compliance documentation, not code
  inspection — flagged as unverified rather than assumed compliant.
```

Report:

```
## residency-guard review: patient-data infrastructure

1. DR failover target (us-west-2) is outside the committed boundary
   (BLOCK): the runbook promotes patients-dr on primary-region outage,
   which is exactly the moment the residency promise is contractually
   supposed to hold hardest. Fix: stand up the DR target inside the EU
   (e.g. eu-west-1) or make the current cross-region standby
   read-only/non-promotable until it is.

2. A live read replica (us-east-1) is serving patient-data reads
   outside the EU today, continuously, not hypothetically (BLOCK):
   added for internal dashboard latency with no residency review. Fix:
   move the replica in-region, or move the dashboard workload to query
   the EU primary/an EU-region replica instead.

3. CloudFront has no geo restriction on the patient portal (BLOCK):
   `restriction_type = "none"` lets any edge location worldwide cache
   and log responses. Fix: set an allow-list geo restriction to EU
   edge locations, or move to an EU-restricted CDN configuration.

4. Google Analytics on the patient portal sends full IP + page data to
   Google's global infrastructure, `anonymize_ip` disabled (BLOCK,
   same shape as the 2022 Austrian DSB ruling against this exact
   pattern): the portal's privacy policy claims EU-only, but a
   third-party SDK is the actual boundary-crosser. Fix: remove gtag.js
   from any page handling patient data, or replace it with an EU-hosted
   analytics vendor with a verified data-processing agreement.

## Verdict: BLOCK
The primary database is exactly where the contract says — that's the
one surface already reviewed. Every other surface added or configured
since then (a read replica, a DR target, a CDN, an analytics SDK)
crosses the committed boundary today, not just in a hypothetical
failover. Before renewal, fix the DR target and the live replica first
(active, continuous exposure), then the CDN and analytics SDK.
```
