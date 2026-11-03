---
name: pwos-wfc
alias: wfc
description: "Use when composing skills, personas, and inter-CLI runners into a 5-Wave Multi-Persona Triage (MPT:N) DAG with Synergetic Assimilation and Counterpart Limit Coverage."
category: orchestration-and-synthesis
tier: tier-3-high-order-lifecycle
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Wfc Skeleton Procedure

## Overview

Wave Function Collapse (`WFC`) orchestrator that compiles `N` personas (default `N=9` for `MPT:9`) into a 5-wave cognitive DAG (`Planning -> Reasoning -> Adversarial Triage -> Synthesizing/Orchestrating -> Meta-Evaluating`).

## Invariants

1. Five-Wave Topological Order: Wave 0 (`Planning`), Wave 1 (`Reasoning`), Wave 2 (`Adversarial Triage`), Wave 3 (`Synthesizing/Orchestrating`), and Wave 4 (`Meta-Evaluating`) execute in strict dependency order.
2. Four Disjoint Role Tiers: Enforce `Composer != Validator != Synthesizer != Meta-Evaluator` across all `N` seats.
3. Synergetic Assimilation + Counterpart Limit Coverage: Pair every primary mechanism's strength with a complementary mechanism that covers its structural failure mode.
4. Inter-CLI Dispatch Enforcement: Bind each seat to an explicit `--inter-cli` target, model, persona, governing skill, and leased template.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Roster Selection and Role Disjointness Check

Select `N` personas (4 to 15, default 9) and verify zero overlap across Composer, Validator, Synthesizer, and Meta-Evaluator sets.

### Stage 2: Five-Wave DAG Compilation

Wire inter-wave dependencies so each wave consumes the verified outputs of the preceding wave.

### Stage 3: Meta-Prompt Template Provisioning

Render pre-bound [fable-mode](../pwos-fable-mode/SKILL.md) `FULL` templates (`task_<seat_id>_<persona>.md`) with session `lease_token` and `preimage_sha256`.

### Stage 4: Inter-CLI Seat Dispatch

Execute seats across waves via `--inter-cli`, recording per-seat dispatch plans, prompts, and execution receipts.

### Stage 5: Distinct Evidence and Ladder Evaluation

Verify `postimage != preimage`, zero unfilled placeholders, `distinct_delta_count == N`, and Near-Deterministic Ladder pass.

## Artifacts and Verification Gates

- `mpt-manifest.json`, `mpt-legs.json`, and `templates/task_<seat_id>_<persona>.md`.
- `mpt-deploy-cli-dispatch-receipt.json` and `mpt-evaluation-receipt.json`.

## Hard Boundaries

- Never collapse multi-persona waves into a single unreviewed monologue.
- Never allow inline unverified stubs to substitute for enforced template edits.
