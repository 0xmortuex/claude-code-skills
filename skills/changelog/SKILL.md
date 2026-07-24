---
name: changelog
description: Turn git history since the last release into a human-readable changelog or release notes, grouped by type of change and written for the people who use the software, not the people who wrote it. Use this whenever the user is cutting a release, asks for release notes, a changelog, "what changed since the last version", wants to update CHANGELOG.md, or is tagging a version. Also use when someone needs to summarize a range of commits into something a user or stakeholder would read.
---

# changelog

A changelog is written for the reader who wants to know *"what does this release mean for me — what's new, what's fixed, what might break?"* — not for the author reviewing their own commits. The raw git log is the input, not the output. Your job is to translate developer-facing commit messages into user-facing notes: grouped, deduplicated, and phrased around impact.

## Gather the material

1. **Find the last release boundary.** The most recent tag is usually it: `git describe --tags --abbrev=0`, then `git log <lasttag>..HEAD`. If there are no tags, ask the user for the range (a date, a commit, "since v1.2") rather than dumping the entire history.
2. **Read the commits with their diffs when the message is thin.** A commit that says "fix stuff" needs you to look at what it changed. The message is a hint; the diff is the truth.
3. **Check for an existing `CHANGELOG.md`** and match its format, headings, and voice exactly. Consistency across releases matters more than any format you'd prefer.

## Group by what it means to a user

Organize under [Keep a Changelog](https://keepachangelog.com) categories — they map to the reader's actual questions:

- **Added** — new features and capabilities
- **Changed** — changes to existing behavior
- **Deprecated** — soon-to-be-removed features
- **Removed** — features taken out this release
- **Fixed** — bug fixes
- **Security** — vulnerability fixes (call these out; users need them to make patching decisions)

Omit empty categories. If the project uses Conventional Commits, the type prefix (`feat`/`fix`/…) maps cleanly onto these — but still read for meaning, since one commit can carry a fix and a behavior change.

## Write for the user, not the committer

This is the whole skill. Translate:

- **Drop the noise.** Merge commits, `wip`, `fix typo`, formatting-only changes, dependency bumps with no user impact — these don't belong in user-facing notes (a separate "Dependencies" or "Internal" section is fine if the project wants completeness).
- **Deduplicate.** Five commits building one feature become one entry describing the feature.
- **Phrase around impact.** Not "refactored the auth middleware" but "Fixed login sessions being dropped after 30 minutes." The reader cares about the effect, not the mechanism.
- **Flag breaking changes loudly.** Anything that changes an API, a config key, a default, or a migration requirement gets a **BREAKING** marker and a line on what the user must do. This is the single most important thing a changelog does — a surprised user is a broken deployment.
- **Credit and link where the project does.** If the repo references PRs/issues (`#123`) or contributors in its existing changelog, keep that convention.

## Output format

Default to Keep a Changelog style, matching an existing `CHANGELOG.md` if present:

```markdown
## [1.4.0] - 2026-07-24

### Added
- Dark mode, toggled from Settings or with `Ctrl+Shift+L`.

### Fixed
- Login sessions no longer drop after 30 minutes of inactivity.
- CSV export now escapes commas inside quoted fields.

### Security
- Patched a path-traversal in the file-download endpoint (a crafted
  filename could read files outside the upload directory).

### Changed
- **BREAKING:** `config.timeout` is now milliseconds, not seconds.
  Multiply existing values by 1000.
```

Prepend the new entry to `CHANGELOG.md` (newest on top). If the user wants GitHub Release notes instead, offer a slightly punchier version with a one-line summary at the top and a "Full changelog" compare link. Ask which they want if it's ambiguous.

After writing, tell the user the version/date you used and anything you deliberately left out (noise) or flagged as breaking, so they can sanity-check before publishing.
