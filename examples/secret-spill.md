# secret-spill — example

**Trigger:**

> just got a GitHub secret scanning email — looks like I committed our
> Stripe secret key in `.env` three commits ago. repo's public. can you
> clean it up?

**Response shape:**

Claude doesn't start with the instinctive fix (delete the file, push a new
commit) — it opens with why that's backwards, then goes straight to rotation
before touching git at all:

```
Deleting the file now would leave the key fully readable in history — anyone
who cloned or forked in the last three commits already has it, and a public
repo means assume it was scraped within minutes. First move is rotating the
credential at the provider, not editing git. I'll do that first, then fix
history at leisure.

Rotating the Stripe secret key now:
  1. Issue a new secret key in the Stripe dashboard
  2. Deploy it to whatever legitimately uses it (checking: this looks like
     it's read by the backend's payment service — confirm before I revoke
     the old one, so we don't cause an outage)
  3. Revoke the old key once the new one is confirmed live
```

It widens past the one flagged key, since `.env` files rarely leak alone:

```
Checked the rest of the committed .env — it also has STRIPE_WEBHOOK_SECRET
and AWS_SECRET_ACCESS_KEY. The scanner only flagged the Stripe key because
that's the pattern it recognizes, but both of these were exposed in the same
commit and need rotating too, not just the one GitHub emailed about.
```

Before purging, it assesses blast radius rather than jumping straight to a
history rewrite:

```
Blast radius:
  - Repo is public, so assume compromised regardless of how long it was
    live — no window is "too short to matter."
  - Forks: this repo has 4 forks. A history purge here won't reach them —
    GitHub keeps fork-network objects fetchable by sha even after the
    upstream rewrites. Rotation is the actual fix for that exposure; the
    purge below is hygiene only.
  - Abuse check: pulling Stripe's API request log for the leaked key's
    fingerprint (sk_live_...ab12) since the leak window opened. [checks]
    No unexplained charges or requests — this stays a leak, not a breach.
```

Only after rotation and assessment does it purge, and it's explicit that
this step is destructive and needs sign-off before running:

```
Purge plan (needs your go-ahead before I run it — this force-pushes and
rewrites every descendant sha):
  git filter-repo --replace-text <(echo 'sk_live_...==>REDACTED')
  Then: temporarily allow force-push on main's branch protection, force-push,
  and message every collaborator to re-clone (not pull — a pull resurrects
  the old history and it can get pushed right back).
```

It closes with verification as facts, not assertions, and prevention scoped
to one paragraph:

```
Verify:
  - gitleaks git --log-opts="--all --reflog" — clean, including tags and reflog
  - grepped CI build logs for the key substring — no hits
  - called the Stripe API with the old key: 401. It's actually dead, not
    just "revoked" in name.

Prevent: .env is now in .gitignore with a committed .env.example template;
added a gitleaks pre-commit hook so this can't happen again silently. If you
want a broader review of what else might be exposed in current code, that's
a separate security-sweep pass, not part of this incident.
```

Throughout, the key's actual value never appears in the conversation or the
purge command shown above — only its fingerprint (`sk_live_...ab12`).
