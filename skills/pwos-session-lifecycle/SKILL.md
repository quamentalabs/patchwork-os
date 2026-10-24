---
name: pwos-session-lifecycle
alias: session-lifecycle
description: "Use when checkpointing a session before compaction or close (session-close / session-carry), exchanging verified cross-session messages with ACK digests (session-messenger), or recording deferred obligations in the backlog ledger (backlog-task)."
category: session-continuity-and-messaging
tier: tier-1-lifecycle-gate
paradigms:
  - workflow
  - prompt-flow
  - graph-prompting
  - meta-prompting
license: MIT
---

# Session Lifecycle, Carry/Close, Messenger and Backlog Skeleton Procedure

## Overview

Generalizes Upstream-Agentic-OS's session continuity quartet (`session-close`, `session-carry`, `session-messenger`, and `backlog-task`) into `session_lifecycle.py`. Ensures that active plans, lease boundaries, cross-session messages, and deferred obligations survive context compaction and multi-session handoffs without silent drops.

## Invariants

1. Compaction-Proof Dual Checkpoint: Every session close or compaction event emits both a machine-verifiable JSON checkpoint (`checkpoint_sha256`) and a human-readable Markdown handover block.
2. Strict Messenger State Separation: Never treat `queued`, `typed`, or `submitted` as `acked`; a cross-session message transitions to `acked` only when `verify_session_messenger_ack` confirms matching `recipient_session` and `message_sha256`.
3. Persistent Deferred Backlog: Any finding or task deferred to a future turn or session must be registered via `register_backlog_obligation` before claiming completion.
4. Three-Layer Config Support: Accepts `config.json`, `input.json`, and `--set key=value` overrides.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Session Lease Binding and Frontier Inventory

Inventory completed items, open continuation items, and active leased paths for the current `session_id`.

### Stage 2: Cross-Session Messenger Envelope Creation

When coordinating with a peer or child session, build a signed envelope via `create_session_messenger_envelope` (`sender_session != recipient_session`).

### Stage 3: Transcript-Observed ACK Verification

Verify peer receipt through `verify_session_messenger_ack` against the peer's observed digest before advancing dependent workflow waves.

### Stage 4: Backlog Obligation Registration

Record any parked or deferred non-critical items via `register_backlog_obligation` so they remain visible across compactions.

### Stage 5: Checkpoint and Handover Emission

Generate the combined checkpoint and Markdown handover block via `build_session_checkpoint_and_handover`.

## Artifacts and Verification Gates

- `session-checkpoint.json` and `session-handover.md` pinned by `checkpoint_sha256`.
- Messenger ACK receipts and `backlog-obligations.json` entries.

## Hard Boundaries

- Never claim a peer session acknowledged a message based solely on pane typing or queue insertion.
- Never silently drop deferred obligations across session boundaries.
