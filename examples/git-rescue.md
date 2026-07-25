# git-rescue — example

**Trigger:**

> omg I think I just destroyed 3 hours of work. I ran `git reset --hard` on the
> wrong branch and now `git status` shows nothing changed. please tell me this
> is recoverable

**Response shape:**

Claude does not run the reset again or try `checkout .` — it secures the
scene first, then diagnoses:

```
Before touching anything: pinning your current HEAD in case this rescue
needs its own rescue.

  git branch rescue-backup-1721900000

Now let's find the lost commits. Nothing is usually gone in git — reset
--hard unlinks commits from the branch pointer, it doesn't delete the
objects. Checking the reflog:

  git reflog show feature/payments-refactor

  a3f9c2e HEAD@{1}: commit: wire up refund retry logic
  b71e0aa HEAD@{2}: reset: moving to HEAD~3   <- this is the reset that "lost" your work
  ...
```

It shows the evidence before recovering — `git show --stat a3f9c2e` — then
proposes the smallest safe fix:

```
Found it: a3f9c2e has your refund retry work, 3 commits ahead of where you
are now. Recovering:

  git branch recovered a3f9c2e

That's zero-risk — it just names the commit, doesn't move anything yet.
Your work is at `recovered`. Want me to merge it into
feature/payments-refactor, or check it out directly?
```

It confirms the recovery (diff or tests) before offering to delete
`rescue-backup-1721900000`, and closes with one line of prevention specific
to what happened — no lecture.
