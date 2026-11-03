# SPDX-License-Identifier: Apache-2.0
"""Generalized Starter-Boost-Kit Persona-Agent Elicitation and Setup System for Patchwork-OS.

Uses brainstorming skills (`pwos-grilling`, `pwos-quarry`, `pwos-deconstruct`, `pwos-crucible`)
to elicit alignment across organization/company, team topology, individual working style,
task characteristics, SME domain expertise, personality/voice, background/lineage, and
open-ended `custom_facets` (not limited to predefined fields), then compiles role-disjoint
persona agent definitions and model-tier bindings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .hub_spoke_gate import resolve_canonical_three_tier_models
from .skills_registry import resolve_skill_id

BRAINSTORMING_ELICITATION_SKILLS: tuple[str, ...] = (
    "pwos-grilling",
    "pwos-quarry",
    "pwos-deconstruct",
    "pwos-crucible",
)

STARTER_ARCHETYPE_SLOTS: tuple[Dict[str, Any], ...] = (
    {
        "slot_id": "dag-planner",
        "lore_alias": "ptah-planner",
        "short_role": "planner",
        "mpt_wave": 0,
        "cognitive_stage": "planning",
        "role_tier": "composer",
        "seat_model_bucket": "fable_roles",
        "wfc_task_kind": "planning",
        "default_skills": ["pwos-wfc", "pwos-stdd"],
        "counterpart_slot": "adversarial-critic",
        "default_expertise": "DAG dependency decomposition, pre-execution contract verification, and gate placement before irreversible mutations",
        "does_not_include": ["Unreviewed direct production mutation", "Self-approving gate verdicts"],
    },
    {
        "slot_id": "domain-architect",
        "lore_alias": "mago-architect",
        "short_role": "architect",
        "mpt_wave": 0,
        "cognitive_stage": "planning",
        "role_tier": "composer",
        "seat_model_bucket": "fable_roles",
        "wfc_task_kind": "planning",
        "default_skills": ["pwos-deconstruct", "pwos-crucible"],
        "counterpart_slot": "compliance-auditor",
        "default_expertise": "Ubiquitous domain modeling, 5-Pillar structural topology, and clean-room boundary design",
        "does_not_include": ["Skipping EARS specification locks", "Bypassing counterpart critique"],
    },
    {
        "slot_id": "worktree-traverser",
        "lore_alias": "nala-traverser",
        "short_role": "traverser",
        "mpt_wave": 0,
        "cognitive_stage": "planning",
        "role_tier": "composer",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "boundary",
        "default_skills": ["pwos-deploy-cli", "pwos-wfc"],
        "counterpart_slot": "state-reconciler",
        "default_expertise": "Isolated git worktree allocation, dirty-tree protection, and cross-runtime boundary traversal",
        "does_not_include": ["Destructive reset on dirty worktrees", "Foreign session lease overwrite"],
    },
    {
        "slot_id": "epistemic-scholar",
        "lore_alias": "sejong-scholar",
        "short_role": "scholar",
        "mpt_wave": 1,
        "cognitive_stage": "reasoning",
        "role_tier": "composer",
        "seat_model_bucket": "fable_roles",
        "wfc_task_kind": "experiment",
        "default_skills": ["pwos-deconstruct", "pwos-quarry"],
        "counterpart_slot": "adversarial-critic",
        "default_expertise": "First-principles KK/KU/UK/UU epistemic deconstruction, hypothesis formulation, and lexical disambiguation",
        "does_not_include": ["Treating unverified assumptions as Known-Knowns", "Final gate sign-off"],
    },
    {
        "slot_id": "evidence-curator",
        "lore_alias": "seshat-evidence-curator",
        "short_role": "curator",
        "mpt_wave": 1,
        "cognitive_stage": "reasoning",
        "role_tier": "composer",
        "seat_model_bucket": "sonnet_roles",
        "wfc_task_kind": "evidence-curation",
        "default_skills": ["pwos-quarry", "pwos-fable-mode"],
        "counterpart_slot": "evidence-validator",
        "default_expertise": "CMDS 3-layer (raw/wiki/rules) source-manifest stewardship, claim-to-document traceability, and zero-leak curation",
        "does_not_include": ["Eligibility verdicts", "Lifecycle state mutation without audit"],
    },
    {
        "slot_id": "ast-instrumenter",
        "lore_alias": "chilseong-instrumenter",
        "short_role": "instrumenter",
        "mpt_wave": 1,
        "cognitive_stage": "reasoning",
        "role_tier": "composer",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "telemetry",
        "default_skills": ["pwos-rea", "pwos-systematic-debugging"],
        "counterpart_slot": "mutation-crafttester",
        "default_expertise": "Empirical AST codemap extraction, telemetry routing, and non-mutating sensor classification",
        "does_not_include": ["Speculative extrapolation without sensor data", "Promoting advisory sensors to authority"],
    },
    {
        "slot_id": "adversarial-critic",
        "lore_alias": "loki-flyter",
        "short_role": "critic",
        "mpt_wave": 2,
        "cognitive_stage": "adversarial_triage",
        "role_tier": "validator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "design-review",
        "default_skills": ["pwos-crucible", "pwos-grilling"],
        "counterpart_slot": "dag-planner",
        "default_expertise": "Adversarial hypothesis attack, seeded-flaw detection, and premise falsification",
        "does_not_include": ["Performative agreement", "Authoring the primary implementation"],
    },
    {
        "slot_id": "compliance-auditor",
        "lore_alias": "haechi-compliance-auditor",
        "short_role": "auditor",
        "mpt_wave": 2,
        "cognitive_stage": "adversarial_triage",
        "role_tier": "validator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "authority",
        "default_skills": ["pwos-fable-mode", "pwos-crucible"],
        "counterpart_slot": "domain-architect",
        "default_expertise": "Evidence-to-rule binding, PreToolUse hook contract compliance, and Tier-0/1/2 ladder enforcement",
        "does_not_include": ["Inventing unstated rules", "Mutating production code"],
    },
    {
        "slot_id": "state-reconciler",
        "lore_alias": "heimdall-adversarial-reconciler",
        "short_role": "reconciler",
        "mpt_wave": 2,
        "cognitive_stage": "adversarial_triage",
        "role_tier": "validator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "state-reconciliation",
        "default_skills": ["pwos-rea", "pwos-fable-mode"],
        "counterpart_slot": "worktree-traverser",
        "default_expertise": "Multi-store state reconciliation, add/add merge conflict detection, and mirror parity verification",
        "does_not_include": ["Silent delete-on-absent overwrites", "Unverified state promotion"],
    },
    {
        "slot_id": "mutation-crafttester",
        "lore_alias": "sindri-crafttester",
        "short_role": "tester",
        "mpt_wave": 2,
        "cognitive_stage": "adversarial_triage",
        "role_tier": "validator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "implementation",
        "default_skills": ["pwos-tdd", "pwos-stdd", "pwos-systematic-debugging"],
        "counterpart_slot": "ast-instrumenter",
        "default_expertise": "RED-GREEN-REFACTOR TDD discipline, mutation testing resistance, and boundary regression verification",
        "does_not_include": ["Deleting failing assertions to turn suites green", "Skipping RED verification"],
    },
    {
        "slot_id": "dialectic-synthesizer",
        "lore_alias": "thoth-synthesizer",
        "short_role": "synthesizer",
        "mpt_wave": 3,
        "cognitive_stage": "synthesizing_and_orchestrating",
        "role_tier": "synthesizer",
        "seat_model_bucket": "fable_roles",
        "wfc_task_kind": "synthesis",
        "default_skills": ["pwos-wfc", "pwos-fable-mode"],
        "counterpart_slot": "adversarial-critic",
        "default_expertise": "Synergetic assimilation + counterpart limit coverage across Workflow, Meta-Prompting, Graph-Prompting, and Prompt-Flow",
        "does_not_include": ["Smoothing over verified contradictions with vague prose", "Dropping minority counter-evidence"],
    },
    {
        "slot_id": "workflow-synthesizer",
        "lore_alias": "mimir-synthesizer",
        "short_role": "synthesizer",
        "mpt_wave": 3,
        "cognitive_stage": "synthesizing_and_orchestrating",
        "role_tier": "synthesizer",
        "seat_model_bucket": "fable_roles",
        "wfc_task_kind": "synthesis",
        "default_skills": ["pwos-wfc", "pwos-stdd"],
        "counterpart_slot": "state-reconciler",
        "default_expertise": "Cross-wave state synthesis and prompt-flow handoff consolidation without premise compromise",
        "does_not_include": ["Bypassing predecessor wave readiness checks"],
    },
    {
        "slot_id": "evidence-validator",
        "lore_alias": "jaya-vijaya-evidence-validator",
        "short_role": "validator",
        "mpt_wave": 4,
        "cognitive_stage": "meta_evaluating",
        "role_tier": "meta_evaluator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "final-validation",
        "default_skills": ["pwos-fable-mode", "pwos-tdd"],
        "counterpart_slot": "evidence-curator",
        "default_expertise": "Independent meta-evaluation of 4-way role separation, 3xPR/FRR completeness, and cryptographic receipt binding",
        "does_not_include": ["Self-certifying unrun checks", "Ingesting raw uncurated evidence"],
    },
    {
        "slot_id": "delivery-witness",
        "lore_alias": "hanuman-delivery-witness",
        "short_role": "witness",
        "mpt_wave": 4,
        "cognitive_stage": "meta_evaluating",
        "role_tier": "meta_evaluator",
        "seat_model_bucket": "sonnet_roles",
        "wfc_task_kind": "delivery-witness",
        "default_skills": ["pwos-fable-mode", "pwos-rea"],
        "counterpart_slot": "worktree-traverser",
        "default_expertise": "Consumer deliverable witness verification, lease hygiene, and terminal receipt attestation",
        "does_not_include": ["Certifying dry-run plans as delivered artifacts"],
    },
    {
        "slot_id": "sovereign-meta-evaluator",
        "lore_alias": "sovereign-orchestrator",
        "short_role": "main",
        "mpt_wave": 4,
        "cognitive_stage": "meta_evaluating",
        "role_tier": "meta_evaluator",
        "seat_model_bucket": "opus_roles",
        "wfc_task_kind": "authority",
        "default_skills": ["pwos-fable-mode", "pwos-wfc", "pwos-persona-agent"],
        "counterpart_slot": "adversarial-critic",
        "default_expertise": "Main-Hub sovereign meta-evaluation, authority-hierarchy alignment, and multi-spoke convergence",
        "does_not_include": ["Overriding explicit operator Tier-1 orders"],
    },
)


@dataclass(frozen=True)
class PersonaAlignmentProfile:
    """Multi-facet alignment profile elicited via brainstorming skills (`grilling`, `quarry`, `deconstruct`, `crucible`).

    Includes organization, team, individual, task characteristics, SME expertise,
    personality/voice, background/lineage, and open-ended `custom_facets` (not limited
    to fixed fields).
    """

    persona_slug: str
    slot_id: str
    display_title: str
    organization_context: Dict[str, Any] = field(default_factory=dict)
    team_topology: Dict[str, Any] = field(default_factory=dict)
    individual_preferences: Dict[str, Any] = field(default_factory=dict)
    task_characteristics: Dict[str, Any] = field(default_factory=dict)
    domain_expertise: List[str] = field(default_factory=list)
    does_not_include: List[str] = field(default_factory=list)
    personality_and_voice: Dict[str, Any] = field(default_factory=dict)
    background_and_lineage: Dict[str, Any] = field(default_factory=dict)
    elicited_by_skills: List[str] = field(
        default_factory=lambda: list(BRAINSTORMING_ELICITATION_SKILLS)
    )
    custom_facets: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_slug": self.persona_slug,
            "slot_id": self.slot_id,
            "display_title": self.display_title,
            "organization_context": dict(self.organization_context),
            "team_topology": dict(self.team_topology),
            "individual_preferences": dict(self.individual_preferences),
            "task_characteristics": dict(self.task_characteristics),
            "domain_expertise": list(self.domain_expertise),
            "does_not_include": list(self.does_not_include),
            "personality_and_voice": dict(self.personality_and_voice),
            "background_and_lineage": dict(self.background_and_lineage),
            "elicited_by_skills": list(self.elicited_by_skills),
            "custom_facets": dict(self.custom_facets),
        }


def elicit_persona_alignment_from_brainstorming(
    *,
    persona_slug: str,
    slot_id: str,
    display_title: Optional[str] = None,
    organization_context: Optional[Mapping[str, Any]] = None,
    team_topology: Optional[Mapping[str, Any]] = None,
    individual_preferences: Optional[Mapping[str, Any]] = None,
    task_characteristics: Optional[Mapping[str, Any]] = None,
    domain_expertise: Optional[Sequence[str]] = None,
    does_not_include: Optional[Sequence[str]] = None,
    personality_and_voice: Optional[Mapping[str, Any]] = None,
    background_and_lineage: Optional[Mapping[str, Any]] = None,
    elicited_by_skills: Optional[Sequence[str]] = None,
    custom_facets: Optional[Mapping[str, Any]] = None,
) -> PersonaAlignmentProfile:
    """Build a validated `PersonaAlignmentProfile` from brainstorming outputs (`grilling`/`quarry`/`crucible`)."""
    slug = persona_slug.strip()
    if not slug:
        raise ValueError("persona_slug must be non-empty")
    slot_lookup = {s["slot_id"]: s for s in STARTER_ARCHETYPE_SLOTS}
    lore_lookup = {s["lore_alias"]: s for s in STARTER_ARCHETYPE_SLOTS}
    archetype = slot_lookup.get(slot_id) or lore_lookup.get(slot_id)
    if archetype is None:
        raise KeyError(f"Unknown starter archetype slot_id: {slot_id!r}")

    skills = [
        resolve_skill_id(sk)
        for sk in (elicited_by_skills or BRAINSTORMING_ELICITATION_SKILLS)
    ]
    expertise = list(domain_expertise or [archetype["default_expertise"]])
    exclusions = list(does_not_include or archetype["does_not_include"])

    return PersonaAlignmentProfile(
        persona_slug=slug,
        slot_id=archetype["slot_id"],
        display_title=display_title or slug.replace("-", " ").title(),
        organization_context=dict(
            organization_context
            or {
                "domain": "generalized-engineering",
                "compliance_boundary": "clean-room-zero-leak",
                "architecture_paradigm": "hub-spoke-cmds-3layer",
            }
        ),
        team_topology=dict(
            team_topology
            or {
                "role_orthogonality": "Composer != Validator != Synthesizer != Meta-Evaluator",
                "counterpart_slot": archetype["counterpart_slot"],
            }
        ),
        individual_preferences=dict(
            individual_preferences
            or {
                "communication_style": "evidence-first-zero-sycophancy",
                "explain_while_executing": True,
            }
        ),
        task_characteristics=dict(
            task_characteristics
            or {
                "cognitive_stage": archetype["cognitive_stage"],
                "wfc_task_kind": archetype["wfc_task_kind"],
                "verification_gate": "Tier-0 AST/Lint -> Tier-1 Zero-Thinking -> Tier-2 Counterpart Escalation",
            }
        ),
        domain_expertise=expertise,
        does_not_include=exclusions,
        personality_and_voice=dict(
            personality_and_voice
            or {
                "stance": "falsification-first" if archetype["role_tier"] == "validator" else "constructive-rigor",
                "tone": "concise-analytic",
            }
        ),
        background_and_lineage=dict(
            background_and_lineage
            or {
                "starter_slot": archetype["slot_id"],
                "lore_alias": archetype["lore_alias"],
                "cognitive_wave": archetype["mpt_wave"],
            }
        ),
        elicited_by_skills=skills,
        custom_facets=dict(custom_facets or {}),
    )


def synthesize_persona_agent(
    profile: PersonaAlignmentProfile,
    *,
    registry_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Synthesize a portable `.agents/agents/<slug>.md` definition and model-tier binding from a `PersonaAlignmentProfile`."""
    slot_lookup = {s["slot_id"]: s for s in STARTER_ARCHETYPE_SLOTS}
    archetype = slot_lookup[profile.slot_id]

    models_3tier = resolve_canonical_three_tier_models(
        cognitive_stage=archetype["cognitive_stage"],
        registry_path=registry_path,
    )
    bucket = archetype["seat_model_bucket"]
    if bucket == "fable_roles":
        tier_idx = 0
    elif bucket == "sonnet_roles":
        tier_idx = 2
    else:
        tier_idx = 1 if archetype["cognitive_stage"] in {"planning", "reasoning"} else 0

    exec_3tier = resolve_canonical_three_tier_models(
        cognitive_stage="adversarial_triage",
        registry_path=registry_path,
    )
    if bucket == "fable_roles":
        cc_model = models_3tier["cc"]["selected_models"][0]
        codex_model = models_3tier["codex"]["selected_models"][0]
        agy_model = models_3tier["agy"]["selected_models"][0]
        muse_model = models_3tier["muse"]["selected_models"][0]
    elif bucket == "sonnet_roles":
        cc_model = models_3tier["cc"]["selected_models"][2]
        codex_model = models_3tier["codex"]["selected_models"][2]
        agy_model = models_3tier["agy"]["selected_models"][2]
        muse_model = models_3tier["muse"]["selected_models"][2]
    else:
        cc_model = exec_3tier["cc"]["selected_models"][0]
        codex_model = exec_3tier["codex"]["selected_models"][1]
        agy_model = exec_3tier["agy"]["selected_models"][0]
        muse_model = exec_3tier["muse"]["selected_models"][0]

    markdown_lines = [
        "---",
        f"name: {profile.persona_slug}",
        f"slot_id: {profile.slot_id}",
        f"short_role: {archetype['short_role']}",
        f"role_tier: {archetype['role_tier']}",
        f"cognitive_stage: {archetype['cognitive_stage']}",
        f"mpt_wave: {archetype['mpt_wave']}",
        f"seat_model_bucket: {bucket}",
        f"counterpart_slot: {archetype['counterpart_slot']}",
        "elicited_by_skills:",
    ]
    for sk in profile.elicited_by_skills:
        markdown_lines.append(f"  - {sk}")
    markdown_lines.extend(
        [
            "---",
            "",
            f"# {profile.display_title} ({profile.persona_slug})",
            "",
            "## 1. Domain Expertise and Mission",
        ]
    )
    for exp in profile.domain_expertise:
        markdown_lines.append(f"- {exp}")
    markdown_lines.extend(
        [
            "",
            "## 2. Explicit Anti-Scope (Does Not Include)",
        ]
    )
    for exc in profile.does_not_include:
        markdown_lines.append(f"- {exc}")
    markdown_lines.extend(
        [
            "",
            "## 3. Alignment Context (Organization, Team, Individual, Task)",
            f"- **Organization Context**: `{json.dumps(profile.organization_context, ensure_ascii=False, sort_keys=True)}`",
            f"- **Team Topology**: `{json.dumps(profile.team_topology, ensure_ascii=False, sort_keys=True)}`",
            f"- **Individual Preferences**: `{json.dumps(profile.individual_preferences, ensure_ascii=False, sort_keys=True)}`",
            f"- **Task Characteristics**: `{json.dumps(profile.task_characteristics, ensure_ascii=False, sort_keys=True)}`",
            f"- **Personality & Voice**: `{json.dumps(profile.personality_and_voice, ensure_ascii=False, sort_keys=True)}`",
            f"- **Background & Lineage**: `{json.dumps(profile.background_and_lineage, ensure_ascii=False, sort_keys=True)}`",
            f"- **Custom Open-Ended Facets**: `{json.dumps(profile.custom_facets, ensure_ascii=False, sort_keys=True)}`",
            "",
        ]
    )
    markdown_text = "\n".join(markdown_lines)

    return {
        "persona_slug": profile.persona_slug,
        "slot_id": profile.slot_id,
        "lore_alias": archetype["lore_alias"],
        "short_role": archetype["short_role"],
        "role_tier": archetype["role_tier"],
        "cognitive_stage": archetype["cognitive_stage"],
        "mpt_wave": archetype["mpt_wave"],
        "wfc_task_kind": archetype["wfc_task_kind"],
        "seat_model_bucket": bucket,
        "tier_index": tier_idx,
        "governing_skills": list(archetype["default_skills"]),
        "elicited_by_skills": list(profile.elicited_by_skills),
        "counterpart_slot": archetype["counterpart_slot"],
        "recommended_models_by_runtime": {
            "cc": cc_model,
            "codex": codex_model,
            "agy": agy_model,
            "muse": muse_model,
        },
        "alignment_profile": profile.to_dict(),
        "markdown": markdown_text,
        "markdown_sha256": f"sha256:{hashlib.sha256(markdown_text.encode('utf-8')).hexdigest()}",
    }


def bootstrap_persona_starter_kit(
    target_root: Path,
    *,
    use_lore_names: bool = False,
    organization_context: Optional[Mapping[str, Any]] = None,
    team_topology: Optional[Mapping[str, Any]] = None,
    individual_preferences: Optional[Mapping[str, Any]] = None,
    task_characteristics: Optional[Mapping[str, Any]] = None,
    custom_facets_by_slot: Optional[Mapping[str, Mapping[str, Any]]] = None,
    registry_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Bootstrap the generalized Starter-Boost-Kit persona roster into `<target_root>/.agents/agents/`."""
    root = Path(target_root).resolve()
    agents_dir = root / ".agents" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    synthesized_roster: List[Dict[str, Any]] = []
    fable_roles: List[str] = []
    opus_roles: List[str] = []
    sonnet_roles: List[str] = []

    for arch in STARTER_ARCHETYPE_SLOTS:
        slug = arch["lore_alias"] if use_lore_names else arch["slot_id"]
        slot_custom = (custom_facets_by_slot or {}).get(arch["slot_id"]) or (
            custom_facets_by_slot or {}
        ).get(slug)
        profile = elicit_persona_alignment_from_brainstorming(
            persona_slug=slug,
            slot_id=arch["slot_id"],
            organization_context=organization_context,
            team_topology=team_topology,
            individual_preferences=individual_preferences,
            task_characteristics=task_characteristics,
            custom_facets=slot_custom,
        )
        item = synthesize_persona_agent(profile, registry_path=registry_path)
        agent_file = agents_dir / f"{slug}.md"
        agent_file.write_text(item["markdown"], encoding="utf-8", newline="\n")
        item["agent_file"] = agent_file.as_posix()
        synthesized_roster.append(item)

        sr = arch["short_role"]
        if arch["seat_model_bucket"] == "fable_roles" and sr not in fable_roles:
            fable_roles.append(sr)
        elif arch["seat_model_bucket"] == "sonnet_roles" and sr not in sonnet_roles:
            sonnet_roles.append(sr)
        elif arch["seat_model_bucket"] == "opus_roles" and sr not in opus_roles:
            opus_roles.append(sr)

    seat_tier_config = {
        "schema_version": 1,
        "fable_roles": fable_roles,
        "sonnet_roles": sonnet_roles,
        "opus_roles": opus_roles,
        "unregistered_role": "allow",
    }
    seat_tier_path = root / "config" / "runtime-hooks" / "seat-model-tier.json"
    seat_tier_path.parent.mkdir(parents=True, exist_ok=True)
    seat_tier_path.write_text(
        json.dumps(seat_tier_config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return {
        "schema_version": "patchwork-persona-starter-kit-v1",
        "persona_count": len(synthesized_roster),
        "use_lore_names": use_lore_names,
        "agents_dir": agents_dir.as_posix(),
        "seat_model_tier_path": seat_tier_path.as_posix(),
        "seat_model_tier": seat_tier_config,
        "roster": synthesized_roster,
    }
