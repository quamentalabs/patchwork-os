---
name: pwos-branch-convergence
alias: branch-convergence
description: "Use when converging branches with exact stash identity, preimage compare-and-swap, rollback, and consent scope."
category: branch-convergence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Branch Convergence

## Overview

Safe branch convergence: inventory first, merge intent second, exact restore
identity third. Preimages are swapped per surface; rollback is journaled and
re-runnable, never atomic across surfaces. No unique data is pruned silently.

## Invariants

1. Inventory covers dirty, staged, untracked, ignored, submodule, and lease
   state before any branch movement.
2. The closest-node merge intent is preserved in writing.
3. Stash identity is exact: object ID, move path, and pop result.
4. Active checkouts require in-scope consent before touch.
5. Every surface is classified as preimage, postimage, or foreign.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Inventory

Record branch state, dirty files, submodules, and held leases.

### Stage 2: Intent Preservation

Write the merge intent and the closest-node rationale.

### Stage 3: Preimage Compare-and-Swap

Stage the expected preimage and compare again before writing.

### Stage 4: Journaling and Recovery

Journal intent and completion per mutation. Classify each surface, restore
in reverse order, refuse on foreign drift, and make recovery re-runnable.

### Stage 5: Exact Stash Restore

Restore by object ID and verify the pop result per path.

### Stage 6: Rollback on Conflict

Restore the preimage and report the conflict with evidence.

### Stage 7: Safe Prune

Census the tree, preserve ignored, submodule, and untracked uniques as an
exported artifact, remove without force, then verify the result.

## Artifacts and Verification Gates

- Convergence receipt with inventory, preimage, and restore identities.
- Oracle: working tree hash matches the recorded post state.

## Hard Boundaries

- Never prune a tree that holds unique data.
- Never move a branch without the recorded preimage.
- Never claim multi-file atomicity for a landing.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- plan-execution: [pwos-plan-execution](../pwos-plan-execution/SKILL.md)
