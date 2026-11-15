---
name: pwos-parallel-work
alias: parallel-work
description: "Use when splitting work across seats with bounded isolation and a join that verifies every part."
category: routing-and-orchestration
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Parallel Work

## Overview

Independent parts run concurrently under explicit isolation. A separate join
step collects every result and checks each against its oracle. Parallelism
never trades away ownership or verification.

## Invariants

1. Each seat owns a bounded, disjoint scope.
2. Shared files are never edited concurrently.
3. Every seat receives the same acceptance oracle.
4. The join accounts for every launched seat.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Split

Partition the work into disjoint, bounded parts.

### Stage 2: Isolation Binding

Bind each seat to its scope and its oracle.

### Stage 3: Parallel Execution

Run the seats concurrently and collect their receipts.

### Stage 4: Join Verification

Check every result against its oracle, including failures.

### Stage 5: Reconciliation

Merge in a declared order with conflicts reported, not hidden.

## Artifacts and Verification Gates

- Join receipt accounting for every seat and verdict.
- Oracle: seat count equals accounted count.

## Hard Boundaries

- Never share writable scope between seats.
- Never drop an unfinished seat silently.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- workflow-router: [pwos-workflow-router](../pwos-workflow-router/SKILL.md)
- plan-execution: [pwos-plan-execution](../pwos-plan-execution/SKILL.md)
