---
name: pwos-deploy-cli
alias: deploy-cli
description: "Use for dispatch-plan and hash-consistency procedures across runtime labels (cc, codex, agy, muse). Live launch, supervision, lease acquisition and locking require a separate implementation."
category: cross-runtime-dispatch
tier: tier-3-high-order-lifecycle
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Deploy-Cli Generalized Inter-CLI Dispatcher Skeleton Procedure

## Overview

Patchwork-OS provides a plan-only `plan_inter_cli_dispatch` API and hash-consistency/path-contract checks. Runtime labels (`cc`, `codex`, `agy`, `muse`), argv and child result paths are descriptors. `dry_run=False` is unsupported. This module does not launch seats, acquire leases or locks, authenticate results, supervise processes or provide a runnable dispatcher CLI. The live stages below are design requirements for a separate integration.

## Invariants

1. Plan Only: Inspect target/model/effort/task and prompt SHA-256 descriptors with `dry_run=True`; a plan is not a live invocation.
2. Intended Lease Isolation: Result paths and `child_session` describe intended ownership only. A separate integration must acquire and enforce leases.
3. Intended Dispatch Lock: Sequential lock acquisition, pane creation and parallel monitoring are not implemented by this package's planner.
4. Answer Hash Consistency: Compare `done.json` and answer bytes and optional preimage changes. Matching hashes, exit zero and completed metadata do not establish native execution, signatures or acceptance.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Target, Model Tier, and Effort Resolution

Resolve the target runtime (`cc`, `codex`, `agy`, `muse`), canonical 3-tier model (`resolve_canonical_three_tier_models`), and session/cognitive effort level (`max`, `xhigh`, `high`, `medium`) from `models.json` and `resolve_orchestrator_session_routing`.

### Stage 2: Preflight Plan and Lease Boundary Verification

Build the deterministic `--inter-cli` launch plan (`plan_inter_cli_dispatch`), verify parent lease non-contention, and compute `task_sha256` and `first_prompt_sha256`.

### Stage 3: Sequential Lock Acquisition and Seat Launch

Not implemented in this package: a separate authorized integration would acquire a dispatch lock, launch a seat, deliver its prompt and record native observations. Do not execute `launch_argv` as a supported package CLI.

### Stage 4: Readiness Sensing and Non-Invasive Supervision

Not implemented in this package: a separate integration would observe child progress and dialogs through its native transcript/pane surfaces.

### Stage 5: Artifact Collection, Hash Verification, and Clean Reap

Use `verify_inter_cli_completion_contract` for its bounded hash/status/preimage checks. Distinct-delta review, pane closure and lease release require separate observation and implementation; a valid return is not an authenticity or approval verdict.

## Artifacts and Verification Gates

The following are intended integration artifacts, not files emitted by the plan-only API:

- `run.json`, `deliver.jsonl`, `pane-after-deliver.txt`, and `native-result-lease-handoff.json`.
- `done.json`, `task_result.md`, and `mpt-deploy-cli-dispatch-receipt.json`.

## Hard Boundaries

- Never treat a dry-run or preflight receipt as submitted or verified runtime acceptance.
- Never hardcode deprecated model strings in command lines or source code; always resolve from the centralized model registry.
