---
name: pwos-design-dialogue
alias: design-dialogue
description: "Use when exploring requirements and design options before committing to a plan."
category: planning-and-convergence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Design Dialogue

## Overview

Structured exploration of requirements and alternatives. Options are
compared, tradeoffs are named, and the chosen direction is recorded with its
evidence. No implementation commitment is made inside this skill.

## Invariants

1. Every option carries its cost and its friction.
2. Decisions reference the evidence that shaped them.
3. Unresolved questions stay open rather than being guessed away.
4. The dialogue ends with a recorded decision, not a mood.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Requirement Probing

Clarify the goal, constraints, and success criteria.

### Stage 2: Option Formation

Draft distinct options with their tradeoffs.

### Stage 3: Adversarial Attack

Test each option against the failure modes that matter.

### Stage 4: Decision Recording

Bind the chosen option to its evidence and scope.

### Stage 5: Handoff

Pass the decision record to plan authoring with open questions listed.

## Artifacts and Verification Gates

- Decision record with options, tradeoffs, and chosen direction.
- Oracle: the record reproduces the decision inputs exactly.

## Hard Boundaries

- Never start implementation inside the dialogue.
- Never hide an unresolved question behind a default.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- plan-authoring: [pwos-plan-authoring](../pwos-plan-authoring/SKILL.md)
- baseline grilling: [pwos-grilling](../pwos-grilling/SKILL.md)
