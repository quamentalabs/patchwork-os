---
name: pwos-plan-convergence
alias: plan-convergence
description: "Use when resuming, realigning, or recapping work with stable task identities, dependencies, and an observed frontier."
category: planning-and-convergence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Plan Convergence

## Overview

Resumes interrupted work without reactivating stale intentions. Stable task
identifiers and dependencies survive interruption. The observed frontier is
kept separate from plans that were merely intended.

## Invariants

1. Task IDs never change meaning across resume.
2. Observed progress is reported separately from intended progress.
3. Stale conclusions are invalidated by newer evidence, not edited silently.
4. Resume reads the frontier before planning new work.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Frontier Read

Load the last observed frontier, attempts, and operator corrections.

### Stage 2: Realign

Re-run due checks and mark which premises still hold.

### Stage 3: Recap

Summarize closed, open, and blocked tasks with evidence links.

### Stage 4: Task Graph Sync

Synchronize plan, todo, and map views so they cannot diverge silently.

### Stage 5: Continuation Binding

Carry the frontier into the next session entry with its receipts.

## Artifacts and Verification Gates

- Frontier receipt with per-task observed status and attempt counts.
- Oracle: a second reader reconstructs the same frontier from the records.

## Hard Boundaries

- Never reactivate a stale plan without fresh evidence.
- Never merge intentionally different task views without a link.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- plan-authoring: [pwos-plan-authoring](../pwos-plan-authoring/SKILL.md)
- plan-execution: [pwos-plan-execution](../pwos-plan-execution/SKILL.md)
- baseline quarry: [pwos-quarry](../pwos-quarry/SKILL.md)
