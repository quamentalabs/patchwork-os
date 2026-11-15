---
name: pwos-completion-check
alias: completion-check
description: "Use when verifying completion before the work is declared done, with fresh evidence and a final verdict."
category: review-and-verification
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Completion Check

## Overview

Last gate before done. Every distinct behavior the request asked for is
checked against the real code with fresh evidence. A claim of done without a
fresh check is not done.

## Invariants

1. Evidence is fresh in this session, not recalled from earlier.
2. Each check exercises the real consumption boundary; a suite that never
   calls the consumer maps to not_run, not to verified.
3. Each requirement maps to a check and a result.
4. Failing checks block the done verdict.
5. Unrun checks stay reported as unrun.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Requirement Enumeration

List every behavior, condition, and edge case requested.

### Stage 2: Fresh Evidence

Run the repository checks and the targeted probes.

### Stage 3: Per-Item Verdict

Mark each requirement verified, failed, or not_run.

### Stage 4: Gap Resolution

Fix gaps and re-run the affected checks only.

### Stage 5: Done Declaration

Declare done only with the full verdict table attached.

## Artifacts and Verification Gates

- Completion receipt with per-requirement verdicts and commands.
- Oracle: the verdict table matches the observed check output.

## Hard Boundaries

- Never mark an unrun check as verified.
- Never trim a requirement to fit the result.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- change-review: [pwos-change-review](../pwos-change-review/SKILL.md)
- baseline harness-audit: [pwos-harness-audit](../pwos-harness-audit/SKILL.md)
