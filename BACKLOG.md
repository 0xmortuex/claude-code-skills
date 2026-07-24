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

## Future skills (research-verified novel, 2026-07-24 sweep — sketches in the item)
- [ ] `clean-exit` — graceful-shutdown audit: SIGTERM sequence (readiness-fail → stop accept → drain w/ deadline → flush → close → exit 0), k8s preStop/grace-period interplay, worker checkpointing, verify by SIGTERM-under-load. No existing skill covers app-level shutdown code.
- [ ] `atomic-io` — crash-safe local file state: find truncate-then-write of state files, fix with temp-file → fsync → rename (`os.replace`), single-writer locks, validate-on-read recovery, Windows AV/EPERM retries. No existing skill; even major CLIs ship this bug.
- [ ] `tombstone` — evidence-based removal of "unused" surface: classify deletion risk (intra-repo vs externally reachable), gather prod evidence (access logs, pg_stat, tombstone counters), instrument-and-soak covering monthly jobs, then delete reversibly. Static dead-code skills exist; the prod-evidence workflow does not. Scope OUT feature-flag cleanup (covered elsewhere).

## Skill improvements
- [ ] ship-it: add a monorepo note (run checks only for affected packages; how to detect the workspace layout)
- [ ] env-detective: add a worked end-to-end example (CI log → delta table → binary search → fix)
- [ ] devlog: support a weekly rollup entry (`devlog week`) summarizing the week's dailies
