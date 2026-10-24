# SPDX-License-Identifier: MIT
"""Runtime-Agnostic Starter-Kit Initialization, Rebranding & Skill-Prefix Engine.

Because ``Patchwork-OS`` is a working title (codename) for the starter kit,
this module provides a 100% runtime-agnostic initialization flow (``pwos-setup``
/ ``<prefix>-setup``) that never assumes Claude Code:

1. Works across any host runtime (``cc``, ``codex``, ``agy``, ``muse``,
   ``aws_kiro``, ``github_copilot``, ``cursor``, or plain terminal CLI).
2. Emits a universal questionnaire schema (``build_agnostic_setup_questionnaire``)
   that can be rendered via ``ask_question`` (AGY), ``AskUserQuestion`` (CC),
   interactive stdin, or answered non-interactively via the 3-Layer Config
   Contract (``--config-json`` + ``--input-json`` + ``--set key=value``).
3. Rebrands or preserves the project identity:
   - ``os_name`` (default ``"Patchwork-OS"``, e.g. ``"Aegis-OS"``, ``"Nexus-OS"``)
   - ``skill_prefix`` (default ``"pwos"``, e.g. ``"aegis"``, ``"nxos"``, or keep ``"pwos"``)
   - ``dispatcher_skill_name`` (default ``"runtime-dispatch"`` with backward-compatible
     ``"deploy-cli"`` alias)
   - ``compliance_regime`` (``commercial_cloud``, ``github_enterprise``,
     ``itar_ear_aws_govcloud``, ``itar_ear_gcp_vertex``, ``itar_ear_dual_govcloud``,
     ``airgapped_local``)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .config_loader import add_three_layer_cli_arguments, load_layered_config
from .persona_setup import bootstrap_persona_starter_kit

COMPLIANCE_REGIMES: tuple[str, ...] = (
    "commercial_cloud",
    "github_enterprise",
    "itar_ear_aws_govcloud",
    "itar_ear_gcp_vertex",
    "itar_ear_dual_govcloud",
    "airgapped_local",
)

DEFAULT_SETUP_CONFIG: Dict[str, Any] = {
    "os_name": "Patchwork-OS",
    "skill_prefix": "pwos",
    "keep_default_prefix_aliases": True,
    "dispatcher_skill_name": "runtime-dispatch",
    "keep_deploy_cli_alias": True,
    "compliance_regime": "commercial_cloud",
    "enabled_cloud_backends": [
        "anthropic_direct",
        "openai_direct",
        "google_ai_studio",
        "gcp_vertex_ai",
        "aws_bedrock",
        "github_models",
    ],
    "enabled_runtime_harnesses": [
        "cc",
        "codex",
        "agy",
        "muse",
        "aws_kiro",
        "github_copilot",
    ],
    "organization_context": "Engineering Organization",
    "team_topology": "Cross-Functional Product & Platform Squad",
    "individual_preferences": "Concise, evidence-first, deterministic verification",
    "task_characteristics": "High-reliability software architecture, TDD, and multi-agent synthesis",
}


def build_agnostic_setup_questionnaire() -> Dict[str, Any]:
    """Return a runtime-agnostic interactive setup questionnaire compatible with any UI/CLI."""
    return {
        "schema_version": "patchwork-agnostic-setup-questionnaire-v1",
        "runtime_agnostic": True,
        "supported_adapters": [
            "agy:ask_question",
            "cc:AskUserQuestion",
            "codex:interactive_prompt_or_json",
            "aws_kiro:steering_and_spec_prompt",
            "github_copilot:chat_questionnaire",
            "cli:config_json_input_json_manual_kwargs",
        ],
        "questions": [
            {
                "id": "os_identity",
                "question": "What project/OS name and skill prefix should this workspace use? (Patchwork-OS / pwos-* is the starter-kit working title; you can keep it or rebrand it via brainstorming.)",
                "is_multi_select": False,
                "maps_to": ["os_name", "skill_prefix"],
                "options": [
                    "(Recommended) Keep default starter-kit identity (Patchwork-OS / pwos-*)",
                    "Customize OS name and skill prefix (e.g., Aegis-OS / aegis-*, Nexus-OS / nxos-*)",
                    "Use prefix-free canonical skill names (e.g., grilling, wfc, runtime-dispatch)",
                ],
            },
            {
                "id": "compliance_regime",
                "question": "Which regulatory, export-control (ITAR/EAR), or enterprise cloud boundary governs this environment?",
                "is_multi_select": False,
                "maps_to": ["compliance_regime", "enabled_cloud_backends"],
                "options": [
                    "(Recommended) Commercial Multi-Cloud Frontier (Anthropic, OpenAI, Google, Meta Muse, Bedrock, Vertex)",
                    "GitHub Enterprise & Commercial Cloud (GitHub Copilot + Claude/GPT/Gemini)",
                    "ITAR / EAR — AWS GovCloud & Amazon Bedrock Only (Claude Opus/Sonnet + Nova + Llama + Kiro/CC cross-runtime)",
                    "ITAR / EAR — Google Cloud Vertex AI Assured Workloads Only (Gemini 4 Argon/Flash + Vertex Claude + AGY/CC)",
                    "ITAR / EAR — Dual Sovereign GovCloud (AWS Bedrock GovCloud + GCP Vertex AI Assured Workloads)",
                    "Air-Gapped / On-Premises Open-Weights Only (Muse Spark Open, Mistral Large 4, Nemotron, Llama 4, Gemma 4)",
                ],
            },
            {
                "id": "runtime_harnesses",
                "question": "Which agent runtime harnesses are active in your workflow for Inter-Runtime Synthesis?",
                "is_multi_select": True,
                "maps_to": ["enabled_runtime_harnesses"],
                "options": [
                    "(Recommended) Claude Code (cc) — Hooks, subagents, worktrees",
                    "(Recommended) OpenAI Codex (codex) — Sandboxed worktree execution & diff verification",
                    "(Recommended) Google Antigravity (agy) — Browser VLA, multimodal & MCP sidecars",
                    "Meta Muse (muse) — 1M+ context & high-speed synthesis",
                    "AWS Kiro (aws_kiro) — Native EARS specs, steering & Bedrock IAM integration",
                    "GitHub Copilot (github_copilot) — PR/Actions graph & multi-model enterprise workspace",
                ],
            },
            {
                "id": "dispatcher_naming",
                "question": "How should the cross-runtime dispatcher skill be named?",
                "is_multi_select": False,
                "maps_to": ["dispatcher_skill_name", "keep_deploy_cli_alias"],
                "options": [
                    "(Recommended) Generalize to runtime-dispatch (<prefix>-runtime-dispatch) while keeping deploy-cli alias",
                    "Use inter-runtime-dispatch (<prefix>-inter-runtime-dispatch) with deploy-cli alias",
                    "Keep deploy-cli (<prefix>-deploy-cli) as primary name",
                ],
            },
        ],
    }


def _sanitize_slug(raw: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", raw.strip().lower()).strip("-")
    return cleaned or fallback


def apply_project_setup_and_rebrand(
    repo_root: Path,
    *,
    config_json: Optional[Path | str | Mapping[str, Any]] = None,
    input_json: Optional[Path | str | Mapping[str, Any]] = None,
    manual_set_pairs: Optional[Sequence[str]] = None,
    manual_kwargs: Optional[Mapping[str, Any]] = None,
    bootstrap_personas: bool = True,
) -> Dict[str, Any]:
    """Initialize or rebrand the starter-kit workspace using the 3-Layer Config Contract."""
    resolved = load_layered_config(
        defaults=DEFAULT_SETUP_CONFIG,
        config_json=config_json,
        input_json=input_json,
        manual_set_pairs=manual_set_pairs,
        manual_kwargs=manual_kwargs,
    )

    os_name = str(resolved.get("os_name") or "Patchwork-OS").strip()
    raw_prefix = str(resolved.get("skill_prefix") or "pwos").strip().lower()
    skill_prefix = "" if raw_prefix in {"none", "empty", "unprefixed"} else _sanitize_slug(raw_prefix, "pwos")
    dispatcher_base = _sanitize_slug(
        str(resolved.get("dispatcher_skill_name") or "runtime-dispatch"),
        "runtime-dispatch",
    )
    compliance_regime = str(resolved.get("compliance_regime") or "commercial_cloud").strip().lower()
    if compliance_regime not in COMPLIANCE_REGIMES:
        raise ValueError(
            f"Unsupported compliance_regime {compliance_regime!r}; expected one of {COMPLIANCE_REGIMES}"
        )

    skills_dir = repo_root / "skills"
    rebranded_skills: List[Dict[str, str]] = []
    if skills_dir.is_dir():
        for src_skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
            src_name = src_skill_dir.name
            base_slug = src_name[5:] if src_name.startswith("pwos-") else src_name
            if base_slug == "deploy-cli" and dispatcher_base != "deploy-cli":
                target_base = dispatcher_base
            else:
                target_base = base_slug

            target_skill_name = f"{skill_prefix}-{target_base}" if skill_prefix else target_base
            target_dir = skills_dir / target_skill_name
            target_dir.mkdir(parents=True, exist_ok=True)
            src_text = (src_skill_dir / "SKILL.md").read_text(encoding="utf-8")
            rewritten = re.sub(
                r"^name:\s*.*$",
                f"name: {target_skill_name}",
                src_text,
                count=1,
                flags=re.MULTILINE,
            )
            rewritten = rewritten.replace("Patchwork-OS", os_name)
            (target_dir / "SKILL.md").write_text(rewritten, encoding="utf-8")
            rebranded_skills.append(
                {
                    "source_skill": src_name,
                    "target_skill": target_skill_name,
                    "path": (target_dir / "SKILL.md").as_posix(),
                }
            )

    persona_manifest: Optional[Dict[str, Any]] = None
    if bootstrap_personas:
        persona_manifest = bootstrap_persona_starter_kit(
            repo_root,
            organization_context={"context": str(resolved.get("organization_context", ""))},
            team_topology={"topology": str(resolved.get("team_topology", ""))},
            individual_preferences={"preferences": str(resolved.get("individual_preferences", ""))},
            task_characteristics={"characteristics": str(resolved.get("task_characteristics", ""))},
            custom_facets_by_slot={
                "dag-planner": {
                    "os_name": os_name,
                    "skill_prefix": skill_prefix or "unprefixed",
                    "compliance_regime": compliance_regime,
                }
            },
        )

    profile_out = repo_root / "config" / "workspace-profile.json"
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    workspace_profile = {
        "schema_version": "patchwork-workspace-profile-v1",
        "os_name": os_name,
        "skill_prefix": skill_prefix,
        "dispatcher_skill_name": (
            f"{skill_prefix}-{dispatcher_base}" if skill_prefix else dispatcher_base
        ),
        "deploy_cli_alias_preserved": bool(resolved.get("keep_deploy_cli_alias", True)),
        "compliance_regime": compliance_regime,
        "enabled_cloud_backends": list(resolved.get("enabled_cloud_backends", [])),
        "enabled_runtime_harnesses": list(resolved.get("enabled_runtime_harnesses", [])),
        "rebranded_skill_count": len(rebranded_skills),
        "rebranded_skills": rebranded_skills,
        "persona_starter_kit_initialized": persona_manifest is not None,
        "config_provenance": resolved.get("_config_provenance", {}),
    }
    profile_out.write_text(
        json.dumps(workspace_profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return workspace_profile


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Runtime-agnostic setup, rebranding, skill-prefix, and compliance initializer."
    )
    add_three_layer_cli_arguments(parser)
    parser.add_argument("--repo-root", type=str, default=".", help="Target repository root.")
    parser.add_argument("--os-name", type=str, default=None, help="Override OS/project display name.")
    parser.add_argument("--skill-prefix", type=str, default=None, help="Override skill prefix (e.g. pwos, aegis, nxos).")
    parser.add_argument(
        "--dispatcher-skill-name",
        type=str,
        default=None,
        help="Override generalized dispatcher skill base name (default: runtime-dispatch).",
    )
    parser.add_argument(
        "--compliance-regime",
        type=str,
        default=None,
        choices=list(COMPLIANCE_REGIMES),
        help="Override regulatory/cloud compliance regime.",
    )
    parser.add_argument(
        "--emit-questionnaire",
        action="store_true",
        help="Print the runtime-agnostic setup questionnaire JSON and exit.",
    )
    args = parser.parse_args(argv)
    if args.emit_questionnaire:
        print(json.dumps(build_agnostic_setup_questionnaire(), indent=2, ensure_ascii=False))
        return 0

    result = apply_project_setup_and_rebrand(
        Path(args.repo_root).resolve(),
        config_json=args.config_json,
        input_json=args.input_json,
        manual_set_pairs=args.manual_set,
        manual_kwargs={
            "os_name": args.os_name,
            "skill_prefix": args.skill_prefix,
            "dispatcher_skill_name": args.dispatcher_skill_name,
            "compliance_regime": args.compliance_regime,
        },
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
