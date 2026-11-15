---
name: pwos-experience-loop
alias: experience-loop
description: "Use when turning observations into evaluated, promoted, retrievable, and eventually retired lessons."
category: learning-and-retirement
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Experience Loop

## Overview

Observation becomes a candidate lesson, passes independent evaluation, is
promoted under a reversible canary, gets retrieved for next use, and is
revised or retired from measured outcomes. Authority never widens on its own.

## Invariants

1. A lesson is a claim with evidence, not a slogan.
2. Promotion requires an independent evaluation, not self-report.
3. Canary promotion is reversible in one step.
4. Drift is measured by outcomes, not by link counts.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Observation Capture

Record what happened, with inputs, outputs, and hashes.

### Stage 2: Candidate Lesson

Draft a bounded lesson that another seat could test.

### Stage 3: Independent Evaluation

A separate evaluator replays the evidence and rules.

### Stage 4: Canary Promotion

Enable the lesson for a bounded set with rollback ready.

### Stage 5: Retrieval and Retirement

Track each reuse outcome and revise or retire on evidence.

## Artifacts and Verification Gates

- Loop receipt with candidate, evaluation, canary, and outcome links.
- Oracle: next-use retrieval verifies current premises before reuse.

## Hard Boundaries

- Never auto-widen authority from a lesson.
- Never retire evidence that proves revision.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- memory-hub: [pwos-memory-hub](../pwos-memory-hub/SKILL.md)
- baseline crucible: [pwos-crucible](../pwos-crucible/SKILL.md)
