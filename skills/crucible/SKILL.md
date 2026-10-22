---
name: crucible
description: "Use when a design, architecture, or plan must be hardened by repeated adversarial melting across construction-blind lenses with seeded-flaw dryness verification until it fuses."
category: adversarial-hardening
tier: tier-2-methodology-shim
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
license: MIT
---

# Crucible Skeleton Procedure

## Overview

Multi-round adversarial design smelting loop that attacks a hash-bound design charge from distinct construction-blind lenses until the charge reaches a measured terminal state (`fused`, `molten`, `stalled`, or `cracked`).

## Invariants

1. Three-Part Fusion Stop Condition: A charge is `fused` only when (1) Frontier is empty, (2) Dryness holds for `K=2` consecutive rounds, and (3) Every load-bearing claim is anchored to evidence or a named falsifier.
2. Seeded-Flaw Dryness Guard: A round counts as dry only if a deliberately planted flaw in the seeded charge was caught by a construction-blind lens in that same round (`DRYNESS_UNMEASURED` otherwise).
3. Construction Blindness: Attacking lenses receive only the current charge bytes, never prior round rationale or defense prose.
4. Distinct Attack Lenses: Parallel attackers must use non-overlapping lenses (`Correctness`, `Boundary`, `Premise`, `Operator`, `Cost`).
5. No Runtime Acceptance Claim: Crucible hardens design charges and always records `runtime_acceptance: not_run` until implementation is verified.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Charge Fixation

Write the current design or plan as a self-contained artifact and compute its canonical `charge_sha256` (plus a separate seeded copy containing one planted defect).

### Stage 2: Parallel Blind Heat

Dispatch distinct construction-blind lenses (`Correctness`, `Boundary`, `Premise`, `Operator`, `Cost`) against the charge without sharing prior rationale.

### Stage 3: Seeded-Flaw Assay

Verify whether the blind lenses caught the planted flaw; if missed, mark the round `DRYNESS_UNMEASURED` and recalibrate the lenses.

### Stage 4: Skim and Recast

Deduplicate surviving findings, check whether any finding falsifies the root premise (`cracked`), and fold valid fixes into the next round's charge.

### Stage 5: Terminal Disposition

Classify the round as `fused` (ready for [fable-mode](../fable-mode/SKILL.md)), `molten` (continue melting), `stalled` (budget exhausted with named molten regions), or `cracked` (re-cast from root).

## Artifacts and Verification Gates

- Fused design charge with `charge_sha256` and round-by-round adversarial ledger.
- Seeded-flaw catch receipt proving attacker sensitivity.

## Hard Boundaries

- Never score a round as dry without a caught seeded flaw from an uncompromised blind lens.
- Never report `stalled` or `molten` charges as `fused`.
