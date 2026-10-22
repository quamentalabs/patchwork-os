---
name: pwos-stdd
alias: stdd
description: "Use when orchestrating multi-seat subagent-driven development combined with the 9-step TDD build order, role-disjoint wave allocation, and quota-aware inter-CLI dispatch."
category: autonomous-lifecycle
tier: tier-3-high-order-lifecycle
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: MIT
---

# Stdd Skeleton Procedure

## Overview

Three-tier autonomous development lifecycle uniting Wave Function Collapse (`WFC`) DAG planning, role-disjoint persona seat allocation (`Composer != Validator != Synthesizer != Meta-Evaluator`), inter-CLI execution, and the 9-step [tdd](../pwos-tdd/SKILL.md) build order.

## Invariants

1. Strict Role Disjointness: The seat that composes code or plans (`Composer`) must never serve as its own `Validator`, `Synthesizer`, or `Meta-Evaluator`.
2. Leased Path Ownership: Every worker leg claims explicit file paths before writing and never mutates foreign worktree files.
3. Delivery-First Anti-Choke Budget: After one independent review, one scoped fix, and one re-review, defer non-critical meta-machinery findings until consumer content is delivered.
4. Empirical Receipt Binding: Every completed wave leg binds its task digest, diff digest, and test receipt into the plan/task store.
5. Quota-Aware Routing: Select target CLI runtimes and model tiers based on measured quota bands and task complexity.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Bind Work, Plan Frontier, and Knowledge Receipt

Load the active plan frontier, query the knowledge hub, and claim the session lease for all target write paths.

### Stage 2: Allocate Role-Disjoint SDD Wave Legs

Compile the task DAG into parallelizable waves via [wfc](../pwos-wfc/SKILL.md), assigning distinct personas and skills to Planning, Implementation, Adversarial Review, Synthesis, and Meta-Evaluation.

### Stage 3: Execute Inter-CLI Dispatch

Dispatch each wave leg through the inter-CLI runner with bound `task_<seat>.md` templates, lease tokens, and explicit workspace scopes.

### Stage 4: Hand-Compose Recovery on Defective Contracts

If a contract or adapter refuses, diagnose the exact boundary, hand-compose one working instance at the consumer, and upgrade the contract.

### Stage 5: Enforce 9-Step TDD and Mutation Gates

Verify every implementation leg through [tdd](../pwos-tdd/SKILL.md) (hand-compose, run-x3 byte parity, regression suite, and mutation kill check).

### Stage 6: Consumer Loop Closure and Plan Sync

Fold accepted review findings into the artifact, synchronize the atomic task store, and land verified changes via an isolated Git index.

## Artifacts and Verification Gates

- Compiled wave manifest (`mpt-manifest.json`) with disjoint role tiers.
- Per-seat edited `task_<seat>.md` templates and consolidated verification receipt.

## Hard Boundaries

- Never allow a single persona seat to self-approve its own implementation.
- Never overwrite foreign staged or dirty files in a shared worktree.
