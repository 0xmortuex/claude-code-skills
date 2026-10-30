#!/usr/bin/env python3
"""Validate every skill in this pack for structural consistency.

Checks, per skill under ``skills/<name>/SKILL.md``:

* the file exists and opens with a closed ``---`` YAML frontmatter block;
* ``name`` is present, kebab-case, and equals the directory name;
* ``description`` is present and within Claude's practical length band
  (a floor that rejects stub descriptions, and the 1024-char platform
  ceiling for skill descriptions);
* the body has a top-level ``# <name>`` heading matching the skill; and
* the body ends with a ``## Boundaries`` section, per the house style in
  ``CONTRIBUTING.md`` (three skills -- changelog, codebase-tour,
  readme-forge -- were found missing one and fixed alongside this check).

Cross-file checks against ``README.md``:

* every skill directory is linked from the "## The skills" table, and
  every ``skills/<name>/SKILL.md`` link in that table resolves to a real
  skill directory; and
* the same, separately, for the "## Which skill do I want?" decision
  table -- a skill can be linked from the skills table but missing its own
  decision-table row (or vice versa), and the two were previously checked
  as one pooled set of links, which let either table drift out of sync
  with the skill list unnoticed.

And against the pack's convention that every skill has a worked example in
``examples/<name>.md``, linked from both ``examples/README.md`` and the main
``README.md``'s Examples section:

* every skill has an ``examples/<name>.md`` file,
* every such file is linked from ``examples/README.md``, and
* every such file is linked from ``README.md``'s Examples section
  (dangling links back to a nonexistent skill are flagged in both places).

And the recurring prose-drift class noted twice in ``BACKLOG.md`` (2026-09-20,
2026-10-28): ``README.md``'s intro and install-tip sentences state the pack's
size in words ("forty-two") or digits ("42-skill"), which silently goes stale
whenever a skill is added or removed because nothing re-derives it from the
actual skill count. ``validate_skill_count_mentions`` catches both forms.

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
EXAMPLES_DIR = ROOT / "examples"
EXAMPLES_README = EXAMPLES_DIR / "README.md"

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
DESCRIPTION_MIN = 40
DESCRIPTION_MAX = 1024
README_LINK = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")
README_EXAMPLE_LINK = re.compile(r"\(examples/([a-z0-9-]+)\.md\)")
EXAMPLES_README_LINK = re.compile(r"\(([a-z0-9-]+)\.md\)")

SKILLS_TABLE_HEADING = "## The skills"
DECISION_TABLE_HEADING = "## Which skill do I want?"

ONES_AND_TEENS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMBER_WORD = rf"(?:(?:{'|'.join(TENS)})(?:-(?:{'|'.join(ONES_AND_TEENS)}))?|(?:{'|'.join(ONES_AND_TEENS)}))"
# Only matched where it follows/precedes the exact phrasing the pack's two
# known skill-count mentions use, so this can't misfire on an unrelated
# number word ("one or two skills work best...") elsewhere in the prose.
SKILL_COUNT_WORD = re.compile(
    rf"\bcopying all ({_NUMBER_WORD}) at once\b|\b({_NUMBER_WORD}) that earn their place\b")
SKILL_COUNT_DIGIT = re.compile(r"\b(\d+)-skill\b")


def word_to_number(word: str) -> int:
    tens, _, ones = word.partition("-")
    if tens in TENS:
        return TENS[tens] + (ONES_AND_TEENS[ones] if ones else 0)
    return ONES_AND_TEENS[word]


def extract_section(text: str, heading: str) -> str | None:
    """Return the body between ``heading`` and the next top-level ``##``
    heading (or end of file), or None if ``heading`` isn't found."""
    start = text.find(heading)
    if start == -1:
        return None
    start += len(heading)
    next_heading = text.find("\n## ", start)
    return text[start:] if next_heading == -1 else text[start:next_heading]


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

    if not re.search(r"^##\s+Boundaries\s*$", body, re.MULTILINE):
        problems.append(f"{name}: body has no '## Boundaries' section")


def validate_readme_section(
    text: str, heading: str, skill_names: set[str], problems: list[str],
) -> None:
    section = extract_section(text, heading)
    if section is None:
        problems.append(f"README.md is missing the '{heading}' section")
        return
    linked = set(README_LINK.findall(section))
    for missing in sorted(skill_names - linked):
        problems.append(f"README.md '{heading}' section does not link skill '{missing}'")
    for dangling in sorted(linked - skill_names):
        problems.append(
            f"README.md '{heading}' section links 'skills/{dangling}/SKILL.md' "
            "but no such skill exists")


def validate_readme(skill_names: set[str], problems: list[str]) -> None:
    if not README.is_file():
        problems.append("README.md is missing")
        return
    text = README.read_text(encoding="utf-8")
    validate_readme_section(text, SKILLS_TABLE_HEADING, skill_names, problems)
    validate_readme_section(text, DECISION_TABLE_HEADING, skill_names, problems)


def validate_examples(skill_names: set[str], problems: list[str]) -> None:
    for name in sorted(skill_names):
        if not (EXAMPLES_DIR / f"{name}.md").is_file():
            problems.append(f"{name}: missing examples/{name}.md")

    existing = {
        p.stem for p in EXAMPLES_DIR.glob("*.md") if p.stem != "README"
    } if EXAMPLES_DIR.is_dir() else set()

    if not EXAMPLES_README.is_file():
        problems.append("examples/README.md is missing")
    else:
        linked = set(EXAMPLES_README_LINK.findall(
            EXAMPLES_README.read_text(encoding="utf-8")))
        for missing in sorted(existing - linked):
            problems.append(f"examples/README.md does not link '{missing}.md'")
        for dangling in sorted(linked - existing):
            problems.append(
                f"examples/README.md links '{dangling}.md' but no such file exists")

    if README.is_file():
        linked = set(README_EXAMPLE_LINK.findall(README.read_text(encoding="utf-8")))
        for missing in sorted(existing - linked):
            problems.append(
                f"README.md Examples section does not link 'examples/{missing}.md'")
        for dangling in sorted(linked - existing):
            problems.append(
                f"README.md links 'examples/{dangling}.md' but no such file exists")


def validate_skill_count_mentions(skill_count: int, problems: list[str]) -> None:
    if not README.is_file():
        return
    text = README.read_text(encoding="utf-8")

    for match in SKILL_COUNT_DIGIT.finditer(text):
        mentioned = int(match.group(1))
        if mentioned != skill_count:
            problems.append(
                f"README.md says '{match.group(0)}' but there are "
                f"{skill_count} skills")

    for match in SKILL_COUNT_WORD.finditer(text):
        word = match.group(1) or match.group(2)
        mentioned = word_to_number(word)
        if mentioned != skill_count:
            problems.append(
                f"README.md says '{word}' in '{match.group(0)}' but there "
                f"are {skill_count} skills")


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
    skill_names = {p.name for p in skill_dirs}
    validate_readme(skill_names, problems)
    validate_examples(skill_names, problems)
    validate_skill_count_mentions(len(skill_dirs), problems)

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"\n{len(problems)} problem(s) across {len(skill_dirs)} skill(s).")
        return 1

    print(f"OK: {len(skill_dirs)} skills valid and consistent with README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
