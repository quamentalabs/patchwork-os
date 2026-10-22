# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from patchwork_os.skills_registry import (
    REQUIRED_CORE_SKILLS,
    parse_skill_skeleton,
    validate_skills_directory,
)


def test_all_ten_generalized_skill_skeletons_present_and_valid() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skills_root = repo_root / "skills"
    report = validate_skills_directory(skills_root)

    assert report["valid"] is True
    assert report["index_present"] is True
    assert report["missing_core_skills"] == []
    assert report["invalid_skills"] == []
    assert report["skill_count"] == len(REQUIRED_CORE_SKILLS) == 10

    for skill_name in REQUIRED_CORE_SKILLS:
        info = report["skills"][skill_name]
        assert info["valid"] is True
        assert info["stage_count"] >= 4
        assert info["proprietary_hits"] == []
        assert info["has_em_dash"] is False
        assert info["has_dollar"] is False
        assert info["has_crlf"] is False


def test_parse_skill_skeleton_rejects_proprietary_leak_or_em_dash(tmp_path: Path) -> None:
    bad_dir = tmp_path / "skills" / "grilling"
    bad_dir.mkdir(parents=True)
    bad_md = bad_dir / "SKILL.md"
    bad_md.write_text(
        "---\nname: grilling\ndescription: \"test\"\n---\n"
        "## Overview\nLeaked proprietary-internal token and em-dash \u2014 plus $var.\n",
        encoding="utf-8",
        newline="\n",
    )
    res = parse_skill_skeleton(bad_md)
    assert res["valid"] is False
    assert "proprietary-internal" in res["proprietary_hits"]
    assert res["has_em_dash"] is True
    assert res["has_dollar"] is True
