---
name: pwos-grilling
alias: grilling
description: "Use when a plan, decision, or architecture needs relentless one-question-at-a-time stress-testing down every branch of the decision tree before any execution begins."
category: discovery-and-alignment
tier: tier-1-epistemic-gate
paradigms:
  - workflow
  - meta-prompting
license: MIT
---

# Grilling Skeleton Procedure

## Overview

Relentless decision-tree interview procedure that walks down every branch of a design or plan, resolving dependencies between decisions one by one before any mutation or implementation is permitted.

## Invariants

1. One Question at a Time: Never ask multiple questions in a single turn; wait for explicit operator feedback on each question before advancing.
2. Recommended Default Required: Every question must carry a concrete, reasoned recommended answer.
3. Environment Lookup First: If a fact can be discovered from the filesystem, AST, git history, or runtime tools, inspect the environment directly instead of asking the operator.
4. Decisions Belong to the Operator: Empirical facts belong to tool lookups; value tradeoffs and architectural decisions belong to the operator.
5. No Premature Action: Do not modify code or execute the plan until the operator explicitly confirms shared understanding.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Environment Fact Pre-Lookup

Scan the repository, AST codemap, and existing documentation to resolve all factual questions without burdening the operator.

### Stage 2: Decision-Tree Branch Decomposition

Map the root architectural or operational choices and order them by prerequisite dependency so upstream choices settle first.

### Stage 3: Single-Question Probe with Recommended Answer

Present exactly one unresolved decision branch, state the trade-offs clearly, and provide one recommended option with its rationale.

### Stage 4: Dependency Resolution and Branch Pruning

Record the operator's answer, prune invalidated branches of the decision tree, and advance to the next dependent decision.

### Stage 5: Shared Understanding Confirmation Gate

Summarize the settled decision tree and wait for explicit operator confirmation before transitioning to planning or execution.

## Artifacts and Verification Gates

- Settled decision-tree ledger mapping each question to the operator's chosen branch.
- Explicit shared-understanding confirmation receipt prior to implementation.

## Hard Boundaries

- Never batch multiple questions into a numbered questionnaire.
- Never ask the operator a factual question that a local read or grep can answer.
- Never treat silence or partial feedback as authorization to execute.
