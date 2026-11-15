---
name: pwos-change-review
alias: change-review
description: "Use when requesting and receiving code review with independent verification and explicit revision."
category: review-and-verification
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Change Review

## Overview

Review covers both directions: requesting a review with full context, and
receiving it without defensiveness. The reviewer inspects the shipped text
against the contract, and every finding ends in a disposition.

## Invariants

1. The requester supplies scope, contract, and evidence pointers.
2. The reviewer reads beyond the brief and tests the premises.
3. Every finding is accepted, revised, or rebutted with evidence.
4. An unresolved disagreement names an adjudicator and blocks delivery until
   adjudicated.
5. A verdict is compared against the final shipped text.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Review Request

Package scope, contract, and evidence for the reviewer.

### Stage 2: Independent Inspection

Read the change and its callers, tests, and history.

### Stage 3: Finding Disposition

Classify each finding and record the response.

### Stage 4: Scoped Revision

Apply the smallest fix that addresses the finding.

### Stage 5: Re-Review

Confirm the shipped text matches every disposition.

## Artifacts and Verification Gates

- Review receipt with findings, dispositions, and re-check.
- Oracle: the shipped text matches the final verdict.

## Hard Boundaries

- Never review only the brief and call it complete.
- Never ship a finding without a disposition.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- delivery-line: [pwos-delivery-line](../pwos-delivery-line/SKILL.md)
- completion-check: [pwos-completion-check](../pwos-completion-check/SKILL.md)
