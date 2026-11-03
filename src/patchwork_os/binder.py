# SPDX-License-Identifier: Apache-2.0
"""Host- and runtime-agnostic 3-layer CMDS knowledge validator and hub-spoke binder."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List

from .ladder import EvaluationVerdict, LadderEvaluationResult, NearDeterministicLadder

REQUIRED_PILLARS = (
    "morluto/rea",
    "cmds-llm-wiki",
    "graft",
    "trail-code",
    "hermes-agent",
    "buildermethods/agent-os",
    "mattpocock/skills",
    "cmds-share",
    "ais-os",
    "unlazy",
)

REQUIRED_PARADIGMS = (
    "workflow",
    "meta-prompting",
    "graph-prompting",
    "prompt-flow",
)


def validate_patchwork_satellite(
    repo_root: Path,
    satellite_rel_path: str = "knowledge",
) -> Dict[str, Any]:
    """Deterministically validate a 3-layer CMDS knowledge directory at Tier 0."""
    sat_root = repo_root / satellite_rel_path
    reasons: List[str] = []
    required_files = (
        sat_root / "index.md",
        sat_root / "raw" / "source-manifest.md",
        sat_root / "wiki" / "patchwork-os-architecture.md",
        sat_root / "rules" / "patchwork-os-contract.md",
    )
    missing = [str(p.relative_to(repo_root).as_posix()) for p in required_files if not p.is_file()]
    if missing:
        return {
            "valid": False,
            "reasons": [f"MISSING_SATELLITE_FILES:{','.join(missing)}"],
            "missing_files": missing,
        }

    texts = {p.name: p.read_text(encoding="utf-8") for p in required_files}
    combined = "\n".join(texts.values())
    combined_lower = combined.lower()

    for pillar in REQUIRED_PILLARS:
        if pillar not in combined_lower:
            reasons.append(f"MISSING_PILLAR:{pillar}")

    for paradigm in REQUIRED_PARADIGMS:
        if paradigm not in combined_lower:
            reasons.append(f"MISSING_PARADIGM:{paradigm}")

    if re.search(r"sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}", combined):
        reasons.append("API_KEY_LEAK")

    in_mermaid = False
    for name, content in texts.items():
        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```mermaid"):
                in_mermaid = True
                continue
            if in_mermaid and stripped.startswith("```"):
                in_mermaid = False
                continue
            if in_mermaid and len(line) > 79:
                reasons.append(f"MERMAID_LINE_TOO_WIDE:{name}:L{idx}:{len(line)}")

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "files_checked": len(required_files),
    }


def evaluate_repository(repo_root: Path) -> LadderEvaluationResult:
    """Run Tier-0 deterministic evaluation over the repository knowledge hub."""
    ladder = NearDeterministicLadder()

    def _tier0(raw: Dict[str, Any]) -> tuple[EvaluationVerdict | None, List[str], Dict[str, Any]]:
        res = validate_patchwork_satellite(Path(raw["repo_root"]))
        if res["valid"]:
            return EvaluationVerdict.PASS, ["TIER0_SATELLITE_VALID"], res
        return EvaluationVerdict.FAIL, res["reasons"], res

    return ladder.evaluate({"repo_root": str(repo_root)}, _tier0)
