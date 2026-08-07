# changelog — example

**Trigger:**

> we're cutting v2.3.0 today, can you write the changelog? last tag was v2.2.0

**Response shape:**

Claude finds the boundary itself instead of asking the user to paste commits,
then reads past thin messages to what actually changed:

```
git describe --tags --abbrev=0        # v2.2.0
git log v2.2.0..HEAD --oneline

a1e4f2c feat(export): add CSV export for order history
9bb7c10 fix(auth): session no longer drops after 30min idle
5d0e881 fix csv escaping
c2f9a03 chore: bump lodash to 4.17.21
7ee1b45 wip
0a4d9de feat(export): CSV export polish + tests
41cb220 fix(api): tighten path validation on /files/:name download
b3aa901 chore: typo in comment
88f0c11 feat!: config.timeout now takes milliseconds, not seconds
```

It checks for an existing `CHANGELOG.md` to match format, finds one in
Keep a Changelog style, and drafts the new entry — collapsing the two
CSV-export commits into one feature, dropping the noise, and pulling the
path-validation fix's real story out of a message that undersells it:

```
## [2.3.0] - 2026-08-07

### Added
- CSV export for order history (Settings → Export).

### Fixed
- Login sessions no longer drop after 30 minutes of inactivity.
- CSV export now escapes commas and quotes inside quoted fields.

### Security
- Patched a path-traversal in the `/files/:name` download endpoint — a
  crafted filename could previously escape the upload directory and read
  arbitrary files on the server.

### Changed
- **BREAKING:** `config.timeout` is now milliseconds, not seconds.
  Multiply existing config values by 1000 before upgrading.
```

Dropped from the log, and named as dropped rather than silently omitted:
`chore: bump lodash to 4.17.21` (no user-facing effect), `wip` and
`fix csv escaping` (folded into the CSV entries above), `chore: typo in
comment`.

It prepends this above the existing `[2.2.0]` entry in `CHANGELOG.md`
(newest on top) rather than replacing the file, and closes with what it
used and what a human should double check before publishing:

```
Used range v2.2.0..HEAD (9 commits), dated 2026-08-07. Flagged one
BREAKING change (config.timeout units) — confirm the release notes
call this out prominently, since it silently changes behavior for
anyone who upgrades without reading them.
```
