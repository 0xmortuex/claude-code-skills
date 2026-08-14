# portability-audit — example

**Trigger:**

> a Windows user filed a bug: `reportgen build` dies with "'rm' is not
> recognized as an internal or external command". we've never tested this
> tool outside our own Macs/Linux boxes. can you make it actually
> cross-platform, not just patch this one crash?

**Response shape:**

Claude doesn't patch the one crash — it sweeps the whole tool against the
hazard checklist in order, per the skill's "this is a sweep with a
checklist, not detective work":

```
Sweeping reportgen/ and scripts/ for the six hazard classes:

1. Shelling out to platform-specific commands
   reportgen/build.py:22    os.system(f"rm -rf {out_dir}")
   reportgen/build.py:35    subprocess.run(f"mkdir -p {cache_dir}", shell=True)
   scripts/docker-entrypoint.sh:8   rm -rf /app/tmp/*

2. Path construction and comparison
   reportgen/paths.py:14    cache_dir = base + "/" + "reportgen" + "/" + "cache"
   reportgen/paths.py:19    tmp_root = os.environ["HOME"] + "/.reportgen"

3. CRLF / line endings — none found (report is JSON, not line-parsed)

4. Filename legality
   reportgen/cache.py:41    write_cache(f"{report_name}.aux.json")
   # report_name is user-supplied; "aux" anywhere in a Windows filename
   # (even mid-name) is fine — only a bare reserved stem before the
   # extension is illegal. Re-checking: this one's actually safe, dropping it.

5. Process & runtime semantics
   reportgen/build.py:51    signal.signal(signal.SIGKILL, cleanup)
   # SIGKILL can't be caught on any platform, POSIX or Windows — this
   # line is dead code everywhere, not a portability bug specifically.
   # Flagging separately, not counting it as a Windows finding.

6. CI — no Windows job in .github/workflows/ci.yml today
```

It verifies each hit in context before reporting it as real, per the
skill's "a `rm -rf` inside an already-Linux-only Docker script is not a
finding; flagging it erodes trust in the real ones" — and drops two
candidates that didn't hold up:

```
scripts/docker-entrypoint.sh:8 — runs inside the tool's own Dockerfile
(FROM python:3.12-slim), never on a bare Windows host. Not a finding.

reportgen/cache.py:41 — re-checked against the actual Windows reserved-name
rule (bare stem AUX/CON/NUL/... before the extension, not a substring).
"report.aux.json" is legal. Not a finding.

Real count: 4 (2 shell-outs, 2 path-construction), plus the CI gap.
```

Fixes are mechanical, matching the "prefer the stdlib replacement over a
Windows-conditional" rule — no `if platform.system() == "Windows"` branches:

```python
# reportgen/build.py:22
- os.system(f"rm -rf {out_dir}")
+ shutil.rmtree(out_dir, ignore_errors=True)

# reportgen/build.py:35
- subprocess.run(f"mkdir -p {cache_dir}", shell=True)
+ os.makedirs(cache_dir, exist_ok=True)

# reportgen/paths.py:14
- cache_dir = base + "/" + "reportgen" + "/" + "cache"
+ cache_dir = Path(base) / "reportgen" / "cache"

# reportgen/paths.py:19
- tmp_root = os.environ["HOME"] + "/.reportgen"
+ tmp_root = Path.home() / ".reportgen"
  # os.environ["HOME"] raises KeyError on Windows (unset by default);
  # Path.home() resolves USERPROFILE there instead.
```

It closes with the CI-matrix recommendation the skill treats as the
lasting fix, not an optional nice-to-have:

```
None of these four fixes are provable from here — I can't run a Windows
box in this session. What proves it is CI. Recommending an addition to
.github/workflows/ci.yml:

  strategy:
    matrix:
      os: [ubuntu-latest, windows-latest]

running the existing test suite on both. Without this, the next
os.system() or "/" join lands the same way and nobody notices until the
next Windows user does.
```

## Verdict: 4 real hazards fixed (2 shell-outs → stdlib calls, 2 path
joins → `pathlib`), 2 candidates checked and correctly dropped (the Docker
script's `rm -rf` and the `.aux.json` filename), 1 unrelated dead-code line
flagged separately rather than folded into the count, and a `windows-latest`
CI job proposed since nothing here was actually run on Windows to confirm.
