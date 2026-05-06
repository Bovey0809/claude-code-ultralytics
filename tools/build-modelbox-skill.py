#!/usr/bin/env python3
"""build-modelbox-skill.py — Generate skills/modelbox/ from the upstream ModelBox repo.

Usage:
    python3 tools/build-modelbox-skill.py \
        --modelbox-repo /path/to/modelbox \
        --commit <full-sha> \
        --out skills/modelbox/

Requirements:
    pip install pyyaml tomli   # or Python 3.11+ (has tomllib built-in)
"""
import argparse
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


# ── Templates ──────────────────────────────────────────────────────────────

SKILL_FRONTMATTER = '''\
---
name: modelbox
description: Use when authoring or modifying a ModelBox graph (.toml), configuring a ModelBox flowunit, choosing the right flowunit for a step (video decode, inference, YOLO postprocess, drawing boxes, encoding output), or resolving "which flowunit handles X". Provides a curated index of flowunits used in YOLO + video pipelines, with TOML config schema, ports, device options, and known-good recipes.
---

# ModelBox Flowunit Index

'''

CATALOG_HEADER = """\
## Catalog

| Flowunit | Devices | Group | Use for | Reference |
|----------|---------|-------|---------|-----------|
"""

REFERENCE_TEMPLATE = """\
---
generated: true
modelbox_commit: {commit}
modelbox_commit_date: {commit_date}
---

# `{name}`

**Devices:** {devices}
**Group:** {group}

## Purpose

{purpose}

## TOML config (`{name}.toml`)

```toml
{toml_content}
```

## Ports

{ports_md}

## Config keys

{config_keys_md}

## Notes / gotchas

{notes_md}

## Upstream source

- `{source_dir}/`

---
_Generated from modelbox@{commit} ({commit_date})._
"""

SKILL_FOOTER = """\
---
_Generated from modelbox@{commit} ({commit_date}). Re-run `make modelbox-skill` to update._
"""


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def read_upstream_file(repo: Path, rel: str) -> str | None:
    if not rel:
        return None
    p = repo / rel
    return p.read_text() if p.exists() else None


def ports_to_md(ports: dict) -> str:
    lines: list[str] = []
    for inp in ports.get("inputs", []):
        lines.append(
            f"- **Input `{inp['name']}`:** {inp['type']} — {inp.get('notes', '')}"
        )
    for out in ports.get("outputs", []):
        lines.append(
            f"- **Output `{out['name']}`:** {out['type']} — {out.get('notes', '')}"
        )
    return "\n".join(lines) if lines else "- See upstream docs."


def config_keys_to_md(keys: list) -> str:
    if not keys:
        return "None required beyond `[base]`."
    rows = [
        "| Key | Required | Default | Notes |",
        "|-----|----------|---------|-------|",
    ]
    for k in keys:
        req = "yes" if k.get("required") else "no"
        default = str(k.get("default", "—"))
        notes = k.get("notes", "")
        rows.append(f"| `{k['key']}` | {req} | {default} | {notes} |")
    return "\n".join(rows)


def notes_to_md(notes: list) -> str:
    if not notes:
        return "- See upstream docs."
    return "\n".join(f"- {n}" for n in notes)


def extract_section(text: str, section_id: str) -> str:
    """Extract content after `<!-- SECTION: id -->` up to next marker or EOF."""
    pattern = rf"<!-- SECTION: {re.escape(section_id)} -->\n(.*?)(?=<!-- SECTION:|$)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        raise ValueError(f"Section '{section_id}' not found in prelude/recipes file")
    return m.group(1).strip()


def build_catalog_row(fu: dict) -> str:
    name = fu["name"]
    devices = ", ".join(fu["devices"]) if isinstance(fu["devices"], list) else fu["devices"]
    group = fu["group"]
    use_for = fu["use_for"]
    return f"| `{name}` | {devices} | {group} | {use_for} | [references/{name}.md](references/{name}.md) |"


def make_toml_content(fu: dict, repo: Path) -> str:
    if fu.get("example_toml"):
        content = read_upstream_file(repo, fu["example_toml"])
        if content:
            return content.strip()
    fallback = fu.get("default_toml", "")
    if fallback:
        return fallback.strip()
    devices = fu["devices"]
    dev = devices[0] if isinstance(devices, list) else devices
    return (
        f'[base]\nname = "{fu["name"]}"\ndevice = "{dev}"\n'
        f'version = "1.0.0"\ntype = "{fu["name"]}"'
    )


def generate_reference(fu: dict, toml_content: str, commit: str, commit_date: str) -> str:
    devices = fu["devices"]
    devices_str = ", ".join(devices) if isinstance(devices, list) else devices
    return REFERENCE_TEMPLATE.format(
        commit=commit,
        commit_date=commit_date,
        name=fu["name"],
        devices=devices_str,
        group=fu["group"],
        purpose=fu.get("purpose", "").strip(),
        toml_content=toml_content,
        ports_md=ports_to_md(fu.get("ports", {})),
        config_keys_md=config_keys_to_md(fu.get("config_keys", [])),
        notes_md=notes_to_md(fu.get("notes", [])),
        source_dir=fu.get("source_dir", ""),
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate skills/modelbox/ from upstream ModelBox repo."
    )
    parser.add_argument("--modelbox-repo", required=True, type=Path,
                        help="Path to cloned upstream modelbox repo")
    parser.add_argument("--commit", required=True,
                        help="Full SHA of the pinned commit")
    parser.add_argument("--out", required=True, type=Path,
                        help="Output directory (e.g. skills/modelbox/)")
    args = parser.parse_args()

    tools_dir = Path(__file__).parent
    allowlist_path = tools_dir / "modelbox-flowunits.yml"
    prelude_path = tools_dir / "modelbox-skill-prelude.md"
    recipes_path = tools_dir / "modelbox-skill-recipes.md"

    data = load_yaml(allowlist_path)
    commit = args.commit
    commit_date = str(data.get("modelbox_commit_date", ""))

    prelude_text = prelude_path.read_text()
    recipes_text = recipes_path.read_text()

    out = args.out
    refs_dir = out / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    flowunits: list[dict] = data["flowunits"]

    # ── Generate reference files ────────────────────────────────────────────
    for fu in flowunits:
        toml_content = make_toml_content(fu, args.modelbox_repo)
        content = generate_reference(fu, toml_content, commit, commit_date)
        ref_path = refs_dir / f"{fu['name']}.md"
        ref_path.write_text(content)
        print(f"  wrote {ref_path}")

    # ── Assemble SKILL.md ───────────────────────────────────────────────────
    parts: list[str] = [SKILL_FRONTMATTER]

    parts.append(extract_section(prelude_text, "when_to_use") + "\n\n")
    parts.append(extract_section(prelude_text, "mental_model") + "\n\n")

    # Catalog (generated from YAML)
    parts.append(CATALOG_HEADER)
    for fu in flowunits:
        parts.append(build_catalog_row(fu) + "\n")
    parts.append("\n")

    parts.append(extract_section(prelude_text, "virtual_type_matrix") + "\n\n")
    parts.append(extract_section(recipes_text, "recipes") + "\n\n")
    parts.append(extract_section(prelude_text, "gotchas") + "\n\n")
    parts.append(extract_section(prelude_text, "pointers") + "\n\n")
    parts.append(SKILL_FOOTER.format(commit=commit, commit_date=commit_date))

    skill_path = out / "SKILL.md"
    skill_path.write_text("".join(parts))
    print(f"  wrote {skill_path}")
    print(f"\nDone. {len(flowunits)} flowunits, commit={commit[:12]}")


if __name__ == "__main__":
    main()
