# SPDX-License-Identifier: MIT
"""Generalized Multi-Runtime, Multi-Cloud & Compliance-Aware Inter-Runtime Dispatcher.

Generalizes ``deploy-cli`` into ``runtime-dispatch`` (``pwos-runtime-dispatch``
with backward-compatible ``pwos-deploy-cli`` alias) while decoupling:
1. **Compliance & Export-Control Regime** (``commercial_cloud``, ``github_enterprise``,
   ``itar_ear_aws_govcloud``, ``itar_ear_gcp_vertex``, ``itar_ear_dual_govcloud``,
   ``airgapped_local``)
2. **Cloud Hosting Backend** (``anthropic_direct``, ``openai_direct``,
   ``google_ai_studio``, ``aws_bedrock_commercial``, ``aws_bedrock_govcloud_itar``,
   ``gcp_vertex_ai``, ``gcp_vertex_assured_itar``, ``github_models_enterprise``,
   ``local_airgap_vllm``)
3. **Runtime Harness** (``cc``, ``codex``, ``agy``, ``muse``, ``aws_kiro``,
   ``github_copilot``, ``cursor``, ``custom_cli``)
4. **Foundation Model & Effort** (grounded in the VLA-extracted 272-model
   Artificial Analysis v4.3.2 leaderboard & comparison catalog)

Even when ITAR/EAR export controls restrict the available model pool (for example,
when ``fable-5-1``, ``gpt-6-astra``, ``gpt-6.1-sol``, ``muse-wonder-*``, or
``gemini-*`` are unavailable on AWS Bedrock GovCloud), this engine achieves
**Inter-Runtime Synthesis** by pairing distinct runtime harnesses (such as
``cc`` + ``aws_kiro`` on Bedrock GovCloud, or ``agy`` + ``cc`` on Vertex AI
Assured Workloads) so ``Composer Runtime != Validator Runtime`` brings
complementary harness capabilities over compliant model endpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .config_loader import add_three_layer_cli_arguments, load_layered_config
from .deploy_cli import (
    plan_inter_cli_dispatch,
    verify_inter_cli_completion_contract,
    verify_parent_child_lease_isolation,
)


def _m_gpt6(slot: str) -> str:
    return f"gpt-6-{slot}"


def _m_gem38(suffix: str) -> str:
    return f"gemini-3.8-{suffix}"


def _m_muse(suffix: str) -> str:
    return f"muse-{suffix}"


# Runtime Harness Capabilities: why different runtimes provide Inter-Runtime Synthesis
# even when backed by the exact same underlying foundation model.
RUNTIME_HARNESS_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "cc": {
        "display_name": "Claude Code CLI/IDE",
        "supported_surfaces": ["cli", "ide", "desktop_app"],
        "supported_backends": [
            "anthropic_direct",
            "aws_bedrock_commercial",
            "aws_bedrock_govcloud_itar",
            "gcp_vertex_ai",
            "gcp_vertex_assured_itar",
            "local_airgap_vllm",
        ],
        "unique_runtime_strengths": [
            "Deterministic PreToolUse/PostToolUse/Stop lifecycle hooks",
            "Subagent tree orchestration & isolated git worktree execution",
            "2-row hybrid HUD statusline and session checkpointing",
        ],
    },
    "aws_kiro": {
        "display_name": "AWS Kiro Spec-Driven Agent",
        "supported_surfaces": ["cli", "ide"],
        "supported_backends": [
            "aws_bedrock_commercial",
            "aws_bedrock_govcloud_itar",
        ],
        "unique_runtime_strengths": [
            "Native EARS 3-stage specification engine (requirements.md -> design.md -> tasks.md)",
            "Native AWS IAM / Bedrock GovCloud (ITAR/EAR/FedRAMP High) credential boundary",
            "Repository steering files (.kiro/steering/) and event-driven file hooks",
        ],
    },
    "github_copilot": {
        "display_name": "GitHub Copilot Enterprise / CLI / IDE",
        "supported_surfaces": ["cli", "ide", "desktop_app"],
        "supported_backends": [
            "github_models_enterprise",
            "azure_openai_commercial",
        ],
        "unique_runtime_strengths": [
            "Native GitHub Pull Request, Issue, Actions workflow & security-advisory graph",
            "Multi-model switching (Claude Opus/Sonnet, GPT-6.1 Sol/Astra, Gemini 4 Argon) under one enterprise seat",
            "Organization-wide audit logs and IP indemnity controls (non-ITAR commercial/enterprise)",
        ],
    },
    "codex": {
        "display_name": "OpenAI Codex CLI/App",
        "supported_surfaces": ["cli", "ide", "desktop_app"],
        "supported_backends": [
            "openai_direct",
            "azure_openai_commercial",
            "github_models_enterprise",
            "local_airgap_vllm",
        ],
        "unique_runtime_strengths": [
            "Sandboxed kernel/worktree execution with zero-console patch verification",
            "High-precision unified diff generation and multi-file refactoring",
            "Ultra-low-cost Pareto execution with GPT-6.1 Sol ($0.39/task, 53% Non-Hallucination)",
        ],
    },
    "agy": {
        "display_name": "Google Antigravity (AGY)",
        "supported_surfaces": ["cli", "ide", "desktop_app"],
        "supported_backends": [
            "google_ai_studio",
            "gcp_vertex_ai",
            "gcp_vertex_assured_itar",
        ],
        "unique_runtime_strengths": [
            "Native Hybrid Browser Control + VLA (Vision-Language-Action) DOM/Screenshot loop",
            "Interactive MCP sidecar viewers and native multimodal audio/video/image ingestion",
            "Vertex AI Assured Workloads (ITAR/EAR) compatibility for Gemini 4 Argon & Vertex Claude",
        ],
    },
    "muse": {
        "display_name": "Meta Muse Platform",
        "supported_surfaces": ["cli", "ide", "desktop_app"],
        "supported_backends": [
            "meta_muse_cloud",
            "aws_bedrock_commercial",
            "gcp_vertex_ai",
            "local_airgap_vllm",
        ],
        "unique_runtime_strengths": [
            "1.05M token context window (#1) and 145 tok/s output speed (#1)",
            "Top-1 GDP.pdf document reasoning (33%) and CritPt physics/science reasoning (33%)",
            "Open-weight Muse Spark Open (xhigh, Index 39) deployable on ITAR/air-gapped clusters",
        ],
    },
    "custom_cli": {
        "display_name": "Custom / Open-Weight Local CLI Harness",
        "supported_surfaces": ["cli"],
        "supported_backends": [
            "local_airgap_vllm",
            "aws_bedrock_govcloud_itar",
            "gcp_vertex_assured_itar",
        ],
        "unique_runtime_strengths": [
            "100% air-gapped on-premises execution over vLLM / Ollama / TGI / NIM",
            "Zero external network egress for strict ITAR / EAR / classified workloads",
        ],
    },
}


# VLA-Grounded 272-Model Leaderboard & Compliance Availability Catalog
COMPLIANCE_REGIME_CATALOG: Dict[str, Dict[str, Any]] = {
    "commercial_cloud": {
        "description": "Full commercial multi-cloud access across Anthropic, OpenAI, Google, Meta Muse, AWS Bedrock, and GCP Vertex AI.",
        "itar_ear_restricted": False,
        "available_backends": [
            "anthropic_direct",
            "openai_direct",
            "google_ai_studio",
            "meta_muse_cloud",
            "aws_bedrock_commercial",
            "gcp_vertex_ai",
            "github_models_enterprise",
        ],
        "available_runtimes": ["cc", "codex", "agy", "muse", "aws_kiro", "github_copilot"],
        "unavailable_models_note": "None (all frontier models available).",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "cc", "backend": "anthropic_direct", "model": "fable-5-1", "effort": "xhigh", "aa_index": 53, "hle_xhigh": "59% (#1)", "omniscience_acc": "67% (#1)"},
                {"runtime": "muse", "backend": "meta_muse_cloud", "model": "muse-wonder-full-1.0", "effort": "max", "aa_index": 56, "gdp_pdf": "33% (#1)", "critpt": "33% (#1)"},
                {"runtime": "codex", "backend": "openai_direct", "model": _m_gpt6("astra"), "effort": "xhigh", "aa_index": 53, "cost_usd": 2.31},
            ],
            "execution_coding_audit": [
                {"runtime": "cc", "backend": "anthropic_direct", "model": "opus", "effort": "xhigh", "aa_index": 58, "terminal_bench": "67% (#1)", "cost_usd": 3.46},
                {"runtime": "codex", "backend": "openai_direct", "model": "gpt-6.1-sol", "effort": "xhigh", "aa_index": 52, "non_hallucination": "53% (#1)", "cost_usd": 0.39},
                {"runtime": "cc", "backend": "anthropic_direct", "model": "sonnet", "effort": "xhigh", "aa_index": 56, "speed_tok_s": 133, "cost_usd": 2.01},
            ],
            "browser_vla_automation": [
                {"runtime": "agy", "backend": "google_ai_studio", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53, "automation_bench": "78% (#1)", "cost_usd": 1.99},
                {"runtime": "muse", "backend": "meta_muse_cloud", "model": "muse-wonder-full-1.0", "effort": "max", "aa_index": 56, "automation_bench": "71% (#2)"},
            ],
            "fast_curation_telemetry": [
                {"runtime": "cc", "backend": "anthropic_direct", "model": "sonnet", "effort": "medium", "aa_index": 52, "speed_tok_s": 133},
                {"runtime": "agy", "backend": "google_ai_studio", "model": _m_gem38("flash-high"), "effort": "high", "aa_index": 41, "cost_usd": 1.24},
            ],
        },
    },
    "github_enterprise": {
        "description": "Non-ITAR commercial enterprise standardized on GitHub Copilot Enterprise + GitHub Models / Azure / Direct APIs.",
        "itar_ear_restricted": False,
        "available_backends": [
            "github_models_enterprise",
            "azure_openai_commercial",
            "anthropic_direct",
            "gcp_vertex_ai",
        ],
        "available_runtimes": ["github_copilot", "cc", "codex", "agy"],
        "unavailable_models_note": "Proprietary Meta Muse cloud endpoints excluded by default; uses Copilot + CC + Codex + AGY.",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "cc", "backend": "anthropic_direct", "model": "fable-5-1", "effort": "xhigh", "aa_index": 53},
                {"runtime": "github_copilot", "backend": "github_models_enterprise", "model": "opus", "effort": "xhigh", "aa_index": 56},
                {"runtime": "codex", "backend": "azure_openai_commercial", "model": _m_gpt6("astra"), "effort": "xhigh", "aa_index": 52},
            ],
            "execution_coding_audit": [
                {"runtime": "github_copilot", "backend": "github_models_enterprise", "model": "opus", "effort": "xhigh", "aa_index": 56, "cost_usd": 3.46},
                {"runtime": "codex", "backend": "azure_openai_commercial", "model": "gpt-6.1-sol", "effort": "xhigh", "aa_index": 51, "cost_usd": 0.39},
            ],
            "browser_vla_automation": [
                {"runtime": "agy", "backend": "gcp_vertex_ai", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53},
                {"runtime": "github_copilot", "backend": "github_models_enterprise", "model": "sonnet", "effort": "xhigh", "aa_index": 52},
            ],
            "fast_curation_telemetry": [
                {"runtime": "github_copilot", "backend": "github_models_enterprise", "model": "sonnet", "effort": "medium", "aa_index": 52},
                {"runtime": "agy", "backend": "gcp_vertex_ai", "model": _m_gem38("flash-high"), "effort": "high", "aa_index": 41},
            ],
        },
    },
    "itar_ear_aws_govcloud": {
        "description": "ITAR / EAR / FedRAMP High sovereign boundary on AWS GovCloud (US) & Amazon Bedrock. Fable, GPT-6 Astra/Sol, Muse Wonder, and Gemini are unavailable on Bedrock; achieves cross-runtime diversity by pairing Claude Code (cc) + AWS Kiro (aws_kiro) over Bedrock Claude Opus/Sonnet, Amazon Nova 2.0, and Bedrock Open-Weights.",
        "itar_ear_restricted": True,
        "available_backends": ["aws_bedrock_govcloud_itar"],
        "available_runtimes": ["cc", "aws_kiro", "custom_cli"],
        "unavailable_models_note": "fable-5-1, gpt-6-astra, gpt-6.1-sol, muse-wonder-full, and gemini-4-argon are unavailable on AWS Bedrock GovCloud. Uses Bedrock Claude Opus 5.5 (Index 58/56), Claude Sonnet 5.5 (Index 56/52, 133 tok/s), Muse Spark Open (Index 39), Mistral Large 4 (Index 38), Llama 4 Maverick / 3.3 70B, and Amazon Nova 2.0 Pro/Omni/Lite.",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "max", "aa_index": 58, "cost_usd": 5.98, "note": "Kiro EARS spec synthesis over Bedrock Opus 5.5 (max, Index 58, AA-LCR 85%)"},
                {"runtime": "cc", "backend": "aws_bedrock_govcloud_itar", "model": "sonnet", "effort": "max", "aa_index": 56, "speed_tok_s": 133, "cost_usd": 5.46, "note": "CC architectural counterpoint over Bedrock Sonnet 5.5 (max, Index 56, 133 tok/s)"},
            ],
            "execution_coding_audit": [
                {"runtime": "cc", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "xhigh", "aa_index": 56, "terminal_bench": "60%", "cost_usd": 3.46, "note": "CC worktree implementation + hook enforcement over Bedrock Opus 5.5"},
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "sonnet", "effort": "xhigh", "aa_index": 52, "speed_tok_s": 111, "cost_usd": 2.01, "note": "Cross-runtime Validator (aws_kiro != cc) verifying EARS requirements & tasks on Bedrock"},
            ],
            "browser_vla_automation": [
                {"runtime": "cc", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "high", "aa_index": 54, "cost_usd": 1.82},
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "amazon-nova-2.0-omni", "effort": "medium", "aa_index": 14},
            ],
            "fast_curation_telemetry": [
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "sonnet", "effort": "medium", "aa_index": 52, "speed_tok_s": 111},
                {"runtime": "custom_cli", "backend": "aws_bedrock_govcloud_itar", "model": "amazon-nova-2.0-lite", "effort": "high", "aa_index": 13},
            ],
        },
    },
    "itar_ear_gcp_vertex": {
        "description": "ITAR / EAR / Assured Workloads boundary on Google Cloud Vertex AI. Gemini 4 Argon & 3.8 Flash are natively available alongside Vertex Partner Anthropic Claude Opus 5.5 & Sonnet 5.5; pairs AGY (agy) + Claude Code (cc) for cross-runtime and cross-model synthesis.",
        "itar_ear_restricted": True,
        "available_backends": ["gcp_vertex_assured_itar"],
        "available_runtimes": ["agy", "cc", "custom_cli"],
        "unavailable_models_note": "OpenAI GPT-6 Astra/Sol and proprietary Meta Muse Wonder are unavailable on GCP Vertex Assured Workloads. Uses Gemini 4 Argon (High, Index 53, AutomationBench 78% #1), Vertex Claude Opus 5.5 (Index 58/56), Vertex Claude Sonnet 5.5 (Index 56/52), Gemini 3.8 Flash (Index 41), and Gemma 4 31B.",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "cc", "backend": "gcp_vertex_assured_itar", "model": "opus", "effort": "max", "aa_index": 58, "cost_usd": 5.98},
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53, "cost_usd": 1.99},
            ],
            "execution_coding_audit": [
                {"runtime": "cc", "backend": "gcp_vertex_assured_itar", "model": "opus", "effort": "xhigh", "aa_index": 56, "cost_usd": 3.46},
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53, "cost_usd": 1.99},
            ],
            "browser_vla_automation": [
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53, "automation_bench": "78% (#1)"},
                {"runtime": "cc", "backend": "gcp_vertex_assured_itar", "model": "sonnet", "effort": "xhigh", "aa_index": 52},
            ],
            "fast_curation_telemetry": [
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": _m_gem38("flash-high"), "effort": "high", "aa_index": 41, "cost_usd": 1.24},
                {"runtime": "cc", "backend": "gcp_vertex_assured_itar", "model": "sonnet", "effort": "medium", "aa_index": 52},
            ],
        },
    },
    "itar_ear_dual_govcloud": {
        "description": "Dual Sovereign ITAR / EAR environment combining AWS Bedrock GovCloud (cc + aws_kiro) and GCP Vertex AI Assured Workloads (agy).",
        "itar_ear_restricted": True,
        "available_backends": ["aws_bedrock_govcloud_itar", "gcp_vertex_assured_itar"],
        "available_runtimes": ["cc", "aws_kiro", "agy", "custom_cli"],
        "unavailable_models_note": "OpenAI GPT-6 Astra/Sol and proprietary Meta Muse cloud excluded; full 3-runtime (cc + aws_kiro + agy) and 2-family (Claude Opus/Sonnet + Gemini 4 Argon/Flash) synthesis active.",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "max", "aa_index": 58},
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53},
            ],
            "execution_coding_audit": [
                {"runtime": "cc", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "xhigh", "aa_index": 56},
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53},
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "sonnet", "effort": "xhigh", "aa_index": 52},
            ],
            "browser_vla_automation": [
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": "gemini-4-argon-high", "effort": "high", "aa_index": 53},
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "opus", "effort": "xhigh", "aa_index": 56},
            ],
            "fast_curation_telemetry": [
                {"runtime": "agy", "backend": "gcp_vertex_assured_itar", "model": _m_gem38("flash-high"), "effort": "high", "aa_index": 41},
                {"runtime": "aws_kiro", "backend": "aws_bedrock_govcloud_itar", "model": "sonnet", "effort": "medium", "aa_index": 52},
            ],
        },
    },
    "airgapped_local": {
        "description": "100% Air-Gapped On-Premises ITAR/Classified cluster running VLA-benchmarked open-weight models over local vLLM/NIM.",
        "itar_ear_restricted": True,
        "available_backends": ["local_airgap_vllm"],
        "available_runtimes": ["cc", "codex", "custom_cli"],
        "unavailable_models_note": "All external cloud APIs blocked; uses open-weight models measured on Artificial Analysis v4.3.2 leaderboard (Muse Spark Open [39], Mistral Large 4 [38], NVIDIA Nemotron 3.5 Super VL [26] / Nemotron 3 Ultra [23], Gemma 4 31B [15], IBM Granite 4.2 30B [13], Llama 4 Maverick, Hermes 4 405B).",
        "tier_models": {
            "planning_reasoning": [
                {"runtime": "cc", "backend": "local_airgap_vllm", "model": _m_muse("spark-open-xhigh"), "effort": "xhigh", "aa_index": 39, "cost_usd": 0.84},
                {"runtime": "codex", "backend": "local_airgap_vllm", "model": "mistral-large-4", "effort": "high", "aa_index": 38, "cost_usd": 1.13},
            ],
            "execution_coding_audit": [
                {"runtime": "codex", "backend": "local_airgap_vllm", "model": "mistral-large-4", "effort": "high", "aa_index": 38},
                {"runtime": "cc", "backend": "local_airgap_vllm", "model": _m_muse("spark-open-xhigh"), "effort": "xhigh", "aa_index": 39},
            ],
            "browser_vla_automation": [
                {"runtime": "custom_cli", "backend": "local_airgap_vllm", "model": "nemotron-3.5-super-vl", "effort": "high", "aa_index": 26, "cost_usd": 0.19},
                {"runtime": "cc", "backend": "local_airgap_vllm", "model": "gemma-4-31b", "effort": "high", "aa_index": 15},
            ],
            "fast_curation_telemetry": [
                {"runtime": "custom_cli", "backend": "local_airgap_vllm", "model": "ibm-granite-4.2-30b", "effort": "medium", "aa_index": 13, "cost_usd": 0.07},
                {"runtime": "codex", "backend": "local_airgap_vllm", "model": "hermes-4-70b", "effort": "medium", "aa_index": 8},
            ],
        },
    },
}


DEFAULT_DISPATCH_CONFIG: Dict[str, Any] = {
    "compliance_regime": "commercial_cloud",
    "session_tier": "main_hub",
    "task_category": "planning_architecture_synthesis",
    "complexity": "high",
    "urgency": "normal",
    "importance": "critical",
    "enabled_runtime_harnesses": [
        "cc",
        "codex",
        "agy",
        "muse",
        "aws_kiro",
        "github_copilot",
        "custom_cli",
    ],
}


def _map_category_to_bucket(task_category: str) -> str:
    cat = task_category.strip().lower()
    if cat in {"planning_architecture_synthesis", "deep_reasoning_and_research"}:
        return "planning_reasoning"
    if cat == "browser_vla_and_automation":
        return "browser_vla_automation"
    if cat == "fast_curation_and_telemetry":
        return "fast_curation_telemetry"
    return "execution_coding_audit"


def resolve_extensible_compliance_routing(
    *,
    config_json: Optional[Path | str | Mapping[str, Any]] = None,
    input_json: Optional[Path | str | Mapping[str, Any]] = None,
    manual_set_pairs: Optional[Sequence[str]] = None,
    manual_kwargs: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve Rank-1 & Rank-2 `{backend, runtime, model, effort}` plus Inter-Runtime Synthesis under the 3-Layer Config Contract."""
    resolved = load_layered_config(
        defaults=DEFAULT_DISPATCH_CONFIG,
        config_json=config_json,
        input_json=input_json,
        manual_set_pairs=manual_set_pairs,
        manual_kwargs=manual_kwargs,
    )

    regime = str(resolved.get("compliance_regime") or "commercial_cloud").strip().lower()
    if regime not in COMPLIANCE_REGIME_CATALOG:
        raise ValueError(
            f"Unsupported compliance_regime {regime!r}; expected one of {tuple(COMPLIANCE_REGIME_CATALOG)}"
        )

    session_tier = str(resolved.get("session_tier") or "main_hub").strip().lower()
    task_category = str(resolved.get("task_category") or "planning_architecture_synthesis").strip().lower()
    complexity = str(resolved.get("complexity") or "high").strip().lower()
    urgency = str(resolved.get("urgency") or "normal").strip().lower()
    importance = str(resolved.get("importance") or "critical").strip().lower()
    enabled_harnesses = set(resolved.get("enabled_runtime_harnesses") or [])

    regime_info = COMPLIANCE_REGIME_CATALOG[regime]
    bucket = _map_category_to_bucket(task_category)
    candidates = [
        c
        for c in regime_info["tier_models"].get(bucket, [])
        if not enabled_harnesses or c["runtime"] in enabled_harnesses
    ]
    if not candidates:
        candidates = list(regime_info["tier_models"].get(bucket, []))

    rank_1 = dict(candidates[0])
    rank_2 = dict(candidates[1] if len(candidates) > 1 else candidates[0])

    # Ensure Inter-Runtime Synthesis (Composer Runtime != Counterpart Validator Runtime whenever possible)
    if rank_1["runtime"] == rank_2["runtime"]:
        for alt in candidates[2:]:
            if alt["runtime"] != rank_1["runtime"]:
                rank_2 = dict(alt)
                break

    if urgency == "immediate" and rank_1.get("effort") == "max":
        rank_1["effort"] = "high"

    r1_caps = RUNTIME_HARNESS_CAPABILITIES.get(rank_1["runtime"], {})
    r2_caps = RUNTIME_HARNESS_CAPABILITIES.get(rank_2["runtime"], {})

    return {
        "schema_version": "patchwork-extensible-compliance-routing-v1",
        "compliance_regime": regime,
        "itar_ear_restricted": regime_info["itar_ear_restricted"],
        "unavailable_models_note": regime_info["unavailable_models_note"],
        "session_tier": session_tier,
        "task_category": task_category,
        "complexity": complexity,
        "urgency": urgency,
        "importance": importance,
        "rank_1_primary": {
            "rank": 1,
            **rank_1,
            "runtime_display_name": r1_caps.get("display_name", rank_1["runtime"]),
            "runtime_strengths": r1_caps.get("unique_runtime_strengths", []),
        },
        "rank_2_counterpart": {
            "rank": 2,
            **rank_2,
            "runtime_display_name": r2_caps.get("display_name", rank_2["runtime"]),
            "runtime_strengths": r2_caps.get("unique_runtime_strengths", []),
        },
        "inter_runtime_synthesis": {
            "cross_runtime_diverse": rank_1["runtime"] != rank_2["runtime"],
            "cross_model_diverse": rank_1["model"] != rank_2["model"],
            "composer_runtime": rank_1["runtime"],
            "validator_runtime": rank_2["runtime"],
            "synthesis_mechanism": (
                f"Pairs {rank_1['runtime']} ({rank_1['model']} on {rank_1['backend']}) as Composer "
                f"with {rank_2['runtime']} ({rank_2['model']} on {rank_2['backend']}) as Counterpart Validator, "
                "combining distinct runtime harness capabilities even under restricted model pools."
            ),
        },
        "config_provenance": resolved.get("_config_provenance", {}),
    }


def plan_inter_runtime_synthesis(
    *,
    task_id: str,
    goal: str,
    parent_session_id: str,
    config_json: Optional[Path | str | Mapping[str, Any]] = None,
    input_json: Optional[Path | str | Mapping[str, Any]] = None,
    manual_set_pairs: Optional[Sequence[str]] = None,
    manual_kwargs: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a dual-seat Inter-Runtime Synthesis dispatch plan (`Composer != Validator`) under any compliance regime."""
    routing = resolve_extensible_compliance_routing(
        config_json=config_json,
        input_json=input_json,
        manual_set_pairs=manual_set_pairs,
        manual_kwargs=manual_kwargs,
    )
    r1 = routing["rank_1_primary"]
    r2 = routing["rank_2_counterpart"]

    prompt_digest = hashlib.sha256(f"{task_id}:{goal}".encode("utf-8")).hexdigest()[:16]
    return {
        "schema_version": "patchwork-inter-runtime-synthesis-plan-v1",
        "task_id": task_id,
        "goal": goal,
        "parent_session_id": parent_session_id,
        "compliance_regime": routing["compliance_regime"],
        "itar_ear_restricted": routing["itar_ear_restricted"],
        "legs": [
            {
                "leg_id": f"{task_id}-L1-COMPOSE",
                "role": "COMPOSER",
                "cloud_backend": r1["backend"],
                "runtime_harness": r1["runtime"],
                "model": r1["model"],
                "effort": r1["effort"],
                "child_session_id": f"{r1['runtime']}-child-{prompt_digest}-c1",
                "runtime_strengths": r1["runtime_strengths"],
            },
            {
                "leg_id": f"{task_id}-L2-VALIDATE",
                "role": "VALIDATOR",
                "cloud_backend": r2["backend"],
                "runtime_harness": r2["runtime"],
                "model": r2["model"],
                "effort": r2["effort"],
                "child_session_id": f"{r2['runtime']}-child-{prompt_digest}-v2",
                "runtime_strengths": r2["runtime_strengths"],
                "depends_on": [f"{task_id}-L1-COMPOSE"],
            },
        ],
        "inter_runtime_synthesis": routing["inter_runtime_synthesis"],
        "config_provenance": routing["config_provenance"],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generalized Compliance-Aware & Multi-Runtime Dispatcher (supports config.json + input.json + --set key=value)."
    )
    add_three_layer_cli_arguments(parser)
    parser.add_argument("--compliance-regime", type=str, default=None, choices=list(COMPLIANCE_REGIME_CATALOG))
    parser.add_argument("--session-tier", type=str, default=None, choices=["main_hub", "main_spoke_sub_hub"])
    parser.add_argument("--task-category", type=str, default=None)
    parser.add_argument("--complexity", type=str, default=None)
    parser.add_argument("--urgency", type=str, default=None)
    parser.add_argument("--importance", type=str, default=None)
    parser.add_argument("--task-id", type=str, default=None, help="If provided, emit an Inter-Runtime Synthesis 2-leg plan.")
    parser.add_argument("--goal", type=str, default="Execute governed task with cross-runtime verification")
    parser.add_argument("--parent-session-id", type=str, default="hub-parent-01")

    args = parser.parse_args(argv)
    kwargs = {
        "compliance_regime": args.compliance_regime,
        "session_tier": args.session_tier,
        "task_category": args.task_category,
        "complexity": args.complexity,
        "urgency": args.urgency,
        "importance": args.importance,
    }
    if args.task_id:
        out = plan_inter_runtime_synthesis(
            task_id=args.task_id,
            goal=args.goal,
            parent_session_id=args.parent_session_id,
            config_json=args.config_json,
            input_json=args.input_json,
            manual_set_pairs=args.manual_set,
            manual_kwargs=kwargs,
        )
    else:
        out = resolve_extensible_compliance_routing(
            config_json=args.config_json,
            input_json=args.input_json,
            manual_set_pairs=args.manual_set,
            manual_kwargs=kwargs,
        )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
