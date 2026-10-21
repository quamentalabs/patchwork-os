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
