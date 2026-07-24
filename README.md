# Claude Code Skills

**A small pack of Claude Code skills for the unglamorous work that actually ships software** — finalizing a change, writing a README people read, catching the security bug before it lands, cutting release notes, and getting oriented in a strange codebase.

Every skill here is written the way the [official skill guidance](https://docs.anthropic.com/en/docs/claude-code/skills) recommends: a pushy trigger description so Claude reaches for it at the right moment, and a body that explains the *why* so Claude does the task well instead of following steps by rote. No fluff, no 40-skill kitchen sink — five that earn their place.

## The skills

| Skill | What it does | Triggers on |
|-------|--------------|-------------|
| **[ship-it](skills/ship-it/SKILL.md)** | Runs the repo's own tests/lint/typecheck, fixes what breaks, writes a clean conventional commit + a review-ready diff summary | "commit this", "ship it", "is this ready to push" |
| **[readme-forge](skills/readme-forge/SKILL.md)** | Writes or overhauls a README by *reading the codebase* — real commands, real entry points, a hook that earns the star | "write a README", "improve my docs", "make this repo look professional" |
| **[security-sweep](skills/security-sweep/SKILL.md)** | Reviews the working diff for *exploitable* issues (injection, IDOR, secrets, SSRF…) and reports only findings with a concrete attack path | "security review", "any vulnerabilities here", "is this safe to ship" |
| **[changelog](skills/changelog/SKILL.md)** | Turns git history since the last tag into user-facing release notes, grouped by impact, breaking changes flagged | "release notes", "what changed since v1.2", "update the changelog" |
| **[codebase-tour](skills/codebase-tour/SKILL.md)** | Orients you in an unfamiliar repo by tracing a real code path and ending at "here's where you'd make your change" | "how does this work", "where do I start", "walk me through this codebase" |

## What makes these different

Most skill packs are thin wrappers — a description and three bullet points. These are written to actually change the quality of the output:

- **Grounded, not guessing.** `readme-forge` reads your `package.json` and entry points; `ship-it` discovers *your* test command instead of assuming one; `codebase-tour` traces real `file:line` paths. Skills that invent details erode trust fast.
- **Honest by design.** `security-sweep` reports only what it can prove is exploitable — a short list of real problems, not a wall of theoretical maybes. `ship-it` never dresses a failing test up as passing.
- **They explain the why.** Each skill tells Claude the reasoning behind the steps, which is what lets a capable model do the task well on *your* repo instead of pattern-matching a template.

## Install

Skills live in a `skills/` directory Claude Code reads. You have two options.

### Option A — per project (recommended to try)

Drop the ones you want into your project's `.claude/skills/`:

```bash
git clone https://github.com/0xmortuex/claude-code-skills
mkdir -p .claude/skills
cp -r claude-code-skills/skills/ship-it .claude/skills/
cp -r claude-code-skills/skills/readme-forge .claude/skills/
# ...or copy them all:
cp -r claude-code-skills/skills/* .claude/skills/
```

### Option B — globally, for every project

Copy them into your user skills directory so they're available everywhere:

```bash
git clone https://github.com/0xmortuex/claude-code-skills
mkdir -p ~/.claude/skills
cp -r claude-code-skills/skills/* ~/.claude/skills/
```

Either way, start (or restart) Claude Code and the skills are live. Claude invokes them automatically when your request matches — or call one by name, e.g. `/ship-it`. Run `/skills` to confirm they loaded.

> **Tip:** start with one or two. Skills work best when each one clearly owns its trigger; copying all five at once is fine, but if you only want the security review, just take `security-sweep`.

## Using them

You mostly don't have to do anything — the descriptions are tuned to trigger on natural phrasing:

```
you:  ok I think the payment refactor is done, get it ready to push
      → ship-it runs your tests, catches a type error, fixes it,
        stages a conventional commit, hands you a PR summary

you:  this endpoint takes a user id from the query string — anything scary here?
      → security-sweep traces it, finds the missing ownership check (IDOR),
        shows the exact request that reads another user's data, gives the fix

you:  just cloned this thing and I'm lost, where do I even start
      → codebase-tour finds main, traces one request through the layers,
        tells you which file to open for what you're trying to change
```

## Contributing

Got a skill that pulls its weight? Open a PR. The bar: it should be grounded (reads real state, doesn't guess), honest (no inflated output), and explain its reasoning so Claude does it well across many different repos — not just the one you tested on. One tight, well-triggered skill beats five vague ones.

## License

MIT — copy them, fork them, adapt them to your own workflow.
