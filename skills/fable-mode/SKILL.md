---
name: fable-mode
description: "Use when a nontrivial workflow, CLI, architecture, or multi-agent leg requires the 6-gate evidence-grounded wrapper with 3xPR, FRR, KK/KU/UK/UU, no-tradeoff invariants, and enforced template Edit."
category: governance-and-verification
tier: tier-2-methodology-shim
paradigms:
  - meta-prompting
  - prompt-flow
license: MIT
---

# Fable Mode Skeleton Procedure

## Overview

Six-gate evidence-grounded execution wrapper (`FULL` depth) requiring structured `3xPR` records, `FRR` (`Forward / Reverse / Roundtrip`) verification, `KK/KU/UK/UU` epistemic grids, `no-tradeoff` invariant coverage, and verified template edits.

## Invariants

1. Six Ordered Gates: Execute Scope (Gate 1), Evidence (Gate 2), Adversarial Attack (Gate 3), FRR Verification (Gate 4), Bounded Learning (Gate 5), and Closed-Loop Return (Gate 6) in sequence.
2. Complete 3xPR Packet: Record `Plan`, `Purpose`, `Procedure`, `Reason`, `Reference`, and `Result` with concrete file and SHA-256 citations.
3. FRR Triangulation: Verify every claim in Forward execution, Reverse source-to-claim audit, and Roundtrip consumer replay.
4. Pre-Image vs Post-Image Edit Enforcement: Every seat must edit its assigned `task_<seat>.md` template so `postimage_sha256 != preimage_sha256` with zero unfilled placeholders.
5. Zero Boilerplate Gaming: Post-preimage deltas across multi-persona seats must be normalized and verified as distinct (`distinct_delta_count == N`).

## Skeleton Procedure (Ordered Stages)

### Gate 1: Scope and Invariant Binding

Define the bounded target, lease token, owned paths, and non-negotiable `no-tradeoff` invariants.

### Gate 2: Evidence Collection and KK/KU/UK/UU Classification

Collect primary source digests and classify all domain knowledge into `KK`, `KU`, `UK`, and `UU`.

### Gate 3: Adversarial Attack

Challenge the implementation or design at its weakest boundary and record whether the guard held.

### Gate 4: FRR (Forward / Reverse / Roundtrip) Verification

Run deterministic Tier-0 checks across Forward build, Reverse unpack/inspection, and Roundtrip consumer execution.

### Gate 5: Bounded Learning

Extract reusable success patterns and failure modes into the knowledge hub without speculative generalization.

### Gate 6: Closed-Loop Return Receipt

Emit the signed JSON evaluation receipt and verify template postimage hashes.

## Artifacts and Verification Gates

- Edited `task_<seat>.md` containing a valid `fable-full` JSON frame and human-readable audit.
- Cryptographic evaluation receipt (`mpt-evaluation-receipt.json`).

## Hard Boundaries

- Never mark `runtime_acceptance` as `verified` without an actual consumer execution receipt.
- Never accept duplicate boilerplate text appended across multiple seat templates.
