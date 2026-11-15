---
name: pwos-plan-authoring
alias: plan-authoring
description: "Use when authoring an ordered, bounded, checkable plan from an agreed design direction."
category: planning-and-convergence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Plan Authoring

## Overview

Turns an agreed direction into an ordered plan with stable task identities,
dependencies, owners, and acceptance checks. Each task is small enough to
verify on its own and ordered so failures point at the offending step.

## Invariants

1. Every task has a stable ID and an explicit owner.
2. Dependencies are declared in writing.
3. Each task names how it will be checked.
4. The plan stays within its declared scope.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Task Decomposition

Split the direction into bounded tasks with IDs.

### Stage 2: Dependency Ordering

Order tasks and declare their dependencies.

### Stage 3: Owner Binding

Assign one owner per task with its bounded scope.

### Stage 4: Check Definition

Name the acceptance oracle for every task.

### Stage 5: Plan Publication

Record the plan with versions and revision links.

## Artifacts and Verification Gates

- Plan record with task IDs, owners, dependencies, and checks.
- Oracle: every task in the plan has exactly one check.

## Hard Boundaries

- Never write a task without a check.
- Never share a task ID across different meanings.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- plan-convergence: [pwos-plan-convergence](../pwos-plan-convergence/SKILL.md)
- design-dialogue: [pwos-design-dialogue](../pwos-design-dialogue/SKILL.md)
