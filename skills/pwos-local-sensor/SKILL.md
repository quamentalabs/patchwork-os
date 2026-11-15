---
name: pwos-local-sensor
alias: local-sensor
description: "Use when observing local state with a deterministic cursor, a closed-vocabulary model, and human steering."
category: sensing-and-steering
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Local Sensor

## Overview

Local observation with an incremental cursor first, then a closed-vocabulary
model for classification. The main judge owns disposition. Human steering
overrides automated hints. Live host, model, quota, reset, and resource
selection are explicit and auditable.

## Invariants

1. The deterministic cursor reports offset, hash, and count per read.
2. The model verdict uses a closed vocabulary only.
3. The no-thought-output contract holds: reasoning stays out of evidence.
4. Errors and uncertainty are reported, never smoothed away.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Cursor Read

Advance the deterministic cursor and record the new position.

### Stage 2: Model Observation

Ask the closed-vocabulary model for a bounded verdict.

### Stage 3: Judge Disposition

The main judge accepts, rejects, or escalates the verdict.

### Stage 4: Human Steering

Apply operator steering and re-observe the affected state.

### Stage 5: Resource Binding

Record host, model, quota, reset, and resource choices with receipts.

## Artifacts and Verification Gates

- Sensor receipt with cursor positions, verdicts, and disposition.
- Oracle: re-reading from the recorded offset reproduces the same entries.

## Hard Boundaries

- Never let a hint override the judge.
- Never store reasoning text as evidence.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- experience-loop: [pwos-experience-loop](../pwos-experience-loop/SKILL.md)
