# SPDX-License-Identifier: Apache-2.0
"""Check declared module and procedure presence for twelve architecture categories.

The returned evidence concerns file presence only. It does not assess runtime
behavior, secret hygiene, provider availability, compliance or isolation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

UPSTREAM_TO_PATCHWORK_12_PILLARS: tuple[Dict[str, str], ...] = (
    {
        "pillar_id": "P01_AGNOSTIC_SETUP_AND_REBRANDING",
        "patchwork_source": "Runtime-agnostic setup and project/skill rebranding",
        "patchwork_module": "src/patchwork_os/setup_init.py",
        "patchwork_skill": "skills/pwos-setup/SKILL.md",
    },
    {
        "pillar_id": "P02_THREE_LAYER_CLI_CONFIG_CONTRACT",
        "patchwork_source": "Layered configuration and explicit keyword overrides",
        "patchwork_module": "src/patchwork_os/config_loader.py",
        "patchwork_skill": "skills/pwos-setup/SKILL.md",
    },
    {
        "pillar_id": "P03_EXTENSIBLE_COMPLIANCE_INTER_RUNTIME_DISPATCH",
        "patchwork_source": "Example backend selection and inter-runtime dispatch planning",
        "patchwork_module": "src/patchwork_os/runtime_dispatch.py",
        "patchwork_skill": "skills/pwos-runtime-dispatch/SKILL.md",
    },
    {
        "pillar_id": "P04_PERSONA_STARTER_BOOST_KIT",
        "patchwork_source": "Persona configuration and structured requirements elicitation",
        "patchwork_module": "src/patchwork_os/persona_setup.py",
        "patchwork_skill": "skills/pwos-persona-agent/SKILL.md",
    },
    {
        "pillar_id": "P05_HUB_SPOKE_VLA_WFC_MPT_ORCHESTRATION",
        "patchwork_source": "Role-separated workflow, model examples, and hub/spoke metadata",
        "patchwork_module": "src/patchwork_os/hub_spoke_gate.py",
        "patchwork_skill": "skills/pwos-wfc/SKILL.md",
    },
    {
        "pillar_id": "P06_SESSION_LIFECYCLE_MESSENGER_AND_BACKLOG",
        "patchwork_source": "Session handover, communication contracts, and deferred obligations",
        "patchwork_module": "src/patchwork_os/session_lifecycle.py",
        "patchwork_skill": "skills/pwos-session-lifecycle/SKILL.md",
    },
    {
        "pillar_id": "P07_PROGRESSIVE_MCP_TO_CLI_PRINTING_PRESS",
        "patchwork_source": "Progressive MCP tool projection into CLI contracts",
        "patchwork_module": "src/patchwork_os/mcp_printing_press.py",
        "patchwork_skill": "skills/pwos-mcp-bridge/SKILL.md",
    },
    {
        "pillar_id": "P08_HYBRID_BROWSER_VLA_AND_VISUAL_GATE",
        "patchwork_source": "Browser observation and visual feedback contracts",
        "patchwork_module": "src/patchwork_os/browser_vla.py",
        "patchwork_skill": "skills/pwos-browser-vla/SKILL.md",
    },
    {
        "pillar_id": "P09_INSTRUCTION_BUDGET_AND_HARNESS_AUDIT",
        "patchwork_source": "Instruction-budget measurement, event deduplication, and pinned harness contracts",
        "patchwork_module": "src/patchwork_os/harness_audit.py",
        "patchwork_skill": "skills/pwos-harness-audit/SKILL.md",
    },
    {
        "pillar_id": "P10_OBSIDIAN_FREE_CMDS_LLM_WIKI",
        "patchwork_source": "Three-layer Markdown knowledge and bounded local trace scans; no isolation or regulatory assessment",
        "patchwork_module": "src/patchwork_os/llm_wiki.py",
        "patchwork_skill": "skills/pwos-quarry/SKILL.md",
    },
    {
        "pillar_id": "P11_NEAR_DETERMINISTIC_ESCALATION_LADDER",
        "patchwork_source": "Deterministic checks and bounded escalation planning",
        "patchwork_module": "src/patchwork_os/ladder.py",
        "patchwork_skill": "skills/pwos-fable-mode/SKILL.md",
    },
    {
        "pillar_id": "P12_REVERSE_ENGINEERING_ANYTHING_REA",
        "patchwork_source": "Evidence-based reverse engineering, debugging, and test procedures",
        "patchwork_module": "src/patchwork_os/rea_gap_analyzer.py",
        "patchwork_skill": "skills/pwos-rea/SKILL.md",
    },
)


def audit_upstream_to_patchwork_parity(patchwork_root: Path) -> Dict[str, Any]:
    """Check the declared module and skill paths for each architecture category."""
    root = patchwork_root.resolve()
    missing: List[str] = []
    verified_pillars: List[Dict[str, Any]] = []

    for pillar in UPSTREAM_TO_PATCHWORK_12_PILLARS:
        mod_path = root / pillar["patchwork_module"]
        skill_path = root / pillar["patchwork_skill"]
        mod_ok = mod_path.is_file()
        skill_ok = skill_path.is_file()
        if not mod_ok:
            missing.append(f"MISSING_MODULE:{pillar['patchwork_module']}")
        if not skill_ok:
            missing.append(f"MISSING_SKILL:{pillar['patchwork_skill']}")
        verified_pillars.append(
            {
                **pillar,
                "module_exists": mod_ok,
                "skill_exists": skill_ok,
            }
        )

    return {
        "schema_version": "patchwork-rea-parity-audit-v1",
        "patchwork_root": root.as_posix(),
        "pillar_count": len(UPSTREAM_TO_PATCHWORK_12_PILLARS),
        "complete_parity": len(missing) == 0,
        "missing_items": missing,
        "pillars": verified_pillars,
    }
