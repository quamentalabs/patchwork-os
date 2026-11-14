from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from patchwork_os.runtime_hook_adapter import (
    CANONICAL_AI_FAMILIES,
    CANONICAL_DEV_ENV_SURFACES,
    CANONICAL_RUNTIMES,
    EIGHT_CORE_HOOK_CONTRACTS,
    GENERALIZED_REIMPLEMENTATION_BLUEPRINTS,
    RUNTIME_HOOK_ADAPTER_MATRIX,
    SKILL_BRIEF_CONFIG_DEFAULT,
    VOYAGE_MAPS_CONFIG_DEFAULT,
    evaluate_core_hook_gate,
    format_hook_verdict,
    normalize_runtime_id,
    normalize_tool_category,
    render_kiro_hook_files,
)


def test_five_runtimes_and_surfaces_present_in_adapter_matrix() -> None:
    assert set(CANONICAL_RUNTIMES) == {"cc", "codex", "agy", "muse", "kiro"}
    assert "crew" in CANONICAL_DEV_ENV_SURFACES
    assert "ide_extension" in CANONICAL_DEV_ENV_SURFACES
    assert set(CANONICAL_AI_FAMILIES) == {"claude", "gpt", "gemini", "muse"}
    for rt in CANONICAL_RUNTIMES:
        assert rt in RUNTIME_HOOK_ADAPTER_MATRIX
        assert RUNTIME_HOOK_ADAPTER_MATRIX[rt]["verification"] == "unverified_example"
    assert normalize_runtime_id("aws_kiro") == "kiro"
    assert normalize_runtime_id("kiro-cli") == "kiro"
    assert normalize_runtime_id("claude") == "cc"


def test_kiro_tool_vocabulary_normalization_and_exit2_blocking() -> None:
    assert normalize_tool_category("execute_bash") == "shell"
    assert normalize_tool_category("fs_read") == "read"
    assert normalize_tool_category("fs_write") == "write"
    assert normalize_tool_category("str_replace") == "edit"
    assert normalize_tool_category("list_directory") == "search"
    assert normalize_tool_category("invoke_subagent") == "subagent"

    verdict = format_hook_verdict(
        "kiro",
        "tool.pre",
        "deny",
        reason="BLOCKED_IN_KIRO",
    )
    assert verdict["exit_code"] == 2
    assert verdict["stderr"] == "BLOCKED_IN_KIRO"
    assert verdict["stdout"] == ""
    assert verdict["status"] == "blocked"


def test_eight_core_hooks_and_configs_evaluate_across_runtimes() -> None:
    assert len(EIGHT_CORE_HOOK_CONTRACTS) == 8
    assert ".kiro/skills" in SKILL_BRIEF_CONFIG_DEFAULT["skill_roots"]
    assert "str_replace" in VOYAGE_MAPS_CONFIG_DEFAULT["edit_tools"]
    assert "fs_write" in VOYAGE_MAPS_CONFIG_DEFAULT["write_tools"]

    # 1. Conhost prevention blocks unwrapped powershell in kiro with exit 2
    conhost_res = evaluate_core_hook_gate(
        "windowless-conhost-prevention-gate",
        "kiro",
        "execute_bash",
        {"command": "powershell.exe -Command Get-Date"},
    )
    assert conhost_res["exit_code"] == 2
    assert "COMMAND_ROUTE_UNWRAPPED_CONSOLE_REFUSED" in conhost_res["stderr"]

    # Direct windowless python.exe -X utf8 -B is allowed
    clean_res = evaluate_core_hook_gate(
        "windowless-conhost-prevention-gate",
        "kiro",
        "execute_bash",
        {"command": "python.exe -X utf8 -B -m pytest -q"},
    )
    assert clean_res["exit_code"] == 0
    assert clean_res["status"] == "allowed"

    # 2. Skill auto-context injects [SKILL_BRIEF] on .kiro/skills/*/SKILL.md
    skill_res = evaluate_core_hook_gate(
        "skill-auto-context-gate",
        "kiro",
        "fs_read",
        {"path": ".kiro/skills/pwos-rea/SKILL.md"},
    )
    assert skill_res["exit_code"] == 0
    assert "[SKILL_BRIEF skill=pwos-rea" in skill_res["stdout"]

    # 3. Render Kiro v1 hook files
    rendered = render_kiro_hook_files()
    assert len(rendered) == 8
    assert rendered["windowless-conhost-prevention-gate.json"]["version"] == "v1"
    hook_obj = rendered["windowless-conhost-prevention-gate.json"]["hooks"][0]
    assert hook_obj["trigger"] == "PreToolUse"
    assert "execute_bash" in hook_obj["matcher"]


def test_generalized_reimplementation_blueprints_complete() -> None:
    expected_keys = {
        "knowledge_vault",
        "converging_voyage",
        "rea_reverse_engineering",
        "software_factory",
    }
    assert set(GENERALIZED_REIMPLEMENTATION_BLUEPRINTS) == expected_keys
    for key, spec in GENERALIZED_REIMPLEMENTATION_BLUEPRINTS.items():
        assert len(spec["invariants"]) >= 3, key
        assert len(spec["procedure_stages"]) >= 4, key
        assert len(spec["adr_decisions"]) >= 2, key
