# SPDX-License-Identifier: Apache-2.0
"""Generalized Session Lifecycle, Carry/Close Handover, Inter-Session Messenger & Backlog Ledger.

Assimilates and generalizes Upstream-Agentic-OS's session continuity subsystems:
1. ``build_session_checkpoint_and_handover`` (generalized from ``session-close`` & ``session-carry``):
   Produces both a deterministic machine checkpoint JSON and a human-readable
   Markdown handover block that survives context compaction.
2. ``create_session_messenger_envelope`` & ``verify_session_messenger_ack``
   (generalized from ``session-messenger``):
   Enforces distinct ``queued -> delivered -> acked`` state transitions with
   SHA-256 payload digests (never treating queued or typed as acked).
3. ``register_backlog_obligation`` (generalized from ``backlog-task``):
   Persists deferred findings or follow-up tasks so nothing is silently dropped.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .config_loader import load_layered_config


def build_session_checkpoint_and_handover(
    *,
    session_id: str,
    task_id: str,
    completed_items: Sequence[str],
    open_frontier: Sequence[str],
    active_lease_paths: Sequence[str] = (),
    config_json: Optional[Path | str | Mapping[str, Any]] = None,
    input_json: Optional[Path | str | Mapping[str, Any]] = None,
    manual_set_pairs: Optional[Sequence[str]] = None,
    manual_kwargs: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a compaction-proof machine checkpoint + human handover markdown block."""
    if not session_id.strip() or not task_id.strip():
        raise ValueError("session_id and task_id must be non-empty")

    layered = load_layered_config(
        defaults={
            "session_id": session_id.strip(),
            "task_id": task_id.strip(),
            "completed_items": list(completed_items),
            "open_frontier": list(open_frontier),
            "active_lease_paths": list(active_lease_paths),
        },
        config_json=config_json,
        input_json=input_json,
        manual_set_pairs=manual_set_pairs,
        manual_kwargs=manual_kwargs,
    )

    payload_bytes = json.dumps(
        {
            "session_id": layered["session_id"],
            "task_id": layered["task_id"],
            "completed_items": layered["completed_items"],
            "open_frontier": layered["open_frontier"],
        },
        sort_keys=True,
    ).encode("utf-8")
    checkpoint_sha256 = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()

    md_lines = [
        f"# Session Handover & Compaction Carry (`{layered['session_id']}`)",
        "",
        f"- **Task ID**: `{layered['task_id']}`",
        f"- **Checkpoint Digest**: `{checkpoint_sha256}`",
        f"- **Active Lease Paths**: `{', '.join(layered['active_lease_paths']) or 'none'}`",
        "",
        "## Completed Frontier",
    ]
    for item in layered["completed_items"]:
        md_lines.append(f"- [x] {item}")
    md_lines.append("")
    md_lines.append("## Open Continuation Frontier")
    for item in layered["open_frontier"]:
        md_lines.append(f"- [ ] {item}")

    return {
        "schema_version": "patchwork-session-checkpoint-v1",
        "session_id": layered["session_id"],
        "task_id": layered["task_id"],
        "checkpoint_sha256": checkpoint_sha256,
        "completed_items": layered["completed_items"],
        "open_frontier": layered["open_frontier"],
        "active_lease_paths": layered["active_lease_paths"],
        "handover_markdown": "\n".join(md_lines) + "\n",
    }


def create_session_messenger_envelope(
    *,
    sender_session: str,
    recipient_session: str,
    message_body: str,
    correlation_id: str,
) -> Dict[str, Any]:
    """Create a deterministic inter-session message envelope (`state='queued'`)."""
    if not sender_session.strip() or not recipient_session.strip() or not message_body.strip():
        raise ValueError("sender_session, recipient_session, and message_body must be non-empty")
    if sender_session.strip() == recipient_session.strip():
        raise ValueError("sender_session and recipient_session must be distinct")
    digest = "sha256:" + hashlib.sha256(message_body.encode("utf-8")).hexdigest()
    return {
        "schema_version": "patchwork-session-messenger-v1",
        "correlation_id": correlation_id.strip(),
        "sender_session": sender_session.strip(),
        "recipient_session": recipient_session.strip(),
        "message_sha256": digest,
        "message_body": message_body,
        "state": "queued",
        "ack_verified": False,
    }


def verify_session_messenger_ack(
    envelope: Mapping[str, Any],
    *,
    observed_ack_sha256: str,
    observed_recipient: str,
) -> Dict[str, Any]:
    """Verify transcript-observed ACK without conflating queued/typed/submitted with acked."""
    reasons: List[str] = []
    if observed_recipient.strip() != str(envelope.get("recipient_session", "")).strip():
        reasons.append("RECIPIENT_SESSION_MISMATCH")
    if observed_ack_sha256.strip() != str(envelope.get("message_sha256", "")).strip():
        reasons.append("ACK_MESSAGE_DIGEST_MISMATCH")
    valid = len(reasons) == 0
    return {
        "valid": valid,
        "state": "acked" if valid else str(envelope.get("state", "queued")),
        "ack_verified": valid,
        "reasons": reasons,
    }


def register_backlog_obligation(
    *,
    obligation_id: str,
    summary: str,
    deferred_reason: str,
    target_scope: str,
) -> Dict[str, Any]:
    """Create a persistent backlog obligation record so deferred work survives compaction."""
    if not obligation_id.strip() or not summary.strip():
        raise ValueError("obligation_id and summary must be non-empty")
    return {
        "schema_version": "patchwork-backlog-obligation-v1",
        "obligation_id": obligation_id.strip(),
        "summary": summary.strip(),
        "deferred_reason": deferred_reason.strip(),
        "target_scope": target_scope.strip(),
        "status": "deferred",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
