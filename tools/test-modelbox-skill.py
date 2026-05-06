#!/usr/bin/env python3
"""test-modelbox-skill.py — Validate generated skills/modelbox/ artifacts.

Usage:
    python3 tools/test-modelbox-skill.py [skills/modelbox/]

Checks:
    1. SKILL.md has all seven required sections (non-empty bodies)
    2. SKILL.md frontmatter parses (name + description present)
    3. Catalog rows <-> reference files are 1-to-1
    4. Every reference file has six required sections (non-empty bodies)
    5. Every TOML block in reference files parses cleanly
    6. Every generated file footer contains the pinned commit from the YAML
"""
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import]
    except ImportError:
        sys.exit("ERROR: Python 3.11+ required, or: pip install tomli")

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml")

REQUIRED_SKILL_SECTIONS = [
    "## When to use",
    "## Core mental model",
    "## Catalog",
    "## Virtual-type matrix",
    "## Known-good pipelines",
    "## Authoring gotchas",
    "## Pointers",
]

REQUIRED_REF_SECTIONS = [
    "## Purpose",
    "## TOML config",
    "## Ports",
    "## Config keys",
    "## Notes / gotchas",
    "## Upstream source",
]


def section_body(text: str, heading: str) -> str:
    """Return the text between `heading` and the next `## ` heading (or EOF)."""
    idx = text.find(heading)
    if idx == -1:
        return ""
    rest = text[idx + len(heading):]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def check_sections(text: str, required: list[str], label: str) -> list[str]:
    errors: list[str] = []
    for sec in required:
        if sec not in text:
            errors.append(f"{label}: missing section '{sec}'")
        elif not section_body(text, sec).strip():
            errors.append(f"{label}: section '{sec}' is empty")
    return errors


def check_frontmatter(skill_text: str) -> list[str]:
    errors: list[str] = []
    if not skill_text.startswith("---"):
        errors.append("SKILL.md: does not start with YAML frontmatter '---'")
        return errors
    end = skill_text.find("---", 3)
    if end == -1:
        errors.append("SKILL.md: frontmatter has no closing '---'")
        return errors
    fm_str = skill_text[3:end].strip()
    try:
        fm = yaml.safe_load(fm_str)
        if not fm or not fm.get("name"):
            errors.append("SKILL.md: frontmatter missing 'name'")
        if not fm or not fm.get("description"):
            errors.append("SKILL.md: frontmatter missing 'description'")
    except yaml.YAMLError as exc:
        errors.append(f"SKILL.md: frontmatter YAML error: {exc}")
    return errors


def extract_catalog_refs(skill_text: str) -> set[str]:
    """Return set of flowunit names referenced in the Catalog section."""
    return set(re.findall(r"\(references/(\w+)\.md\)", skill_text))


def toml_blocks(text: str) -> list[str]:
    return re.findall(r"```toml\n(.*?)```", text, re.DOTALL)


def check_toml(block: str, label: str) -> list[str]:
    try:
        tomllib.loads(block)
        return []
    except Exception as exc:
        return [f"{label}: TOML parse error: {exc}"]


def check_pin(text: str, commit: str, label: str) -> list[str]:
    short = commit[:12]
    if commit not in text and short not in text:
        return [f"{label}: missing pin record (commit {short})"]
    return []


def load_allowlist_commit(tools_dir: Path) -> str:
    p = tools_dir / "modelbox-flowunits.yml"
    if not p.exists():
        return ""
    with open(p) as f:
        data = yaml.safe_load(f)
    return str(data.get("modelbox_commit", ""))


def main() -> None:
    skill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("skills/modelbox")
    tools_dir = Path(__file__).parent

    errors: list[str] = []

    # ── Check skill_dir exists ──────────────────────────────────────────────
    if not skill_dir.is_dir():
        print(f"FAIL: {skill_dir} does not exist")
        sys.exit(1)

    skill_path = skill_dir / "SKILL.md"
    refs_dir = skill_dir / "references"

    if not skill_path.exists():
        print(f"FAIL: {skill_path} does not exist")
        sys.exit(1)

    skill_text = skill_path.read_text()

    # ── Load pinned commit ──────────────────────────────────────────────────
    expected_commit = load_allowlist_commit(tools_dir)

    # ── Check 1: SKILL.md seven sections ───────────────────────────────────
    errors += check_sections(skill_text, REQUIRED_SKILL_SECTIONS, "SKILL.md")

    # ── Check 2: Frontmatter ────────────────────────────────────────────────
    errors += check_frontmatter(skill_text)

    # ── Check 3: Catalog <-> reference parity ────────────────────────────────
    catalog_refs = extract_catalog_refs(skill_text)
    existing_refs = {p.stem for p in refs_dir.glob("*.md")} if refs_dir.is_dir() else set()

    for name in sorted(catalog_refs - existing_refs):
        errors.append(f"Catalog references '{name}' but references/{name}.md not found")
    for name in sorted(existing_refs - catalog_refs):
        errors.append(f"references/{name}.md exists but is not referenced in Catalog")

    # ── Check 4 + 5 + 6: Per-reference-file checks ─────────────────────────
    if refs_dir.is_dir():
        for ref_path in sorted(refs_dir.glob("*.md")):
            ref_text = ref_path.read_text()
            label = f"references/{ref_path.name}"

            # Six sections present and non-empty
            errors += check_sections(ref_text, REQUIRED_REF_SECTIONS, label)

            # TOML validity
            for block in toml_blocks(ref_text):
                errors += check_toml(block, label)

            # Pin record
            if expected_commit:
                errors += check_pin(ref_text, expected_commit, label)

    # ── Check 6: SKILL.md pin record ───────────────────────────────────────
    if expected_commit:
        errors += check_pin(skill_text, expected_commit, "SKILL.md")

    # ── Report ──────────────────────────────────────────────────────────────
    if errors:
        print(f"FAIL: {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        n_refs = len(existing_refs)
        print(f"OK: {n_refs} reference files, all checks passed (commit={expected_commit[:12]})")


if __name__ == "__main__":
    main()
