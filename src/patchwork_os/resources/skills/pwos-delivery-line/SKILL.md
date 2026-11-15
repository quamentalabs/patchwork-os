---
name: pwos-delivery-line
alias: delivery-line
description: "Use when running a software factory from requirements through build, review, and bounded delivery gates."
category: delivery-and-gates
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Delivery Line

## Overview

A directed acyclic factory pipeline: requirements, design, build, review, and
delivery. Each step has an explicit owner, runtime, model, effort, and skill
assignment. Nothing is left as fire and forget.

## Invariants

1. Every step declares its owner and its acceptance oracle.
2. Composer and validator are distinct actors.
3. A step never advances on its own report of success.
4. Blocked steps stay visible until released or canceled.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Requirements Binding

Freeze the requirement set with stable IDs and acceptance criteria.

### Stage 2: Plan DAG Construction

Order steps with dependencies, owners, and bounded scopes.

### Stage 3: Build Execution

Run each step with recorded inputs, outputs, and receipts.

### Stage 4: Independent Review

A separate validator checks evidence against the frozen criteria.

### Stage 5: Bounded Delivery

Deliver only the reviewed candidate, with rollback noted.

## Artifacts and Verification Gates

- Step receipts with owners, hashes, and verdicts.
- Oracle: review replays each criterion against the delivered bytes.

## Hard Boundaries

- Never share composer and validator for the same step.
- Never deliver an unreviewed or unreplayed candidate.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- plan-authoring: [pwos-plan-authoring](../pwos-plan-authoring/SKILL.md)
- plan-execution: [pwos-plan-execution](../pwos-plan-execution/SKILL.md)
- change-review: [pwos-change-review](../pwos-change-review/SKILL.md)
