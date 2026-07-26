# Contributing

Thanks for considering adding to the pack. This file covers the bar for a new
skill, the house style every `SKILL.md` follows, and how to test one before
you open a PR.

## The novelty bar

Before writing a skill, research first. A new skill needs a problem that is
**real** (you or someone you know actually hit it) and **verified uncovered**
by prominent existing skills — check:

- the skills already in this pack (`skills/`, and the table in `README.md`)
- Anthropic's official skill guidance and any bundled/example skills
- well-known community packs and marketplaces (superpowers, awesome-lists,
  the Claude Code plugin marketplace)

If an existing skill already covers the trigger — even partially — extend
that skill instead of adding a near-duplicate. Candidates this pack has
already rejected as covered elsewhere: commit splitting, flaky-test fixing,
session handoffs, concurrency audits, license compliance. If your idea
overlaps with one of those, it needs a genuinely different angle to earn a
slot, not just a different name.

Write down in the PR description *what you checked* and why it's not already
covered — that's the research-first part, and reviewers will ask if it's
missing.

## `SKILL.md` house style

Every skill in this pack follows the same shape. Use `skills/git-rescue/SKILL.md`
or `skills/migration-guard/SKILL.md` as reference while you write.

**Frontmatter** (closed `---` block at the top of the file):

```yaml
---
name: your-skill-name
description: A pushy, trigger-rich description...
---
```

- `name` is kebab-case and matches the skill's directory name exactly.
- `description` is the single most important sentence you'll write. It has
  two jobs: state what the skill does, and give Claude concrete trigger
  phrases so it reaches for the skill at the right moment ("use this the
  moment the user says X, Y, or Z"). Vague descriptions ("helps with
  testing") don't trigger reliably — pack in the language a user would
  actually type. Keep it under 1024 characters; anything under ~40 reads as
  a stub and will fail validation.

**Body:**

- Open with a top-level `# your-skill-name` heading matching `name` exactly.
- Lead with the *why*, not a step list. Explain the reasoning a competent
  engineer would use — what makes this hard, what the common mistake is,
  why the naive approach fails — before or alongside the steps. A skill
  that only lists steps makes Claude follow them by rote on repos where they
  don't quite fit; a skill that explains the reasoning lets Claude adapt.
- Be honest by design: if the skill's job includes reporting results (a
  review, an audit, a diagnosis), tell it to report only what it can prove,
  not a wall of maybes.
- End with a **Boundaries** section: the cases this skill can't handle,
  where it should say so plainly instead of guessing, and any hard "never
  do X" rules. See `git-rescue`'s Boundaries section for the pattern — it
  says outright that reflog is per-clone and can't see other machines'
  commits, rather than implying full recovery is always possible.

## Testing a skill locally

1. Copy your skill directory into a test project's `.claude/skills/` (or
   `~/.claude/skills/` for a global test), matching the Install steps in
   `README.md`.
2. Start (or restart) Claude Code and run `/skills` to confirm it loaded.
3. Try the natural-language triggers from your own `description` — not just
   `/your-skill-name` — since the description's trigger phrases are what
   real usage depends on. Confirm it fires when it should and stays quiet
   on unrelated requests.
4. Run it against a real (or realistic) repo state, not a toy example — the
   grounded-not-guessing bar means it should read actual files/commands/output
   rather than inventing plausible-sounding details.
5. From the repo root, run `python tools/validate.py` — it checks frontmatter
   shape, naming, description length, the matching H1, and that your skill
   is linked from `README.md`'s table with a resolving link. It must print
   `OK` and exit 0 before you open a PR.
6. Add a row to the skills table in `README.md` (skill, what it does,
   triggers on) — the validator will fail the build if you forget.

## Opening the PR

- One skill per PR, unless you're fixing something across several.
- Describe what you checked for the novelty bar (see above).
- Make sure `python tools/validate.py` passes — CI runs it on every PR.
- If you're improving an existing skill rather than adding one, explain the
  concrete gap you hit (not a style preference) — see the "Skill
  improvements" bar in `BACKLOG.md`.
