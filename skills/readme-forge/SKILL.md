---
name: readme-forge
description: Write or overhaul a project's README by reading the actual codebase — the real entry points, dependencies, scripts, and config — not by guessing from the project name. Use this whenever the user asks to create, write, improve, rewrite, or "make a proper" README, wants better documentation for a repo, is preparing a project to be public or shared, or says their README is thin/outdated/embarrassing. Also use when someone wants their GitHub project to look more professional or get more attention, since the README is the first thing visitors judge.
---

# readme-forge

A README is the single highest-leverage file in a repo: it's what a visitor reads before deciding whether to try, star, or contribute. Most READMEs fail not because they're badly written but because they're *ungrounded* — written from a vague idea of the project instead of what the code actually does. Your job is to write one that's accurate because you read the source, and compelling because you led with why anyone should care.

## The method: read first, write second

Never draft a README from the project name and a guess. Investigate, then write.

### 1. Learn what the project actually is

- **Entry points:** `main`, `index`, `cli`, `app`, `server` — what runs when you run it?
- **Manifest:** `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` — name, description, scripts, dependencies, binaries, version.
- **How it's run and built:** the real commands from scripts, `Makefile`, `Dockerfile`, CI workflows. Use *these*, not invented ones — a README whose install command doesn't work is worse than no README.
- **Config & env:** `.env.example`, config files — what does a user have to set up?
- **Existing docs:** an old README, `docs/`, code comments, tests (tests reveal intended usage better than anything).

If something's ambiguous (license, the one-line purpose, the target audience), ask the user one or two sharp questions rather than inventing an answer.

### 2. Find the hook

Before writing a word of structure, answer: **what does this do, for whom, and why is it better than the alternative they'd otherwise use?** That sentence is the top of the README and the hardest part. Make it concrete and honest — no "blazingly fast, revolutionary" filler. A specific claim ("recon for a domain — DNS, WHOIS, SSL, subdomains — in one dashboard, no API keys") beats a vague superlative every time.

## Structure

Adapt to the project — a library, a CLI, and a web app need different emphases — but this order works because it matches the questions a visitor asks, in order:

```
# Project Name

> One sharp sentence: what it is and who it's for.

[badges: build status, version, license — only real ones]

A short paragraph (2-4 sentences) expanding the hook: the problem it solves,
what makes it worth using. A screenshot or GIF here if it's visual — for many
projects this is what earns the star, so include a placeholder and tell the
user to add one if you can't generate it.

## Features / What it does
- Concrete capabilities, phrased as user value, not implementation trivia.

## Install
Copy-paste commands that actually work (the ones you found in the repo).

## Usage / Quickstart
The smallest real example that produces a visible result. Show input AND output.

## Configuration        (only if there is any)
Env vars / config options, as a table.

## How it works          (optional — great for technical/from-scratch projects)
A short architecture note or diagram. This section is what makes a project
look serious to other engineers.

## Contributing / Development   (if it's meant to accept contributions)

## License
```

## Principles that separate good from generic

- **Show, don't assert.** A working example with real output convinces; "easy to use" doesn't.
- **Lead with value, defer the internals.** A visitor wants "what can this do for me" before "how is it architected." Keep the hook and quickstart above the fold.
- **Every command must be real.** Pulled from the repo, and correct. This is the fastest way to lose a reader's trust.
- **Match the project's ambition.** A weekend script gets a tight, honest README; a serious tool earns a fuller one with architecture and screenshots. Don't inflate a small thing or undersell a substantial one.
- **Prompt for the visual.** If the project has any UI or visible output and you can't produce a screenshot/GIF yourself, leave a clearly-marked placeholder and tell the user exactly what to capture — it's often the highest-impact element on the page.
- **Write like a person.** Skip the corporate-brochure tone and the emoji-per-heading reflex. Clear, direct, a little bit of personality.

## Output

Write the README to `README.md` (or update the existing one in place, preserving anything still accurate — don't blow away good content). After writing, tell the user in one or two lines what you based it on and flag anything you had to guess or leave as a placeholder, so they can verify the parts you couldn't.
