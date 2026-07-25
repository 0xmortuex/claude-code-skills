#!/usr/bin/env python3
"""Validate every skill in this pack for structural consistency.

Checks, per skill under ``skills/<name>/SKILL.md``:

* the file exists and opens with a closed ``---`` YAML frontmatter block;
* ``name`` is present, kebab-case, and equals the directory name;
* ``description`` is present and within Claude's practical length band
  (a floor that rejects stub descriptions, and the 1024-char platform
  ceiling for skill descriptions);
* the body has a top-level ``# <name>`` heading matching the skill.

And two cross-file checks against ``README.md``:

* every skill directory is linked from the README, and
* every ``skills/<name>/SKILL.md`` link in the README resolves to a real
  skill directory.

No third-party dependencies -- the frontmatter is simple ``key: value``
lines, parsed directly. Exit status is 0 when everything passes and 1
otherwise, with one line per problem. Intended for local use and CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
DESCRIPTION_MIN = 40
DESCRIPTION_MAX = 1024
README_LINK = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    """Return (fields, body) for a leading ``---`` block, or None if absent."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            fields: dict[str, str] = {}
            for line in lines[1:index]:
                if ":" in line and not line.startswith((" ", "\t")):
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
            body = "\n".join(lines[index + 1:])
            return fields, body
    return None


def validate_skill(skill_dir: Path, problems: list[str]) -> None:
    name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        problems.append(f"{name}: missing SKILL.md")
        return
    parsed = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
    if parsed is None:
        problems.append(f"{name}: SKILL.md has no closed '---' frontmatter block")
        return
    fields, body = parsed

    declared = fields.get("name")
    if declared is None:
        problems.append(f"{name}: frontmatter has no 'name'")
    elif declared != name:
        problems.append(
            f"{name}: frontmatter name '{declared}' does not match directory")
    elif not NAME_PATTERN.match(declared):
        problems.append(f"{name}: name '{declared}' is not kebab-case")

    description = fields.get("description")
    if description is None:
        problems.append(f"{name}: frontmatter has no 'description'")
    elif len(description) < DESCRIPTION_MIN:
        problems.append(
            f"{name}: description is only {len(description)} chars "
            f"(min {DESCRIPTION_MIN})")
    elif len(description) > DESCRIPTION_MAX:
        problems.append(
            f"{name}: description is {len(description)} chars "
            f"(max {DESCRIPTION_MAX})")

    if not re.search(rf"^#\s+{re.escape(name)}\s*$", body, re.MULTILINE):
        problems.append(f"{name}: body has no '# {name}' top-level heading")


def validate_readme(skill_names: set[str], problems: list[str]) -> None:
    if not README.is_file():
        problems.append("README.md is missing")
        return
    linked = set(README_LINK.findall(README.read_text(encoding="utf-8")))
    for missing in sorted(skill_names - linked):
        problems.append(f"README.md does not link skill '{missing}'")
    for dangling in sorted(linked - skill_names):
        problems.append(
            f"README.md links 'skills/{dangling}/SKILL.md' but no such skill exists")


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"error: no skills directory at {SKILLS_DIR}", file=sys.stderr)
        return 1
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("error: skills directory is empty", file=sys.stderr)
        return 1

    problems: list[str] = []
    for skill_dir in skill_dirs:
        validate_skill(skill_dir, problems)
    validate_readme({p.name for p in skill_dirs}, problems)

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"\n{len(problems)} problem(s) across {len(skill_dirs)} skill(s).")
        return 1

    print(f"OK: {len(skill_dirs)} skills valid and consistent with README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
