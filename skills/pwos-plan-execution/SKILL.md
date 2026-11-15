---
name: pwos-plan-execution
alias: plan-execution
description: "Use when executing an authored plan task by task with receipts and bounded retries."
category: planning-and-convergence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Plan Execution

## Overview

Runs an authored plan in dependency order. Attempts are counted per stable
task ID. Each attempt produces a receipt. Repeated failure delegates through
the declared route instead of retrying silently forever.

## Invariants

1. Attempts are counted per task ID across sessions.
2. Every attempt records its inputs and outputs.
3. A failing check stops the run, not the reporting.
4. Reported status distinguishes executed from intended.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Task Selection

Pick the next ready task from the dependency frontier.

### Stage 2: Bounded Attempt

Execute with the declared scope and oracle.

### Stage 3: Receipt Registration

Store the attempt receipt beside the task record.

### Stage 4: Retry or Delegate

Retry within the bound, then delegate through the declared route.

### Stage 5: Frontier Update

Advance the observed frontier and publish the next state.

## Artifacts and Verification Gates

- Attempt receipts with counts and verdicts per task.
- Oracle: the receipt chain shows every attempt in order.

## Hard Boundaries

- Never reset an attempt counter silently.
- Never report intended work as observed work.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- delivery-line: [pwos-delivery-line](../pwos-delivery-line/SKILL.md)
- parallel-work: [pwos-parallel-work](../pwos-parallel-work/SKILL.md)
- baseline wfc: [pwos-wfc](../pwos-wfc/SKILL.md)
