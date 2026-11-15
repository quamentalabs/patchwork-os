---
name: pwos-evidence-ledger
alias: evidence-ledger
description: "Use when maintaining claims, sources, observations, decisions, and contradictions with exact hashes."
category: evidence-and-records
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Evidence Ledger

## Overview

An append-only ledger of claims, sources, observations, decisions, and
contradictions. Every entry carries exact hashes and timestamps. Replacement
is atomic and linked back to the entries it supersedes.

## Invariants

1. Append is the default; mutation is a linked replacement.
2. Hashes and timestamps bind each entry to its evidence.
3. Contradictions stay visible until adjudicated.
4. Private and public boundaries are enforced per entry.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Claim Entry

Record a claim with its source and evidence hashes.

### Stage 2: Observation Entry

Append measured observations with their instruments and bounds.

### Stage 3: Decision Entry

Record dispositions with rationale and reviewer identity.

### Stage 4: Contradiction Entry

Link conflicting entries and keep both visible.

### Stage 5: Atomic Replacement

Supersede entries through a single atomic entry swap with receipts. A
multi-file mutation stays per-surface and journaled, never claimed atomic.

## Artifacts and Verification Gates

- Ledger receipt with entry hashes and link checks.
- Oracle: recomputing hashes over the log reproduces the chain head.

## Hard Boundaries

- Never rewrite history in place.
- Never publish private evidence past its visibility scope.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- memory-hub: [pwos-memory-hub](../pwos-memory-hub/SKILL.md)
