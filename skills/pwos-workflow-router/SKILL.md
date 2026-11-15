---
name: pwos-workflow-router
alias: workflow-router
description: "Use when selecting the minimal applicable skill graph with fresh capability checks and explicit handoffs."
category: routing-and-orchestration
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Workflow Router

## Overview

Chooses the smallest set of skills that fits the goal. Capability and
prerequisites are resolved fresh for every task. Handoffs are explicit so
responsibility never blurs between seats.

## Invariants

1. Selection is minimal: extra skills require a stated reason.
2. Prerequisites are proven, not assumed from the skill list.
3. Handoffs name owner, inputs, and acceptance oracle.
4. An orchestrator never spawns itself recursively.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Goal Decomposition

Split the goal into bounded, independently checkable parts.

### Stage 2: Phase Ordering

Order the development phases: design, plan, execute, parallel, test-first
build, debugging, review, verify, and skill authoring.

### Stage 3: Capability Resolution

Check what the runtime actually offers, not what is desired.

### Stage 4: Minimal Graph Selection

Pick the smallest skill graph that covers every part.

### Stage 5: Handoff Binding

Record owner, inputs, oracle, and freshness for each edge.

### Stage 6: Execution and Join

Run the graph and join results against each oracle.

## Artifacts and Verification Gates

- Routing receipt with selected skills, prerequisites, and handoffs.
- Oracle: every goal part maps to exactly one executed skill path.

## Hard Boundaries

- Never add a skill without a capability reason.
- Never delegate execution to an unbound seat.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- parallel-work: [pwos-parallel-work](../pwos-parallel-work/SKILL.md)
- skill-authoring: [pwos-skill-authoring](../pwos-skill-authoring/SKILL.md)
