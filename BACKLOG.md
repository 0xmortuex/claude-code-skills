# Backlog

Real, finishable improvements — the daily agent picks ONE and ships it end-to-end.
Rules: check items off when done, add follow-ups you discover, never do two at once.
The pack's bar for NEW skills: the problem must be real and verified uncovered by
prominent existing skills (research first, write second) — see README.

## Pack quality
- [ ] `examples/` directory: one short real transcript per skill showing the trigger firing and the output shape (start with git-rescue and migration-guard)
- [ ] CONTRIBUTING.md: the novelty-check bar, the SKILL.md house style (pushy description, "why" in the body, boundaries section), and how to test a skill locally
- [ ] Frontmatter validator script (`tools/validate.py`: name matches dir, description length sane, required sections present) + CI workflow running it
- [ ] README: add a "which skill do I want?" decision table mapping symptoms → skill

## Skill improvements
- [ ] ship-it: add a monorepo note (run checks only for affected packages; how to detect the workspace layout)
- [ ] env-detective: add a worked end-to-end example (CI log → delta table → binary search → fix)
- [ ] devlog: support a weekly rollup entry (`devlog week`) summarizing the week's dailies
