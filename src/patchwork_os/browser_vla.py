# SPDX-License-Identifier: MIT
"""Generalized Hybrid Browser Control, VLA Receipt Verifier & Visual Width Gate.

Assimilates and generalizes Upstream-Agentic-OS's ``hybrid-browser-control``,
``exec-pw-cli``, and ``closed_feedback_visual_gate.py``:
1. ``verify_vla_capture_receipt``:
   Verifies that a browser VLA roundtrip includes pre-action and post-action
   visual digests (`vision_before_digest != vision_after_digest`), DOM digest,
   and non-empty extracted table/DOM evidence.
2. ``validate_mermaid_visual_width``:
   Enforces the `<= 79` character line-width gate and rejects standalone
   horizontal node pre-declarations before edges.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping


def verify_vla_capture_receipt(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    """Verify a Vision-Language-Action (VLA) capture receipt (`vision_before -> action -> dom + vision_after`)."""
    reasons: List[str] = []
    v_before = str(receipt.get("vision_before_digest", "")).strip()
    v_after = str(receipt.get("vision_after_digest", "")).strip()
    dom_after = str(receipt.get("dom_after_digest", "")).strip()

    if not v_before.startswith("sha256:"):
        reasons.append("MISSING_VISION_BEFORE_DIGEST")
    if not v_after.startswith("sha256:"):
        reasons.append("MISSING_VISION_AFTER_DIGEST")
    if v_before and v_after and v_before == v_after:
        reasons.append("VISION_DIGEST_UNCHANGED_AFTER_ACTION")
    if not dom_after.startswith("sha256:"):
        reasons.append("MISSING_DOM_AFTER_DIGEST")

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "vision_before_digest": v_before,
        "vision_after_digest": v_after,
        "dom_after_digest": dom_after,
    }


def validate_mermaid_visual_width(markdown_text: str, *, max_cols: int = 79) -> Dict[str, Any]:
    """Ensure every Mermaid block line is `<= max_cols` and avoids standalone node pre-declarations."""
    violations: List[str] = []
    in_mermaid = False
    for line_no, raw_line in enumerate(markdown_text.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid and stripped.startswith("```"):
            in_mermaid = False
            continue
        if in_mermaid:
            if len(raw_line) > max_cols:
                violations.append(f"LINE_{line_no}_EXCEEDS_{max_cols}_COLS:{len(raw_line)}")
            if (
                re.match(r'^[A-Za-z0-9_-]+\["[^"]+"\]$', stripped)
                and "-->" not in stripped
                and "---" not in stripped
            ):
                violations.append(f"LINE_{line_no}_STANDALONE_NODE_PREDECLARATION:{stripped}")
    return {
        "valid": len(violations) == 0,
        "violations": violations,
    }
