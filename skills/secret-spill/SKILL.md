---
name: secret-spill
description: Incident response for a credential that leaked into git or logs — an API key, token, password, or private key committed to a repo, pasted into CI output, or found by a scanner. Use the moment the user says "I committed my API key", "there's a secret in the repo", "GitGuardian/GitHub emailed me about a leaked key", or a scanner/security-sweep finding turns out to be a REAL credential already in history. This is remediation, not detection: the instinctive fix (delete the file in a new commit) leaves the secret fully visible in history — treat every spill as an incident with an ordered response.
---

# secret-spill

A secret in git history is not a code problem, it's a live incident: anyone who can read the repo — or already cloned, forked, or scraped it — has the credential *now*. The order of operations is everything, and the instinct ("quick, remove it from the code!") gets it exactly backwards. History rewriting without rotation is theater; rotation without blast-radius assessment leaves siblings burning.

**The order: rotate → assess → purge → verify → prevent.** Never reorder.

## 1. Rotate first — before anything else

The secret is compromised the moment it left the vault; assume it was scraped within minutes if the repo is public (bots watch the GitHub firehose for exactly this). Revoke/rotate the credential at the provider *now*, then fix git at leisure. Sequence for zero downtime: issue new credential → deploy it to whatever legitimately uses it → revoke old.

While rotating, widen one step: **secrets travel in packs.** The `.env` that leaked one key usually held six. Check what else was in the leaked file/commit and rotate everything exposed, not just the one the scanner flagged.

If the user can't rotate (it's a teammate's key, a customer's, production-critical with unknown consumers): escalate to whoever can, immediately — that message outranks every other step.

## 2. Assess the blast radius

Determines urgency of the rest:

- **Visibility**: public repo (assume compromised, period — including if it was public *briefly*), private repo (who has read access? any third-party apps/integrations?), CI logs (who can read builds?).
- **Copies you don't control**: forks (a purge doesn't touch them — GitHub keeps fork networks sharing objects; a secret pushed to a fork-networked repo can stay fetchable by sha even after deletion), collaborators' clones, package tarballs published from the repo, dependency mirrors, PR refs.
- **Abuse check**: the provider's audit log (AWS CloudTrail, GitHub token audit, GCP, Stripe…) for use of the credential since the leak window opened. Any unexplained use upgrades this from "leak" to "breach" — bigger response, different skill set, say so plainly.

## 3. Purge history — now it's worth doing

With rotation done, purging is hygiene (keeps scanners quiet, stops future re-leaks via old branches), not protection. Be honest with the user about that.

- Tool: `git filter-repo` (or BFG) — `git filter-repo --replace-text` with the secret, or `--invert-paths` for a whole file. Never interactive-rebase a shared history by hand.
- Coordinate: this rewrites every descendant sha. Protected branches need force-push temporarily allowed; every collaborator must re-clone (not pull — pulls resurrect the old history and someone WILL push it back). Send that message before the force-push, not after.
- Platform residue: cached views and PR refs on the host survive force-push — GitHub support can garbage-collect them on request; do the same check on GitLab/Bitbucket equivalents.
- If the repo is public and heavily forked, say the true thing: history purge cannot reach the forks; rotation is the only real remedy, and the purge is for hygiene only.

## 4. Verify

- Re-scan **all refs**, not the working tree: `gitleaks git --log-opts="--all --reflog"` / `trufflehog git file://. --all-branches` style, covering branches, tags, and the reflog. Plain `gitleaks git` only walks the current branch's history — without `--log-opts`, a clean result proves nothing about secrets sitting on other branches.
- Grep CI logs and build artifacts for the secret string.
- Confirm the old credential is actually dead: make a real call with it and expect an auth failure. "I clicked revoke" is a hypothesis; a 401 is a fact.

## 5. Prevent — only after the fire is out

One tight paragraph, not a lecture: move the secret to env/secret-manager, add the file to `.gitignore` with a committed `*.example` template, and install a pre-commit scanner (gitleaks hook) plus push protection if the host offers it. If the team wants a deeper preventive review of current changes, that's security-sweep's job.

## Boundaries

- Never print the secret's value into the conversation, the incident notes, or a commit message — refer to it by fingerprint (first/last 4 chars, provider, scope).
- Evidence of active abuse (step 2) means this is now a breach investigation — recommend the provider's incident process / a security engineer; don't cosplay forensics beyond the audit-log check.
- Purging shared history is destructive coordination: get the user's explicit go-ahead on the force-push and the re-clone announcement — never force-push a shared repo on your own initiative.
