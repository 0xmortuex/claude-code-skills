---
name: atomic-io
description: Find and fix non-atomic writes to local state files — config, checkpoints, caches, lockfiles — that leave a truncated or corrupted file on disk after a crash, `kill -9`, OOM-kill, power loss, or full disk. Use when the user reports a config/state file that came back empty or unparseable after a crash or forced restart, when reviewing or writing any code that opens a path in write mode (`open(path, 'w')`, `json.dump`, `yaml.safe_dump`, `pickle.dump`, `torch.save`, `.write_text()`) to persist application state a process reads back later, or when the user asks "how do I save this safely" / "make this crash-safe" / "atomic write". Covers the temp-file-fsync-rename fix, directory fsync, single-writer locking, validate-on-read recovery, and Windows-specific EPERM/antivirus-lock retries on rename.
---

# atomic-io

`open(path, 'w')` truncates the file to zero length the instant it's called, before a single byte of new content lands. Every line between that open and the matching close is a window where a crash, `kill -9`, an OOM-kill, a container eviction, or a plain power loss leaves the file in whatever state it was in when the process died — often empty, sometimes truncated mid-record. This is strictly worse than not writing at all: the previous good version is gone, and the new one never fully arrived. It's the single most common way "unused" config files, job checkpoints, and local caches turn into 3am incidents, and it's easy to miss in review because the code *looks* fine — it reads back correctly in every test that doesn't inject a crash mid-write.

The fix is one well-known pattern, not a debate: write to a temp file in the same directory, flush and `fsync` it, then atomically rename it over the target (`os.replace` on POSIX and Windows both — never `os.rename` on Windows, which raises if the destination exists). The rename is what makes this safe: a reader always sees either the fully-old or fully-new file, never a partial one, because rename swaps a directory entry rather than mutating file contents. Skipping the `fsync` before the rename is a common half-fix — without it, the rename can be durable while the data it points to isn't, so a crash right after can expose zero-length or garbage content through the new name.

## What to check for

**The write path.** Grep for direct writes to a path the same process (or another one) reads back as state: `open(cfg_path, 'w')`, `json.dump(data, open(...))`, `df.to_csv(path)`, `yaml.safe_dump(..., open(path, 'w'))`, checkpoint/`save()`/`persist()` methods. If the final path is opened for writing directly — no temp name anywhere nearby — it's non-atomic. One-shot output a human reads once (a report, a log line) doesn't need this; a file a program parses on its next run does.

**The full sequence, not just "uses a temp file."** A correct fix has all four pieces, and partial fixes are common:
1. Temp file in the *same directory* as the target (a different directory, or worse a different filesystem/mount, makes the rename non-atomic or turns it into a copy).
2. `f.flush()` then `os.fsync(f.fileno())` before close — without this the "atomic" rename can still expose data that was never durably written.
3. `os.replace(tmp, path)` (or the language equivalent — Node's `fs.renameSync`, Go's `os.Rename`, Rust's `std::fs::rename`) — not a manual delete-then-rename, which reopens the truncation window.
4. On Linux, an `fsync` on the *directory* file descriptor after the rename, if the write must survive a host crash (not just a process crash) — the rename itself is a directory-metadata change and needs its own sync to be crash-durable on most Linux filesystems. Skip this one honestly for containers/cloud VMs where the whole disk is expected to survive a process restart and the extra syscall isn't worth it — but say that's the tradeoff being made, don't skip it silently.

**Concurrent writers.** Atomic rename guarantees a reader never sees a torn file; it does not guarantee two writers don't stomp each other — the second rename just wins, silently discarding the first writer's update. If more than one process or thread can save the same state file, that needs a single-writer lock (advisory file lock — `fcntl.flock` on POSIX, `msvcrt.locking` or a lockfile-with-PID convention on Windows — or route all writes through one owning process/actor) in addition to the atomic-write pattern, not instead of it.

**Validate-on-read.** Atomic writes protect against torn files, not against a bug that atomically wrote bad data, or a crash during a *previous*, non-atomic version of this code leaving one corrupt file that a later atomic write hasn't overwritten yet. The read path should parse-and-validate (schema check, checksum, magic-number/version field) before trusting the file, and have a defined fallback — previous-good backup, safe default, or a loud failure — rather than propagating a `JSONDecodeError` up through unrelated code paths. Keeping the previous version as `path.bak` (write new to temp, rename old target to `.bak`, rename temp to target) buys a recovery path almost for free.

**Windows specifics.** `os.replace`/`MoveFileEx` on Windows can fail with `PermissionError`/`ERROR_ACCESS_DENIED` when antivirus, a search indexer, or another process has the target transiently open — this is common enough in practice to need a bounded retry with backoff (a handful of attempts over ~100ms–1s), not a crash on the first transient failure. This is a real platform difference, not paranoia: the same code is reliable on Linux and flaky on Windows without it.

## Report

Cite the actual read-back failure mode, not just "not atomic":

```
config/settings.json: `open(path, 'w')` truncates before json.dump writes —
a crash mid-dump (observed: OOM-kill during a large settings migration)
leaves a 0-byte file; next startup's json.load raises and the process
won't boot until the file is hand-restored.
  fix: write to settings.json.tmp in the same dir, fsync, os.replace.

checkpoint.pt: torch.save writes the final path directly; two training
workers can both checkpoint at once (no lock) — last rename wins, silently
dropping whichever worker's epoch was ahead. Add a lock or route saves
through the coordinator process.
```

## Boundaries

- This is for **local filesystem state a process reads back** — config, checkpoints, local caches, lockfiles, embedded-DB-adjacent files. Database durability (WAL, transactions, `fsync` policy) is the database engine's job, not this skill's.
- Network filesystems (NFS, SMB, most cloud "file" mounts) often don't give rename the same atomicity guarantee as a local disk — say so explicitly rather than applying the local-disk fix and calling it safe; the honest answer there is frequently "move this state into the database or object store instead."
- This skill fixes torn/corrupted files from interrupted writes. It does not solve merge conflicts between two writers with genuinely different updates to reconcile — that needs an actual concurrency design (locking, CRDTs, single-writer architecture), and this skill will say when that's the real problem instead of prescribing a bigger lock.
- Don't demand directory-fsync-after-rename ceremony for a dev-machine cache file where losing it just means a slower next run — scale the rigor to what a lost or corrupt file actually costs, and say plainly when it's being skipped and why.
