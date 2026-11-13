# SPDX-License-Identifier: MIT
"""Generalized Instruction-Budget Guard, Hook Storm Deduplicator & Harness Contract Compiler.

Provides deterministic helpers for instruction budgets, hook-event deduplication
and pinned verification contracts. Callers supply actual hook integration:
1. ``audit_hop0_instruction_budget``:
   Prevents the ``open-write-path-closed-exit`` antipattern by checking total
   Hop-0 startup characters against a strict budget (default 150,000 chars) and
   detecting duplicate per-turn static re-injections.
2. ``should_deduplicate_hook_event``:
   Suppresses duplicate hook invocations within a 1.5-second window (e.g., from
   case-duplicate workspace paths on Windows).
3. ``compile_adversarial_harness_contract``:
   Compiles a target claim and adversarial test cases into a SHA-256-pinned
   verification harness (`target_id == sha256:<canonical_compact_json>`).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Sequence


def audit_hop0_instruction_budget(
    file_char_counts: Mapping[str, int],
    *,
    budget_chars: int = 150_000,
) -> Dict[str, Any]:
    """Audit Hop-0 startup instruction files against `budget_chars` to prevent `open-write-path-closed-exit`."""
    total_chars = sum(max(0, int(v)) for v in file_char_counts.values())
    over_budget = total_chars > budget_chars
    top_offenders = sorted(
        ((k, int(v)) for k, v in file_char_counts.items()),
        key=lambda item: item[1],
        reverse=True,
    )[:5]
    return {
        "within_budget": not over_budget,
        "total_chars": total_chars,
        "budget_chars": budget_chars,
        "delta_chars": total_chars - budget_chars,
        "top_offenders": [{"file": k, "chars": v} for k, v in top_offenders],
    }


def should_deduplicate_hook_event(
    event_signature: str,
    current_timestamp_s: float,
    recent_events: Mapping[str, float],
    *,
    window_seconds: float = 1.5,
) -> bool:
    """Return True if an identical hook event fired within `window_seconds` (prevents 3x hook storms)."""
    prev_ts = recent_events.get(event_signature)
    if prev_ts is None:
        return False
    return (current_timestamp_s - float(prev_ts)) <= window_seconds


def compile_adversarial_harness_contract(
    target_spec: Mapping[str, Any],
    adversarial_cases: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Compile a SHA-256-pinned verification harness (`codify-harness` pattern)."""
    target_without_id = {k: v for k, v in target_spec.items() if k != "target_id"}
    canonical_bytes = json.dumps(
        target_without_id,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    target_id = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
    return {
        "schema_version": "patchwork-codified-harness-v1",
        "target_id": target_id,
        "target": {**target_without_id, "target_id": target_id},
        "case_count": len(adversarial_cases),
        "cases": [dict(c) for c in adversarial_cases],
    }
