---
name: portability-audit
description: Audit a codebase for Windows/POSIX portability hazards and fix them — hardcoded path separators, CRLF/LF assumptions, shelling out to POSIX-only commands, reserved Windows filenames, case-sensitivity collisions, exec-bit and signal differences. Use when the user says "make this work on Windows/Linux/Mac", "a Windows user reported it's broken", "cross-platform", "why does this fail on Windows", or before publishing a CLI/dev tool to an audience that includes both platforms. Also use proactively when you notice platform-specific code in a project that claims to be cross-platform.
---

# portability-audit

Most "cross-platform" tools were only ever run on their author's platform, and the first user on the other one hits a wall of dumb, fixable breakage. The hazards are boring and finite — this is a *sweep with a checklist*, not detective work. Grep for each class, verify each hit is a real problem in context, fix it with the idiomatic construct.

## The hazard classes (sweep in this order — ordered by how often they actually break)

**1. Shelling out to platform-specific commands.**
Search subprocess/exec/spawn/system/backtick calls for `rm -rf`, `cp`, `mv`, `mkdir -p`, `which`, `grep`, `sed`, `awk`, `touch`, `cat`, `curl | sh`, `chmod`. Each has a stdlib replacement (`shutil.rmtree`, `fs.rm`, `os.makedirs`…) — prefer that over a Windows-conditional. Also: `sh -c` doesn't exist on Windows; `shell=True` means *different shells* on each platform, and `cmd.exe` quoting is its own hazard.

**2. Path construction and comparison.**
- Hardcoded separators: strings built with `'/'` mostly work on Windows APIs but break on display, comparison, and mixed input; `'\\'` breaks everywhere else. Use the path library (`pathlib`, `path.join`/`path.sep`, `filepath.Join`).
- Splitting on `'/'` or `':'` (PATH uses `';'` on Windows — use the stdlib's `os.pathsep`, `path.delimiter`).
- Comparing paths as strings: case-insensitive filesystems (Windows, default macOS) mean `C:\Foo` == `c:\foo`; normalize before comparing.
- Hardcoded `/tmp`, `~`, `$HOME` (use the platform temp/home APIs; `HOME` may be unset on Windows — `USERPROFILE`), hardcoded config paths (XDG vs `%APPDATA%` vs `~/Library`).

**3. CRLF / line endings.**
- Parsers that split on `'\n'` and then choke on the trailing `'\r'` from Windows input files or `git config core.autocrlf` checkouts. Trim `\r` or split on universal newlines.
- Tests comparing output against golden files byte-for-byte — fail on the other platform's checkout. Fix with a `.gitattributes` that pins the fixtures (`*.golden -text` or `text eol=lf`) — and recommend a `.gitattributes` (`* text=auto`) if the repo has none; it ends the whole class.
- Shell scripts with CRLF fail with cryptic `\r: command not found`; `#!/usr/bin/env bash` files must stay LF.

**4. Filename legality and length.**
- Reserved Windows names as files or directories: `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9` (with any extension!). Also illegal chars `< > : " | ? *`, and names ending in space or dot. These break *checkout itself* — the repo can't even be cloned on Windows. Check tracked files AND generated-file naming (a cache writing `aux.json` sinks you).
- Two tracked paths differing only by case = un-checkoutable on Windows/macOS: `git ls-files | sort -f | uniq -di`.
- MAX_PATH 260: deeply nested generated trees (node_modules-style) still bite tools that don't opt into long paths.

**5. Process & runtime semantics.**
- Signals: `SIGKILL`/`SIGTERM` handling, `os.fork`, `pty` — none exist on Windows; `process.kill()` semantics differ. Anything trapping SIGINT for cleanup needs a Windows story.
- Exec bit: `chmod +x` is meaningless on Windows checkouts and *lost* when a Windows user commits — script invocation should go through the interpreter (`python tool.py`, `npm exec`), not rely on `./tool.py`.
- Symlinks require elevation/dev-mode on Windows: repos with tracked symlinks or tools that create them need a copy fallback.
- File locking: Windows can't delete/rename an open file (the "EBUSY on cleanup in tests" classic — close handles before removing temp dirs).
- Text encoding: Windows defaults to a legacy codepage, not UTF-8 — any `open()` without an explicit encoding will eventually mangle someone's file (Python: pass `encoding="utf-8"` everywhere; check subprocess output decoding too).

**6. The CI blind spot.**
If the project claims cross-platform, the sweep's lasting fix is a CI matrix that proves it: add/extend a workflow with `windows-latest` (and `macos-latest` if relevant) at least building + running the test suite. A portability fix without a Windows CI job regresses within months.

## Report format

Group findings by class, each with `file:line`, why it breaks and *on which platform*, and the fix. Verify each grep hit in context first — a `rm -rf` inside an already-Linux-only Docker script is not a finding; flagging it erodes trust in the real ones. Fix mechanically fixable classes (paths, encodings, CRLF-safe parsing) directly when asked to fix, and end with the CI-matrix recommendation.

## Boundaries

- Don't rewrite platform-specific-by-design code (a systemd unit installer has no Windows story to fix); note it as explicitly out of scope instead.
- Untestable claims stay claims: unless you can run the other platform here, say "this should fix the Windows checkout — the CI matrix will prove it", not "Windows now works".
