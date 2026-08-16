# readme-forge — example

**Trigger:**

> can you write a proper README for this? it's just "TODO" right now and I
> want to put the repo up publicly

**Response shape:**

Claude reads the repo before writing anything — no drafting from the
project name.

```
cat pyproject.toml
```
```
[project]
name = "reflowcli"
dependencies = ["click", "requests", "rich"]

[project.scripts]
reflow = "reflowcli.cli:main"
```

```
cat reflowcli/cli.py | head -40
```
Two subcommands turn up: `reflow watch <run-id>` (poll a GitHub Actions run
and print live job status with `rich`) and `reflow retry <run-id>` (re-run
just the failed jobs via the Actions API, not the whole workflow).

```
cat .env.example
```
```
GITHUB_TOKEN=
```
— a token is required; no other config.

```
cat README.md
```
```
# reflowcli
TODO
```
Nothing usable there. Checking for a license and CI:
```
ls LICENSE* .github/workflows/
```
No `LICENSE` file exists, and `.github/workflows/ci.yml` runs `pytest` on
push — a real badge-worthy check, not an invented one.

`tests/test_retry.py` shows the actual call shape: `reflow retry 41928321`
against a run with 2 failed / 6 total jobs, retrying only the 2.

**The hook:** not "a GitHub Actions CLI tool" — the specific value is
*re-running only the failed jobs from the terminal*, skipping the Actions
UI click-through. That's the line that opens the README.

**Write** (`README.md`, replacing the `TODO` placeholder):

```markdown
# reflowcli

> Retry just the failed jobs on a GitHub Actions run — from the terminal, no UI click-through.

![CI](https://github.com/<owner>/reflowcli/actions/workflows/ci.yml/badge.svg)

Re-running a whole workflow to retry two flaky jobs out of eight wastes
minutes and CI minutes both. `reflowcli` talks to the Actions API directly
and re-runs only the jobs that failed.

## Install

    pip install reflowcli

## Usage

    export GITHUB_TOKEN=ghp_...
    reflow watch 41928321      # live job status for a run
    reflow retry 41928321      # re-run only its failed jobs

    Retrying 2 of 6 jobs on run 41928321...
    ✓ lint          queued
    ✓ test (3.12)   queued

## Configuration

| Variable       | Required | Purpose                          |
|----------------|----------|-----------------------------------|
| `GITHUB_TOKEN` | yes      | Actions API access (repo scope)  |

## Development

    pip install -e ".[dev]"
    pytest

## License

*(no LICENSE file found in the repo — add one and this section will name it)*
```

**Wrap-up to the user:** two lines — README is based on `pyproject.toml`,
`cli.py`, `.env.example`, and the existing `ci.yml`/tests; flagged that
there's no `LICENSE` file so that section is left as a placeholder rather
than guessed, and there's no screenshot/GIF of the `rich` terminal output
yet, which is worth adding since the live-status view is the most visual
part of the tool.
