---
name: pwos-deploy-cli
alias: deploy-cli
description: "Use when dispatching, supervising, or collecting external CLI, IDE, or Desktop-App agent seats across runtime families (cc, codex, agy, muse) with isolated result leases, sequential dispatch locks, and cryptographic task/prompt/answer verification."
category: cross-runtime-dispatch
tier: tier-3-high-order-lifecycle
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: MIT
---

# Deploy-Cli Generalized Inter-CLI Dispatcher Skeleton Procedure

## Overview

Generalized cross-runtime `--inter-cli` seat launcher, supervisor, and collector for Patchwork-OS. Dispatches isolated worker seats across heterogeneous CLI/IDE/Desktop-App runtimes (`cc`, `codex`, `agy`, `muse`) using canonical 3-tier deduplicated model vectors, dual-axis cognitive stage routing, contention-free child result leases, and cryptographic receipt verification.

## Invariants

1. Dry-Run Preflight Before Live Launch: Always verify target runtime, model tier, effort level, task SHA-256, first-prompt SHA-256, persona path, and governing skill pointer in `--dry-run` or `--preflight` before live pane creation.
2. Parent-Child Result Lease Non-Contention: The parent `owner_session` claims only `.scratch/deploy2/<owner_session>/runs` and task scratch paths; each child seat claims its own `.scratch/session-state/<owner_session>/tasks/<run_id>/task_result.md` and `done.json` under a distinct `child_session` UUID.
3. Sequential Dispatch Lock with Parallel Wave Execution: Acquire `mpt-dispatch.lock` sequentially during pane creation and prompt delivery, then monitor parallel seat execution within each WFC/MPT wave before unlocking dependent waves.
4. Cryptographic Answer Contract Verification: Never equate process exit 0 or dry-run plans with runtime acceptance; verify `done.json`, `answer_sha256`, and `postimage != preimage` before marking a seat complete.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Target, Model Tier, and Effort Resolution

Resolve the target runtime (`cc`, `codex`, `agy`, `muse`), canonical 3-tier model (`resolve_canonical_three_tier_models`), and session/cognitive effort level (`max`, `xhigh`, `high`, `medium`) from `models.json` and `resolve_orchestrator_session_routing`.

### Stage 2: Preflight Plan and Lease Boundary Verification

Build the deterministic `--inter-cli` launch plan (`plan_inter_cli_dispatch`), verify parent lease non-contention, and compute `task_sha256` and `first_prompt_sha256`.

### Stage 3: Sequential Lock Acquisition and Seat Launch

Acquire the dispatch lock, spawn the isolated tmux/worktree or subprocess seat, deliver the bound meta-prompt (`SKILL_BY_POINTER` + persona + leased template), and record `initial_run_json_sha256`.

### Stage 4: Readiness Sensing and Non-Invasive Supervision

Monitor child progress via transcript and pane sensors (`seat-readiness`), handling runtime-specific startup dialogs cleanly without disrupting peer sessions.

### Stage 5: Artifact Collection, Hash Verification, and Clean Reap

Verify `done.json`, `task_result.md` SHA-256, and distinct non-boilerplate deltas (`verify_inter_cli_completion_contract`), then close the child pane and release its result lease.

## Artifacts and Verification Gates

- `run.json`, `deliver.jsonl`, `pane-after-deliver.txt`, and `native-result-lease-handoff.json`.
- `done.json`, `task_result.md`, and `mpt-deploy-cli-dispatch-receipt.json`.

## Hard Boundaries

- Never treat a dry-run or preflight receipt as submitted or verified runtime acceptance.
- Never hardcode deprecated model strings in command lines or source code; always resolve from the centralized model registry.
