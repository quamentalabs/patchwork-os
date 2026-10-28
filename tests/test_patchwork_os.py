# SPDX-License-Identifier: MIT
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patchwork_os.binder import evaluate_repository, validate_patchwork_satellite
from patchwork_os.ladder import EscalationTier, EvaluationVerdict


def test_patchwork_satellite_passes_tier0() -> None:
    report = validate_patchwork_satellite(ROOT)
    assert report["valid"] is True, report["reasons"]
    result = evaluate_repository(ROOT)
    assert result.verdict == EvaluationVerdict.PASS
    assert result.tier_reached == EscalationTier.TIER_0_DETERMINISTIC
    assert result.escalated_to_main_llm is False


def test_claude_code_custom_statusline_hybrid_renders_two_rows() -> None:
    import json
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    settings_path = repo_root / ".claude" / "settings.json"
    example_path = repo_root / ".claude" / "settings.example.json"
    hybrid_script = repo_root / ".claude" / "helpers" / "patchwork-statusline-hybrid.cjs"
    primary_script = repo_root / ".claude" / "helpers" / "statusline.js"
    graft_script = repo_root / ".claude" / "helpers" / "graft-statusline.cjs"

    assert settings_path.is_file()
    assert hybrid_script.is_file()
    assert primary_script.is_file()
    assert graft_script.is_file()

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings == {}
    settings = json.loads(example_path.read_text(encoding="utf-8"))
    assert "patchwork-statusline-hybrid.cjs" in settings["statusLine"]["command"]
    assert "graft-statusline.cjs" in settings["subagentStatusLine"]["command"]

    sample_payload = {
        "model": {"display_name": "Opus 5 (1M context)", "id": "claude-opus-5"},
        "fast_mode": True,
        "workspace": {"project_dir": "/workspace/patchwork-os"},
        "cost": {"total_cost_usd": 1.25},
        "context_window": {
            "total_input_tokens": 880000,
            "context_window_size": 1000000,
            "used_percentage": 88.0,
            "total_output_tokens": 14200,
            "current_usage": {"input_tokens": 3200, "cache_creation_input_tokens": 800},
        },
        "rate_limits": {
            "five_hour": {"used_percentage": 42.0},
            "seven_day": {"used_percentage": 19.0},
        },
    }
    proc = subprocess.run(
        ["node", str(hybrid_script)],
        input=json.dumps(sample_payload),
        text=True,
         encoding="utf-8",
        capture_output=True,
        cwd=str(repo_root),
        check=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert "Opus 5 (1M)" in lines[0]
    assert "patchwork-os" in lines[0]
    assert "$1.25" in lines[0]
    assert "88%" in lines[1]
    assert "120k left" in lines[1]


def test_obsidian_free_llm_wiki_hygiene_and_graph() -> None:
    from pathlib import Path
    from patchwork_os.llm_wiki import (
        audit_itar_and_obsidian_hygiene,
        build_llm_wiki_graph,
        normalize_wikilinks_to_markdown,
        query_llm_wiki,
    )

    repo_root = Path(__file__).resolve().parents[1]
    hygiene = audit_itar_and_obsidian_hygiene(repo_root)
    assert hygiene["zero_obsidian_dependency"] is True
    assert hygiene["itar_airgap_plain_markdown_ready"] is True

    graph = build_llm_wiki_graph(repo_root / "knowledge")
    assert graph["valid"] is True
    assert graph["node_count"] == 4
    assert graph["orphan_nodes"] == []

    converted = normalize_wikilinks_to_markdown("See [[Patchwork Blueprint|Blueprint]].")
    assert converted == "See [Blueprint](patchwork-blueprint.md)."
    hits = query_llm_wiki(repo_root / "knowledge", "Patchwork")
    assert len(hits) >= 1
