---
name: git-rescue
description: Recover work that looks lost in git — after a bad `reset --hard`, a botched rebase or merge, a commit on the wrong branch, a deleted branch, a lost stash, commits orphaned in detached HEAD, or a force-push that overwrote history. Use this the moment the user says anything like "I lost my changes", "my commits are gone", "I reset and now it's empty", "the rebase destroyed everything", "I committed to main by accident", or "someone force-pushed over my work". Also use it BEFORE running any recovery command the user suggests themselves — panicked users propose destructive fixes.
---

# git-rescue

Someone who thinks they just lost hours of work is panicking, and panicked people (and agents) make it worse by running more destructive commands. Your job is the calm paramedic: **secure the scene, then diagnose, then recover.** Almost nothing in git is actually gone — committed work survives `reset --hard`, rebases, branch deletion, and force-pushes for weeks, because git only unlinks objects, it doesn't erase them until garbage collection (default grace: 2+ weeks).

## Rule zero: make things recoverable before you recover

Before ANY recovery action, snapshot the current state so your rescue can't cause a second accident:

```bash
git branch rescue-backup-$(date +%s)        # pin current HEAD (if there are commits worth pinning)
git stash push -u -m "rescue: working tree" # if the working tree has uncommitted changes worth keeping
```

And while rescuing, **never** run `reset --hard`, `checkout -- .`, `clean`, `rebase`, or `push --force` until you have positively located the lost work and stated where it is. One destructive command at a time, each one explained first.

## Diagnose: find where the work actually is

Ask (or determine from the transcript) what the last few commands were — `history | tail` or the user's memory. Then look, in order:

1. **`git reflog`** — the flight recorder. Every position HEAD has held in this clone, even through resets and rebases. `git reflog show <branch>` for a specific branch. The lost commit is almost always here.
2. **`git stash list`** — work people forgot they stashed, or that a tool auto-stashed (`rebase --autostash`!).
3. **`git fsck --lost-found`** — dangling commits and blobs that no ref or reflog entry points to anymore (e.g. after a deleted branch whose reflog went with it). Inspect candidates with `git show <sha>`.
4. **The remote** — if it was ever pushed, `git fetch` and check `origin/<branch>`. For a force-push that overwrote a remote branch: the old tip is still in the *pusher's* reflog, and on GitHub it survives in the events API (`gh api repos/OWNER/REPO/events` shows the `before` sha of the push) and as `git fetch origin <old-sha>` often still works.
5. **Uncommitted work is the hard case.** Never-staged changes wiped by `checkout -- .`/`reset --hard` are genuinely unrecoverable from git — say so honestly, then check editor local history (VS Code Timeline, JetBrains Local History), which frequently saves the day.

Identify the exact sha(s) of the lost work and **show the user the evidence** (`git log --oneline -3 <sha>`, `git show --stat <sha>`) before touching anything.

## Recover: smallest safe operation that gets it back

- **Lost commits after reset/rebase:** `git branch recovered <sha>` — pin them to a name first, decide how to integrate second (merge/cherry-pick/reset). Pinning is zero-risk.
- **Botched rebase/merge:** `git reset --hard <pre-rebase-sha from reflog>` — only after the backup branch exists. `ORIG_HEAD` usually points there too.
- **Committed on the wrong branch:** pin the commit, `git checkout right-branch && git cherry-pick <sha>`, then move the wrong branch back: `git checkout wrong-branch && git reset --keep HEAD~1` (`--keep`, not `--hard` — it refuses rather than eats uncommitted changes).
- **Deleted branch:** `git branch <name> <sha>` from reflog/fsck.
- **Dropped stash:** `git fsck --unreachable | grep commit`, inspect, `git stash apply <sha>`.
- **Detached HEAD commits:** `git branch recovered <sha from reflog>`.

## Confirm, then clean up

Prove the rescue worked — show the recovered diff or run the tests — before deleting any `rescue-backup-*` branch. Leave the backups in place if there is any doubt; a stray branch costs nothing, a second loss costs trust.

Close with one sentence on prevention only if it's specific to what happened (e.g. "`git reset --keep` refuses instead of destroying next time"). No lectures — they just had a bad day.

## Boundaries

- Reflog is **per-clone**: it can't see commits made on another machine or CI. Say so instead of implying everything is always recoverable.
- If `gc` has run and the object is truly gone, say that plainly and pivot to editor history / remote copies / CI artifacts.
- Never force-push during a rescue unless the user explicitly asks to restore a remote branch, and confirm the exact sha with them first.
