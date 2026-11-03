---
name: pwos-deconstruct
alias: deconstruct
description: "Use when an ambiguous target needs one bounded pre-execution pass that scopes, explores, deconstructs into elements and mechanisms, classifies KK/KU/UK/UU, attacks hypotheses, verifies via FRR, and returns a scored option set with explicit tradeoff placement."
category: epistemic-analysis
tier: tier-1-epistemic-gate
paradigms:
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Deconstruct Skeleton Procedure

## Overview

Seven-stage pre-execution deconstruction procedure that produces a bounded Deconstruction Brief with epistemic classification (`KK/KU/UK/UU`), falsifiable hypotheses, `FRR` verification, and a config-weighted option matrix.

## Invariants

1. Recommend Only: Deconstruct produces evidence and a scored option set; it never executes, mutates, or claims runtime acceptance.
2. Strict Epistemic Tagging: Every load-bearing element is classified as `KK` (known with evidence), `KU` (known gap with named probe), `UK` (tacit assumption), or `UU` (unprobed residual surface).
3. No Unverified Promotion: Never promote `UU` or `UK` to `KK` without a concrete empirical observation and source digest.
4. Explicit Tradeoff Placement: Every recommendation states its cost, reversal path, and where operational friction lands.
5. 3xPR Provenance: Every brief records `Plan`, `Purpose`, `Procedure`, `Reason`, `Reference`, and `Result`.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Scope

Name the target, the decision the brief feeds, and the observable success check while separating verified facts from assumptions.

### Stage 2: Explore

Gather bounded evidence from the repository and codemap, recording source identifiers and SHA-256 digests; record missing evidence as absent.

### Stage 3: Deconstruct (KK / KU / UK / UU)

Split the subject into elements, mechanisms, and dependencies, classifying each into `KK`, `KU`, `UK`, or `UU`.

### Stage 4: Hypothesize

Formulate candidate mechanisms and directions, pairing every hypothesis with the exact observation that would falsify it.

### Stage 5: Adversarial Attack

Execute the cheapest decisive probe against the leading hypothesis at a real boundary; two failed attempts with the same remedy invalidate the diagnosis.

### Stage 6: Verify (FRR: Forward / Reverse / Roundtrip)

Check Forward behavior at the boundary, Reverse traceability back to source constraints, and Roundtrip reproducibility at the consumer.

### Stage 7: Recommend Scored Option Set

Evaluate at least three independent candidate approaches (plus genuine hybrids where applicable) against explicit criteria weights and recommend one with its reversal path.

## Artifacts and Verification Gates

- Deconstruction Brief containing `3xPR`, `KK/KU/UK/UU` table, `FRR` verification, and scored option matrix.

## Hard Boundaries

- Never claim a universal no-tradeoff outcome that hides operational friction.
- Escalate to [fable-mode](../pwos-fable-mode/SKILL.md) when transitioning from recommendation to artifact mutation.
