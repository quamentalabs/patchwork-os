# SPDX-License-Identifier: Apache-2.0
"""Unit and adversarial regression tests for Patchwork-OS Hub-Spoke Gate, EARS Spec, and Tessellation."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from patchwork_os.hub_spoke_gate import (
    bootstrap_agnostic_hub,
    build_deterministic_payload,
    build_tessellation_plan,
    evaluate_zero_thinking_gate,
    extract_python_ast_summary,
    generate_lease_token,
    safe_bind_spoke,
    validate_ears_spec_bundle,
    verify_five_role_orthogonality,
    verify_lease_token,
    verify_task_contract_template,
)


def test_five_role_orthogonality_enforces_disjoint_agents() -> None:
    valid_roster = {
        "COMPOSER": "claude-code-primary",
        "CRITICIZER": "codex-counterpart",
        "VALIDATOR": "kiro-spec-gate",
        "SYNTHESIZER": "flash-harvester",
        "META_EVALUATOR": "muse-auditor",
    }
    res = verify_five_role_orthogonality(valid_roster)
    assert res["valid"] is True
    assert res["collisions"] == []

    colliding_roster = dict(valid_roster, CRITICIZER="claude-code-primary")
    bad = verify_five_role_orthogonality(colliding_roster)
    assert bad["valid"] is False
    assert any("ROLE_ORTHOGONALITY_COLLISION" in r for r in bad["reasons"])


def test_hmac_lease_token_and_task_contract_enforcer() -> None:
    secret = b"fixture-only-explicit-key-not-for-production"
    token = generate_lease_token("TASK-001", "COMPOSER", "cc-agent", "a1b2c3d4e5f6", secret=secret)
    assert verify_lease_token(
        token,
        task_id="TASK-001",
        role="COMPOSER",
        agent_id="cc-agent",
        diff_hash="a1b2c3d4e5f6",
        secret=secret,
    )
    assert not verify_lease_token(
        token,
        task_id="TASK-001",
        role="VALIDATOR",
        agent_id="cc-agent",
        diff_hash="a1b2c3d4e5f6",
        secret=secret,
    )

    completed_md = f"""---
task_id: "TASK-001"
lease_token: "{token}"
composer_agent: "cc-agent"
criticizer_agent: "codex-agent"
validator_agent: "kiro-agent"
synthesizer_agent: "flash-agent"
meta_evaluator_agent: "muse-agent"
---
## 1. Epistemic Matrix (KK / KU / UK / UU)
- KK: Verified AST spans.
## 2. Synergetic Assimilation & Counterpart Limit Coverage
- Synthesized hybrid design.
## 3. 3xPR Gate
- [x] PR-1, PR-2, PR-3 verified.
## 4. FRR (Forward / Reverse / Roundtrip)
- Forward: contract validation. Reverse: reject self-approval. Roundtrip: read back the result.
"""
    report = verify_task_contract_template(completed_md, require_completed=True)
    assert report["valid"] is True, report["reasons"]

    self_approved_md = completed_md.replace('criticizer_agent: "codex-agent"', 'criticizer_agent: "cc-agent"')
    bad_report = verify_task_contract_template(self_approved_md, require_completed=True)
    assert bad_report["valid"] is False
    assert any("ORTHOGONALITY_VIOLATION_COMPOSER_EQUALS_CRITICIZER" in r for r in bad_report["reasons"])


def test_safe_bind_spoke_and_bootstrap_preserve_source_on_rebind(tmp_path: Path) -> None:
    src_dir = tmp_path / "source_dir"
    src_dir.mkdir()
    sentinel = src_dir / "keep.txt"
    sentinel.write_text("important-data\n", encoding="utf-8")

    dst_dir = tmp_path / "spoke_dir"
    first = safe_bind_spoke(src_dir, dst_dir, is_dir=True)
    assert first["tier"] in ("SYMLINK", "NTFS_JUNCTION", "ATOMIC_COPY_FALLBACK")
    assert (dst_dir / "keep.txt").read_text(encoding="utf-8") == "important-data\n"

    # Re-binding must never delete the target contents (`GDOC-BUG-01` regression guard)
    second = safe_bind_spoke(src_dir, dst_dir, is_dir=True)
    assert second["tier"] in ("SYMLINK", "NTFS_JUNCTION", "PRESERVED_EXISTING")
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "important-data\n"

    existing_claude = tmp_path / "CLAUDE.md"
    existing_claude.write_text("# Existing Repo Rules\n", encoding="utf-8")
    manifest = bootstrap_agnostic_hub(tmp_path, overwrite_existing_root_docs=False)
    assert manifest["spokes"]["CLAUDE.md"]["tier"] == "PRESERVED_EXISTING"
    assert existing_claude.read_text(encoding="utf-8") == "# Existing Repo Rules\n"


def test_validate_ears_spec_bundle(tmp_path: Path) -> None:
    spec_dir = tmp_path / ".kiro" / "specs" / "hybrid-gate"
    spec_dir.mkdir(parents=True)
    (spec_dir / "requirements.md").write_text(
        "# Requirements\n- WHEN a file is saved THE SYSTEM SHALL run Tier-0 AST checks.\n",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        "# Design\n```mermaid\nflowchart TD\n  A[\"Save\"] --> B[\"Tier 0 Gate\"]\n```\n",
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        "# Tasks\n- [x] Implement AST summary extractor\n- [ ] Add unit tests\n",
        encoding="utf-8",
    )
    res = validate_ears_spec_bundle(spec_dir)
    assert res["valid"] is True
    assert res["ears_clause_count"] == 1
    assert res["task_count"] == 2


def test_zero_thinking_gate_blocks_bare_except_and_routes_ambiguous(tmp_path: Path) -> None:
    bad_py = tmp_path / "bad_service.py"
    bad_py.write_text(
        "def process_order(order_id: int):\n"
        "    try:\n"
        "        return order_id + 1\n"
        "    except:\n"
        "        return 0\n",
        encoding="utf-8",
    )
    summary = extract_python_ast_summary(bad_py)
    assert summary["functions"][0]["bare_excepts"] == 1
    assert summary["functions"][0]["typed_return"] is False

    payload = build_deterministic_payload(
        tmp_path,
        changed_files_override=["bad_service.py"],
        raw_diff_override="+except:\n",
    )
    verdict = evaluate_zero_thinking_gate(payload)
    assert verdict.verdict == "FAIL"
    assert verdict.thinking_enabled is False
    assert "BARE_EXCEPT_FORBIDDEN" in (verdict.violated_invariant or "")

    clean_py = tmp_path / "clean_service.py"
    clean_py.write_text(
        "def process_order(order_id: int) -> int:\n"
        "    return order_id + 1\n",
        encoding="utf-8",
    )
    amb_payload = build_deterministic_payload(
        tmp_path,
        changed_files_override=["src/schemas/contract.py", "clean_service.py"],
        raw_diff_override="+class OrderContract: pass\n",
    )
    amb_verdict = evaluate_zero_thinking_gate(amb_payload)
    assert amb_verdict.verdict == "AMBIGUOUS"
    assert amb_verdict.escalate_to == "PLANNER_VALIDATOR"


def test_build_tessellation_plan_has_five_ordered_phases() -> None:
    plan = build_tessellation_plan("TASK-20261023", "src/patchwork_os")
    assert len(plan["phases"]) == 5
    assert [p["mode"] for p in plan["phases"]] == [
        "SERIAL",
        "PARALLEL_TESSELLATION",
        "SERIAL_PARALLEL_CROSS",
        "SERIAL_GATE",
        "ASYNC_PARALLEL",
    ]
    assert set(plan["canonical_three_tier_models"]) == {"cc", "codex", "agy", "muse"}
    assert all(len(v) == 3 for v in plan["canonical_three_tier_models"].values())


def test_resolve_canonical_three_tier_models_deduplicates_codex_slots_and_projects_agy_tiers() -> None:
    from patchwork_os.hub_spoke_gate import resolve_canonical_three_tier_models

    def _s(*parts: str) -> str:
        return "-".join(parts)

    live_catalogs = {
        "cc": ["opus", "fable-5-1", "sonnet", "haiku"],
        "codex": [
            _s("gpt", "6.1", "sol"),
            _s("gpt", "6", "astra"),
            _s("gpt", "6", "sol"),
            _s("gpt", "6", "luna"),
            _s("gpt", "5.6", "sol"),
            _s("gpt", "5.6", "terra"),
            _s("gpt", "5.6", "luna"),
        ],
        "agy": [
            _s("gemini", "4", "argon"),
            _s("gemini", "4", "argon", "high"),
            _s("gemini", "4", "argon", "medium"),
            _s("gemini", "4", "argon", "low"),
            _s("gemini", "3.8", "flash", "high"),
            _s("gemini", "3.8", "flash", "medium"),
            _s("gemini", "3.8", "flash", "low"),
            _s("gemini", "3.7", "pro", "high"),
            _s("claude", "opus", "5", "5", "high"),
        ],
        "muse": [
            _s("muse", "wonder", "full", "1.0"),
            _s("muse", "wonder", "1.0"),
            _s("muse", "spark", "1.3"),
            _s("muse", "spark", "1.2"),
            _s("muse", "contributor", "1.3"),
        ],
    }

    res = resolve_canonical_three_tier_models(live_catalogs)
    assert res["cc"]["policy"] == "3_TIER_DIRECT"
    assert res["cc"]["selected_models"] == ["fable-5-1", "opus", "sonnet"]
    assert res["cc"]["selected_models_by_axis"]["planning_reasoning_synthesis"] == [
        "fable-5-1",
        "opus",
        "sonnet",
    ]
    assert res["cc"]["selected_models_by_axis"]["execution_validation_coding"] == [
        "opus",
        "fable-5-1",
        "sonnet",
    ]

    res_exec = resolve_canonical_three_tier_models(
        live_catalogs, cognitive_stage="adversarial_triage"
    )
    assert res_exec["cc"]["selected_models"] == ["opus", "fable-5-1", "sonnet"]

    assert res["codex"]["policy"] == "3_TIER_SLOT_DEDUP"
    assert res["codex"]["selected_models"] == [
        _s("gpt", "6", "astra"),
        _s("gpt", "6.1", "sol"),
        _s("gpt", "6", "luna"),
    ]
    assert _s("gpt", "6", "sol") in res["codex"]["superseded_slot_duplicates"]["sol"]
    assert _s("gpt", "5.6", "sol") in res["codex"]["superseded_slot_duplicates"]["sol"]

    assert res["agy"]["policy"] == "2_GEN_TO_3_TIER_PROJECTION"
    assert res["agy"]["selected_models"] == [
        _s("gemini", "4", "argon", "high"),
        _s("gemini", "4", "argon"),
        _s("gemini", "3.8", "flash", "high"),
    ]

    assert res["muse"]["policy"] == "3_TIER_DIRECT"
    assert res["muse"]["selected_models"] == [
        _s("muse", "wonder", "full", "1.0"),
        _s("muse", "wonder", "1.0"),
        _s("muse", "spark", "1.3"),
    ]



def test_cc_model_ids_preserved_from_registry_and_live(tmp_path: Path) -> None:
    import json
    from patchwork_os.hub_spoke_gate import resolve_canonical_three_tier_models

    # 5-2 is a synthetic fixture, distinct from the 5-1 fallback.
    cases = [
        (["claude-fable-5-2", "claude-opus-5-5", "claude-sonnet-5-1"],
         ["claude-fable-5-2", "claude-opus-5-5", "claude-sonnet-5-1"]),
        (["claude-fable-5-1", "opus", "sonnet"], ["claude-fable-5-1", "opus", "sonnet"]),
        (["fable", "opus", "sonnet"], ["fable", "opus", "sonnet"]),
        (["fable-5-1", "opus-5-5", "sonnet-5-1"], ["fable-5-1", "opus-5-5", "sonnet-5-1"]),
        (["haiku", "opus", "sonnet"], ["claude-fable-5-1", "opus", "sonnet"]),
    ]
    registry = tmp_path / "models.json"
    for source in ("registry", "live"):
        for catalog, expected in cases:
            registered = catalog if source == "registry" else [
                "claude-fable-4-1", "claude-opus-4-1", "claude-sonnet-4-1"]
            registry.write_text(json.dumps({"runtimes": {"cc": {"canonical_3tier": registered}}}),
                                encoding="utf-8")
            live = {"cc": catalog} if source == "live" else None
            resolved = resolve_canonical_three_tier_models(live, registry_path=registry)["cc"]
            execution = [expected[1], expected[0], expected[2]]
            assert resolved["selected_models"] == expected
            assert resolved["selected_models_by_axis"] == {
                "planning_reasoning_synthesis": expected, "execution_validation_coding": execution}
            for stage in ("execution", "validation", "coding", "adversarial_triage", "meta_evaluating"):
                routed = resolve_canonical_three_tier_models(
                    live, cognitive_stage=stage, registry_path=registry)["cc"]
                assert routed["selected_models"] == execution
                assert routed["tier_slots"] == ["opus", "fable", "sonnet"]


def test_cc_model_versions_compare_numerically_and_preserve_ids(tmp_path: Path) -> None:
    from patchwork_os.hub_spoke_gate import resolve_canonical_three_tier_models

    catalog = ["claude-fable-5-9", "fable-5-10", "claude-opus-5-10", "opus-5-9",
               "sonnet-5-10", "claude-sonnet-5-9"]
    resolved = resolve_canonical_three_tier_models(
        {"cc": catalog}, registry_path=tmp_path / "absent-registry.json")["cc"]
    assert resolved["selected_models"] == ["fable-5-10", "claude-opus-5-10", "sonnet-5-10"]
    assert resolved["selected_models_by_axis"]["execution_validation_coding"] == [
        "claude-opus-5-10", "fable-5-10", "sonnet-5-10"]


def test_build_vla_wfc_mpt_hub_spoke_map_links_vla_personas_skills_and_memory() -> None:
    from patchwork_os.hub_spoke_gate import build_vla_wfc_mpt_hub_spoke_map

    hub_map = build_vla_wfc_mpt_hub_spoke_map()
    assert hub_map["schema_version"] == "patchwork-vla-wfc-mpt-hub-spoke-v1"
    assert hub_map["canonical_three_tier_models"]["cc"] == ["claude-fable-5-1", "opus", "sonnet"]
    assert hub_map["cognitive_axis_routing"]["planning_reasoning_synthesis"]["cc"] == [
        "claude-fable-5-1",
        "opus",
        "sonnet",
    ]
    assert hub_map["cognitive_axis_routing"]["execution_validation_coding"]["cc"] == [
        "opus",
        "claude-fable-5-1",
        "sonnet",
    ]
    matrix = {row["persona"]: row for row in hub_map["wfc_mpt_persona_skill_matrix"]}
    assert len(matrix) == 15
    assert matrix["ptah-planner"]["recommended_models_by_runtime"]["cc"] == "claude-fable-5-1"
    assert matrix["thoth-synthesizer"]["recommended_models_by_runtime"]["cc"] == "claude-fable-5-1"
    assert matrix["sejong-scholar"]["recommended_models_by_runtime"]["cc"] == "claude-fable-5-1"
    assert matrix["loki-flyter"]["recommended_models_by_runtime"]["cc"] == "opus"
    assert matrix["jaya-vijaya-evidence-validator"]["recommended_models_by_runtime"]["cc"] == "opus"
    assert matrix["seshat-evidence-curator"]["recommended_models_by_runtime"]["cc"] == "sonnet"
    assert matrix["hanuman-delivery-witness"]["recommended_models_by_runtime"]["cc"] == "sonnet"
    assert "knowledge/wiki/patchwork-os-architecture.md" in (
        hub_map["hub_spoke_interlinks"]["memory_vault_spokes"]
    )
    assert "skills/pwos-persona-agent/SKILL.md" in (
        hub_map["hub_spoke_interlinks"]["patchwork_os_generalized_skills"]
    )
    assert "skills/pwos-deploy-cli/SKILL.md" in (
        hub_map["hub_spoke_interlinks"]["patchwork_os_generalized_skills"]
    )
    assert len(hub_map["orchestrator_session_routing_table"]) == 10



def test_public_map_references_only_repository_contained_files() -> None:
    from pathlib import PurePosixPath, PureWindowsPath
    from patchwork_os.hub_spoke_gate import build_vla_wfc_mpt_hub_spoke_map

    hub_map = build_vla_wfc_mpt_hub_spoke_map()
    interlinks = hub_map["hub_spoke_interlinks"]
    references = [
        (group, path)
        for group, paths in interlinks.items()
        for path in paths
    ]
    for row in hub_map["wfc_mpt_persona_skill_matrix"]:
        assert row["governing_skills"], row["persona"]
        references.extend((row["persona"], path) for path in row["governing_skills"])
    assert references
    for group, raw in references:
        assert isinstance(raw, str) and raw, group
        posix = PurePosixPath(raw)
        windows = PureWindowsPath(raw)
        assert not posix.is_absolute() and not windows.drive, (group, raw)
        assert "\\" not in raw and ".." not in posix.parts, (group, raw)
        resolved = (ROOT / raw).resolve()
        assert resolved.is_relative_to(ROOT.resolve()), (group, raw)
        assert resolved.is_file(), (group, raw)

    available_skills = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "skills").glob("pwos-*/SKILL.md")
    }
    assert set(interlinks["patchwork_os_generalized_skills"]) == available_skills

def test_starter_boost_kit_persona_setup_and_custom_facets(tmp_path: Path) -> None:
    from patchwork_os.persona_setup import (
        bootstrap_persona_starter_kit,
        elicit_persona_alignment_from_brainstorming,
        synthesize_persona_agent,
    )

    profile = elicit_persona_alignment_from_brainstorming(
        persona_slug="robotics-controls-architect",
        slot_id="domain-architect",
        display_title="Robotics Controls & MDAO Architect",
        organization_context={"industry": "aerospace-robotics", "safety_standard": "DO-178C"},
        team_topology={"squad": "autonomy-core", "review_policy": "cross-family-2-stage"},
        individual_preferences={"language": "ko", "style": "concise-first-principles"},
        task_characteristics={"complexity": "high", "urgency": "normal", "importance": "critical"},
        domain_expertise=["Actuator control loops", "CasADi trajectory optimization"],
        does_not_include=["Unverified firmware flashing"],
        personality_and_voice={"stance": "dialectic-rigor", "tone": "direct"},
        background_and_lineage={"archetype": "systems-theorist"},
        elicited_by_skills=["grilling", "quarry", "deconstruct", "crucible"],
        custom_facets={"hardware_in_the_loop_required": True, "latency_budget_ms": 2.0},
    )
    agent = synthesize_persona_agent(profile)
    assert agent["persona_slug"] == "robotics-controls-architect"
    assert agent["slot_id"] == "domain-architect"
    assert agent["recommended_models_by_runtime"]["cc"] == "claude-fable-5-1"
    assert agent["alignment_profile"]["custom_facets"]["hardware_in_the_loop_required"] is True
    assert "DO-178C" in agent["markdown"]

    kit = bootstrap_persona_starter_kit(
        tmp_path,
        use_lore_names=False,
        organization_context={"org": "patchwork-labs"},
        custom_facets_by_slot={"dag-planner": {"max_wave_depth": 5}},
    )
    assert kit["persona_count"] == 15
    assert (tmp_path / ".agents" / "agents" / "dag-planner.md").is_file()
    assert (tmp_path / "config" / "runtime-hooks" / "seat-model-tier.json").is_file()


def test_generalized_deploy_cli_plan_and_lease_isolation(tmp_path: Path) -> None:
    import hashlib
    import json
    from patchwork_os.deploy_cli import (
        plan_inter_cli_dispatch,
        verify_inter_cli_completion_contract,
        verify_parent_child_lease_isolation,
    )

    iso_bad = verify_parent_child_lease_isolation(
        owner_session="sess-01",
        parent_claimed_paths=["C:/repo/.scratch/session-state/sess-01/tasks"],
    )
    assert iso_bad["valid"] is False
    assert iso_bad["reason"].startswith("RESULT_LEASE_REFUSED")

    iso_ok = verify_parent_child_lease_isolation(
        owner_session="sess-01",
        parent_claimed_paths=["C:/repo/.scratch/deploy2/sess-01/runs"],
    )
    assert iso_ok["valid"] is True

    task_md = tmp_path / "task.md"
    task_md.write_text("# Task Prompt\n", encoding="utf-8")
    plan = plan_inter_cli_dispatch(
        owner_session="sess-01",
        run_id="run-001",
        target_runtime="cc",
        task_path=task_md,
        workspace_root=tmp_path,
        skill_name="pwos-wfc",
        cognitive_stage="planning",
        effort="xhigh",
        dry_run=True,
    )
    assert plan["kind"] == "deploy2-cli-plan"
    assert plan["model"] == "claude-fable-5-1"
    assert "SKILL_BY_POINTER:pwos-wfc" in plan["notes"]

    res_dir = Path(plan["result_dir"])
    res_dir.mkdir(parents=True, exist_ok=True)
    ans = res_dir / "task_result.md"
    ans_bytes = b"Verified distinct seat output\n"
    ans.write_bytes(ans_bytes)
    ans_sha = f"sha256:{hashlib.sha256(ans_bytes).hexdigest()}"
    (res_dir / "done.json").write_text(
        json.dumps({"status": "completed", "artifacts": [{"path": "task_result.md", "sha256": ans_sha}]}),
        encoding="utf-8",
    )
    ver = verify_inter_cli_completion_contract(result_dir=res_dir, preimage_sha256="sha256:0000")
    assert ver["valid"] is True


def test_resolve_orchestrator_session_routing_covers_hub_and_spoke_axes() -> None:
    from patchwork_os.hub_spoke_gate import resolve_orchestrator_session_routing

    hub_plan = resolve_orchestrator_session_routing(
        session_tier="main_hub",
        task_category="planning_architecture_synthesis",
        complexity="high",
        urgency="normal",
        importance="critical",
    )
    assert hub_plan["rank_1_primary"]["runtime"] == "cc"
    assert hub_plan["rank_1_primary"]["model"] == "claude-fable-5-1"
    assert hub_plan["rank_2_counterpart"]["runtime"] == "muse"

    hub_exec = resolve_orchestrator_session_routing(
        session_tier="main_hub",
        task_category="execution_governance_and_audit",
        complexity="high",
        urgency="normal",
        importance="critical",
    )
    assert hub_exec["rank_1_primary"]["runtime"] == "cc"
    assert hub_exec["rank_1_primary"]["model"] == "opus"
    assert hub_exec["rank_1_primary"]["effort"] == "max"
    assert hub_exec["rank_2_counterpart"]["runtime"] == "codex"

    spoke_code = resolve_orchestrator_session_routing(
        session_tier="main_spoke_sub_hub",
        task_category="agentic_coding_and_tdd",
        complexity="high",
        urgency="normal",
        importance="critical",
    )
    assert spoke_code["rank_1_primary"]["runtime"] == "cc"
    assert spoke_code["rank_1_primary"]["model"] == "opus"
    assert spoke_code["rank_2_counterpart"]["runtime"] == "codex"

    spoke_vla = resolve_orchestrator_session_routing(
        session_tier="main_spoke_sub_hub",
        task_category="browser_vla_and_automation",
        complexity="high",
        urgency="normal",
        importance="critical",
    )
    assert spoke_vla["rank_1_primary"]["runtime"] == "agy"
    assert spoke_vla["rank_2_counterpart"]["runtime"] == "muse"


def test_three_layer_cli_config_precedence_and_agnostic_setup_rebrand(tmp_path: Path) -> None:
    import json
    import shutil
    from patchwork_os.config_loader import load_layered_config
    from patchwork_os.setup_init import (
        apply_project_setup_and_rebrand,
        build_agnostic_setup_questionnaire,
    )

    cfg_path = tmp_path / "config.json"
    inp_path = tmp_path / "input.json"
    cfg_path.write_text(
        json.dumps(
            {
                "os_name": "Base-OS",
                "skill_prefix": "base",
                "compliance_regime": "commercial_cloud",
                "routing": {"urgency": "normal", "complexity": "medium"},
            }
        ),
        encoding="utf-8",
    )
    inp_path.write_text(
        json.dumps(
            {
                "os_name": "Input-OS",
                "compliance_regime": "github_enterprise",
                "routing": {"complexity": "high"},
            }
        ),
        encoding="utf-8",
    )

    layered = load_layered_config(
        defaults={"os_name": "Patchwork-OS", "skill_prefix": "pwos"},
        config_json=cfg_path,
        input_json=inp_path,
        manual_set_pairs=["routing.urgency=immediate", "skill_prefix=aegis"],
        manual_kwargs={"os_name": "Aegis-OS"},
    )
    assert layered["os_name"] == "Aegis-OS"
    assert layered["skill_prefix"] == "aegis"
    assert layered["compliance_regime"] == "github_enterprise"
    assert layered["routing"]["complexity"] == "high"
    assert layered["routing"]["urgency"] == "immediate"

    q = build_agnostic_setup_questionnaire()
    assert q["runtime_agnostic"] is True
    assert q["verification"] == "unverified_example"
    assert q["compliance_assessed"] is False
    assert len(q["questions"]) >= 4

    repo_root = Path(__file__).resolve().parents[1]
    shutil.copytree(repo_root / "skills", tmp_path / "skills", dirs_exist_ok=True)
    profile = apply_project_setup_and_rebrand(
        tmp_path,
        config_json=cfg_path,
        input_json=inp_path,
        manual_set_pairs=["skill_prefix=aegis", "compliance_regime=itar_ear_aws_govcloud"],
        manual_kwargs={"os_name": "Aegis-OS", "dispatcher_skill_name": "runtime-dispatch"},
        bootstrap_personas=True,
    )
    assert profile["os_name"] == "Aegis-OS"
    assert profile["skill_prefix"] == "aegis"
    assert profile["dispatcher_skill_name"] == "aegis-runtime-dispatch"
    assert profile["compliance_regime"] == "itar_ear_aws_govcloud"
    assert profile["verification"] == "unverified_example"
    assert profile["compliance_assessed"] is False
    assert (tmp_path / "skills" / "aegis-setup" / "SKILL.md").is_file()
    assert (tmp_path / "skills" / "aegis-runtime-dispatch" / "SKILL.md").is_file()
    assert (tmp_path / "config" / "workspace-profile.json").is_file()


def test_extensible_compliance_routing_and_inter_runtime_synthesis() -> None:
    from patchwork_os.runtime_dispatch import (
        plan_inter_runtime_synthesis,
        resolve_extensible_compliance_routing,
    )

    # Requested AWS-named example filter; no actual compliance or availability verdict.
    aws_itar = plan_inter_runtime_synthesis(
        task_id="ITAR-AWS-01",
        goal="Implement ITAR flight control law verification",
        parent_session_id="hub-01",
        manual_set_pairs=[
            "compliance_regime=itar_ear_aws_govcloud",
            "task_category=execution_governance_and_audit",
        ],
    )
    assert aws_itar["itar_ear_restricted"] is True
    assert aws_itar["verification"] == "unverified_example"
    assert aws_itar["compliance_assessed"] is False
    assert aws_itar["execution_supported"] is False
    assert all(leg["verification"] == "unverified_example" for leg in aws_itar["legs"])
    assert aws_itar["inter_runtime_synthesis"]["cross_runtime_diverse"] is True
    assert {leg["runtime_harness"] for leg in aws_itar["legs"]} == {"cc", "aws_kiro"}
    assert all(leg["cloud_backend"] == "aws_bedrock_govcloud_itar" for leg in aws_itar["legs"])

    # Requested GCP-named example filter; the pair is configuration data only.
    gcp_itar = resolve_extensible_compliance_routing(
        manual_set_pairs=[
            "compliance_regime=itar_ear_gcp_vertex",
            "task_category=browser_vla_and_automation",
        ]
    )
    assert gcp_itar["rank_1_primary"]["runtime"] == "agy"
    assert gcp_itar["rank_1_primary"]["backend"] == "gcp_vertex_assured_itar"
    assert gcp_itar["rank_2_counterpart"]["runtime"] == "cc"
    assert gcp_itar["inter_runtime_synthesis"]["cross_runtime_diverse"] is True

    # 3. GitHub Enterprise: pairs github_copilot + codex
    gh_ent = resolve_extensible_compliance_routing(
        manual_set_pairs=[
            "compliance_regime=github_enterprise",
            "task_category=agentic_coding_and_tdd",
        ]
    )
    assert gh_ent["rank_1_primary"]["runtime"] == "github_copilot"
    assert gh_ent["rank_2_counterpart"]["runtime"] == "codex"
    assert gh_ent["inter_runtime_synthesis"]["cross_runtime_diverse"] is True

    # Local example selector; it does not measure or enforce an air gap.
    airgap = resolve_extensible_compliance_routing(
        manual_set_pairs=[
            "compliance_regime=airgapped_local",
            "task_category=planning_architecture_synthesis",
        ]
    )
    assert airgap["rank_1_primary"]["backend"] == "local_airgap_vllm"
    assert airgap["inter_runtime_synthesis"]["cross_runtime_diverse"] is True


def test_rea_twelve_pillars_and_generalized_subsystems() -> None:
    from patchwork_os.browser_vla import (
        validate_mermaid_visual_width,
        verify_vla_capture_receipt,
    )
    from patchwork_os.harness_audit import (
        audit_hop0_instruction_budget,
        compile_adversarial_harness_contract,
        should_deduplicate_hook_event,
    )
    from patchwork_os.mcp_printing_press import (
        describe_mcp_tool_tier1,
        gate_mcp_tool_call_tier2,
        project_mcp_tools_tier0,
    )
    from patchwork_os.rea_gap_analyzer import audit_upstream_to_patchwork_parity
    from patchwork_os.session_lifecycle import (
        build_session_checkpoint_and_handover,
        create_session_messenger_envelope,
        register_backlog_obligation,
        verify_session_messenger_ack,
    )

    repo_root = Path(__file__).resolve().parents[1]
    parity = audit_upstream_to_patchwork_parity(repo_root)
    assert parity["complete_parity"] is True
    assert parity["pillar_count"] == 12
    assert parity["missing_items"] == []

    # Session lifecycle & messenger
    ckpt = build_session_checkpoint_and_handover(
        session_id="sess-01",
        task_id="TASK-01",
        completed_items=["Done A"],
        open_frontier=["Next B"],
        manual_set_pairs=["task_id=TASK-01-OVERRIDE"],
    )
    assert ckpt["task_id"] == "TASK-01-OVERRIDE"
    assert ckpt["checkpoint_sha256"].startswith("sha256:")

    env = create_session_messenger_envelope(
        sender_session="sess-01",
        recipient_session="sess-02",
        message_body="Verify leg 1",
        correlation_id="corr-1",
    )
    assert env["state"] == "queued"
    ack = verify_session_messenger_ack(
        env,
        observed_ack_sha256=env["message_sha256"],
        observed_recipient="sess-02",
    )
    assert ack["valid"] is True
    assert ack["state"] == "acked"

    ob = register_backlog_obligation(
        obligation_id="BL-01",
        summary="Run secondary-host live matrix",
        deferred_reason="Host scoped to primary-host first",
        target_scope="scripts/deploy2",
    )
    assert ob["status"] == "deferred"

    # MCP Printing-Press
    tools = [
        {"name": "query_docs", "description": "Read docs", "annotations": {"readOnlyHint": True}},
        {"name": "mutate_prod", "description": "Mutate state", "annotations": {"readOnlyHint": False}},
    ]
    t0 = project_mcp_tools_tier0(tools)
    assert len(t0) == 2
    t1 = describe_mcp_tool_tier1(tools, "query_docs")
    assert t1["read_only"] is True
    blocked = gate_mcp_tool_call_tier2(tools[1], {"x": 1}, allow_mutation=False)
    assert blocked["allowed"] is False
    allowed = gate_mcp_tool_call_tier2(tools[1], {"x": 1}, allow_mutation=True)
    assert allowed["allowed"] is True

    # Browser VLA & Mermaid gate
    vla_ok = verify_vla_capture_receipt(
        {
            "vision_before_digest": "sha256:1111",
            "vision_after_digest": "sha256:2222",
            "dom_after_digest": "sha256:3333",
        }
    )
    assert vla_ok["valid"] is True
    mm_ok = validate_mermaid_visual_width("```mermaid\nflowchart TD\n  A[\"Start\"] --> B[\"End\"]\n```\n")
    assert mm_ok["valid"] is True

    # Harness audit
    budget = audit_hop0_instruction_budget({"CLAUDE.md": 40000, "AGENTS.md": 35000}, budget_chars=150000)
    assert budget["within_budget"] is True
    assert should_deduplicate_hook_event("PreToolUse:Read", 100.5, {"PreToolUse:Read": 100.0}) is True
    harness = compile_adversarial_harness_contract({"rule": "anti-choke"}, [{"case": "c1"}])
    assert harness["target_id"].startswith("sha256:")




