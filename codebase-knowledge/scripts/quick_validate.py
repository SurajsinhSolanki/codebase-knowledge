#!/usr/bin/env python3
"""
Validation script for the codebase-knowledge skill.

Two modes:
  quick_validate.py <skill_dir>            - validate the skill's own files (SKILL.md, references, agents)
  quick_validate.py --bundle <knowledge_dir> - validate a generated OKF bundle for OKF v0.1 conformance
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml")
    sys.exit(1)

RESERVED_FILENAMES = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
LOG_DATE_HEADING_RE = re.compile(r"^## \d{4}-\d{2}-\d{2}", re.MULTILINE)


def parse_frontmatter(content):
    """Return (frontmatter_dict_or_None, had_frontmatter_block, error_or_None)."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, False, None
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return None, True, str(e)
    return fm, True, None


def validate_skill(skill_path):
    skill_path = Path(skill_path)
    errors = []

    # ---- SKILL.md exists ----
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md not found")
        return False, errors

    content = skill_md.read_text()

    # ---- Frontmatter ----
    fm, had_fm, fm_error = parse_frontmatter(content)
    if not had_fm:
        errors.append("SKILL.md: no YAML frontmatter (must start with '---')")
        return False, errors
    if fm_error:
        errors.append(f"SKILL.md: invalid YAML in frontmatter: {fm_error}")
        return False, errors
    if not isinstance(fm, dict):
        errors.append("SKILL.md: frontmatter must be a YAML dictionary")
        return False, errors

    # ---- Required fields ----
    if "name" not in fm:
        errors.append("SKILL.md: missing 'name' in frontmatter")
    if "description" not in fm:
        errors.append("SKILL.md: missing 'description' in frontmatter")

    name = fm.get("name", "")
    if name != "codebase-knowledge":
        errors.append(f"SKILL.md: name should be 'codebase-knowledge', got '{name}'")

    desc = fm.get("description", "")
    if len(desc) > 1024:
        errors.append(f"SKILL.md: description too long ({len(desc)} chars, max 1024)")

    # ---- References ----
    ref_file = skill_path / "references" / "knowledge-spec.md"
    if not ref_file.exists():
        errors.append("references/knowledge-spec.md not found")

    # ---- Scripts referenced by SKILL.md exist ----
    for script_name in ("quick_validate.py", "visualize.py"):
        if not (skill_path / "scripts" / script_name).exists():
            errors.append(f"scripts/{script_name} not found but referenced by SKILL.md")

    # ---- Agents metadata ----
    agent_yaml = skill_path / "agents" / "openai.yaml"
    if agent_yaml.exists():
        try:
            yaml.safe_load(agent_yaml.read_text())
        except yaml.YAMLError as e:
            errors.append(f"agents/openai.yaml: invalid YAML: {e}")

    if errors:
        return False, errors
    return True, ["Skill is valid!"]


def validate_bundle(bundle_path):
    """Check a generated knowledge/ folder for OKF v0.1 conformance."""
    bundle_path = Path(bundle_path)
    errors = []
    warnings = []

    if not bundle_path.is_dir():
        return False, [f"{bundle_path} is not a directory"], []

    md_files = sorted(bundle_path.rglob("*.md"))
    if not md_files:
        return False, [f"No .md files found under {bundle_path}"], []

    dirs_with_files = {p.parent for p in md_files}
    for d in sorted(dirs_with_files):
        if not (d / "index.md").exists():
            warnings.append(f"{d}/: missing index.md")

    for f in md_files:
        rel = f.relative_to(bundle_path)
        content = f.read_text()

        if f.name == "index.md":
            fm, had_fm, fm_error = parse_frontmatter(content)
            if had_fm:
                errors.append(f"{rel}: index.md must not have YAML frontmatter (OKF reserved filename)")
            continue

        if f.name == "log.md":
            fm, had_fm, fm_error = parse_frontmatter(content)
            if had_fm:
                errors.append(f"{rel}: log.md must not have YAML frontmatter (OKF reserved filename)")
            if not LOG_DATE_HEADING_RE.search(content):
                errors.append(f"{rel}: log.md must have at least one '## YYYY-MM-DD' date heading")
            continue

        # Concept document: OKF-mandated frontmatter with non-empty 'type'
        fm, had_fm, fm_error = parse_frontmatter(content)
        if not had_fm:
            errors.append(f"{rel}: missing YAML frontmatter (OKF requires parseable frontmatter on every concept document)")
            continue
        if fm_error:
            errors.append(f"{rel}: invalid YAML in frontmatter: {fm_error}")
            continue
        if not isinstance(fm, dict):
            errors.append(f"{rel}: frontmatter must be a YAML dictionary")
            continue
        if not fm.get("type"):
            errors.append(f"{rel}: 'type' field is missing or empty (OKF-mandated field)")

        for recommended in ("title", "description", "resource", "tags", "timestamp"):
            if recommended not in fm:
                warnings.append(f"{rel}: missing OKF-recommended field '{recommended}'")

    # ---- Broken-link check (informational only — OKF tolerates broken links) ----
    for f in md_files:
        content = f.read_text()
        for link_target in re.findall(r"\]\(([^)]+)\)", content):
            if link_target.startswith(("http://", "https://", "#")):
                continue
            target = link_target.split("#")[0]
            if not target:
                continue
            resolved = (f.parent / target).resolve() if not target.startswith("/") else (bundle_path / target.lstrip("/")).resolve()
            if not resolved.exists():
                warnings.append(f"{f.relative_to(bundle_path)}: broken link -> {link_target}")

    return len(errors) == 0, errors, warnings


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--bundle":
        ok, errs, warns = validate_bundle(sys.argv[2])
        for w in warns:
            print(f"WARNING: {w}")
        for e in errs:
            print(f"ERROR: {e}")
        print("OKF bundle is conformant!" if ok else f"OKF bundle has {len(errs)} conformance error(s).")
        sys.exit(0 if ok else 1)
    elif len(sys.argv) == 2:
        valid, messages = validate_skill(sys.argv[1])
        for msg in messages:
            print(msg)
        sys.exit(0 if valid else 1)
    else:
        print("Usage: python quick_validate.py <skill_directory>")
        print("       python quick_validate.py --bundle <knowledge_directory>")
        sys.exit(1)
