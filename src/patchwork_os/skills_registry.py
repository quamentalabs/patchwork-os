# SPDX-License-Identifier: MIT
"""Tier-0 Validator and Registry for Patchwork-OS Generalized Skill Skeleton Procedures."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

REQUIRED_CORE_SKILLS: tuple[str, ...] = (
    "grilling",
    "quarry",
    "deconstruct",
    "crucible",
    "systematic-debugging",
    "tdd",
    "stdd",
    "fable-mode",
    "wfc",
    "rea",
)

FORBIDDEN_PROPRIETARY_TOKENS: tuple[str, ...] = (
    "proprietary-internal",
    "private-host-alias",
    "unredacted-user-home",
    "confidential-org",
)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
STAGE_HEADING_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


def parse_skill_skeleton(skill_md_path: Path) -> dict[str, Any]:
    """Parse and validate a single generalized SKILL.md skeleton procedure at Tier 0."""
    raw_bytes = skill_md_path.read_bytes()
    text = raw_bytes.decode("utf-8")
    m = FRONTMATTER_RE.match(text)
    meta: dict[str, Any] = {}
    body = text
    if m:
        fm_text, body = m.group(1), m.group(2)
        current_list: list[str] | None = None
        for line in fm_text.splitlines():
            if line.startswith("  - ") and current_list is not None:
                current_list.append(line[4:].strip())
            elif ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if not v:
                    current_list = []
                    meta[k] = current_list
                else:
                    current_list = None
                    meta[k] = v

    stages = [s.strip() for s in STAGE_HEADING_RE.findall(body)]
    required_sections = (
        "## Overview",
        "## Invariants",
        "## Skeleton Procedure (Ordered Stages)",
        "## Artifacts and Verification Gates",
        "## Hard Boundaries",
    )
    missing_sections = [sec for sec in required_sections if sec not in body]
    lower_text = text.lower()
    proprietary_hits = [tok for tok in FORBIDDEN_PROPRIETARY_TOKENS if tok in lower_text]
    has_em_dash = "\u2014" in text
    has_dollar = "$" in text
    has_crlf = b"\r\n" in raw_bytes

    valid = (
        bool(meta.get("name"))
        and bool(meta.get("description"))
        and len(stages) >= 4
        and not missing_sections
        and not proprietary_hits
        and not has_em_dash
        and not has_dollar
        and not has_crlf
    )
    return {
        "name": meta.get("name", skill_md_path.parent.name),
        "path": skill_md_path.as_posix(),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "category": meta.get("category", ""),
        "tier": meta.get("tier", ""),
        "paradigms": meta.get("paradigms", []),
        "stage_count": len(stages),
        "stages": stages,
        "missing_sections": missing_sections,
        "proprietary_hits": proprietary_hits,
        "has_em_dash": has_em_dash,
        "has_dollar": has_dollar,
        "has_crlf": has_crlf,
        "valid": valid,
    }


def validate_skills_directory(skills_root: Path) -> dict[str, Any]:
    """Validate the complete `skills/` directory of generalized skeleton procedures."""
    skills_root = Path(skills_root).resolve()
    index_path = skills_root / "INDEX.md"
    discovered: dict[str, dict[str, Any]] = {}
    if skills_root.is_dir():
        for skill_md in sorted(skills_root.glob("*/SKILL.md")):
            info = parse_skill_skeleton(skill_md)
            discovered[skill_md.parent.name] = info

    missing_core = [name for name in REQUIRED_CORE_SKILLS if name not in discovered]
    invalid_skills = [name for name, info in discovered.items() if not info["valid"]]

    return {
        "valid": index_path.is_file() and not missing_core and not invalid_skills,
        "index_present": index_path.is_file(),
        "skill_count": len(discovered),
        "required_core_skills": list(REQUIRED_CORE_SKILLS),
        "missing_core_skills": missing_core,
        "invalid_skills": invalid_skills,
        "skills": discovered,
    }
