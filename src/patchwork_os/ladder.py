"""Near-deterministic 3-tier evaluation ladder for Patchwork-OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EvaluationVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    AMBIGUOUS_ESCALATE = "ambiguous_escalate"


class EscalationTier(str, Enum):
    TIER_0_DETERMINISTIC = "tier_0_deterministic"
    TIER_1_LOCAL_LLM_NO_THINKING = "tier_1_local_llm_no_thinking"
    TIER_2_MAIN_LLM = "tier_2_main_llm"


@dataclass(frozen=True)
class LadderEvaluationResult:
    verdict: EvaluationVerdict
    tier_reached: EscalationTier
    reasons: List[str] = field(default_factory=list)
    processed_summary: Dict[str, Any] = field(default_factory=dict)
    escalated_to_main_llm: bool = False
    local_llm_thinking_enabled: bool = False


class NearDeterministicLadder:
    """Executes Tier-0 deterministic rules -> Tier-1 local no-thinking LLM -> Tier-2 escalation."""

    def evaluate(
        self,
        raw_data: Dict[str, Any],
        tier0_fn: Callable[[Dict[str, Any]], tuple[Optional[EvaluationVerdict], List[str], Dict[str, Any]]],
        tier1_local_llm_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], tuple[EvaluationVerdict, str]]] = None,
    ) -> LadderEvaluationResult:
        verdict, reasons, processed = tier0_fn(raw_data)
        if verdict in (EvaluationVerdict.PASS, EvaluationVerdict.FAIL):
            return LadderEvaluationResult(
                verdict=verdict,
                tier_reached=EscalationTier.TIER_0_DETERMINISTIC,
                reasons=reasons,
                processed_summary=processed,
                escalated_to_main_llm=False,
                local_llm_thinking_enabled=False,
            )
        if tier1_local_llm_fn is None:
            return LadderEvaluationResult(
                verdict=EvaluationVerdict.AMBIGUOUS_ESCALATE,
                tier_reached=EscalationTier.TIER_2_MAIN_LLM,
                reasons=reasons + ["TIER1_UNAVAILABLE_ESCALATED"],
                processed_summary=processed,
                escalated_to_main_llm=True,
                local_llm_thinking_enabled=False,
            )
        t1_verdict, t1_reason = tier1_local_llm_fn(processed, raw_data)
        if t1_verdict == EvaluationVerdict.AMBIGUOUS_ESCALATE:
            return LadderEvaluationResult(
                verdict=EvaluationVerdict.AMBIGUOUS_ESCALATE,
                tier_reached=EscalationTier.TIER_2_MAIN_LLM,
                reasons=reasons + [t1_reason],
                processed_summary=processed,
                escalated_to_main_llm=True,
                local_llm_thinking_enabled=False,
            )
        return LadderEvaluationResult(
            verdict=t1_verdict,
            tier_reached=EscalationTier.TIER_1_LOCAL_LLM_NO_THINKING,
            reasons=reasons + [t1_reason],
            processed_summary=processed,
            escalated_to_main_llm=False,
            local_llm_thinking_enabled=False,
        )
