---
name: pwos-session-ownership
alias: session-ownership
description: "Use when owning sessions through leases, task scope, process generation, expiry, renewal, reaping, and recovery."
category: sessions-and-leases
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Session Ownership

## Overview

Ownership is proven by a live lease, not by memory. Mint before claim,
claim before use, and renew before expiry. Crash recovery replays the same
receipts.

## Invariants

1. The first write requires a held lease in the shared registry.
2. Task scope bounds exactly the paths a session may touch.
3. Process generation binds the owner to its live process.
4. Expired or reaped leases never authorize new writes.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Mint

Issue the token file and register the pending session.

### Stage 2: Claim

Bind the session to its runtime, effort, and task scope.

### Stage 3: Renew

Extend expiry only while the owner is demonstrably live.

### Stage 4: Reap

Reap dead owners and release their scopes with receipts.

### Stage 5: Recovery

Rebuild ownership from receipts after a crash, never from guesses.

## Artifacts and Verification Gates

- Lease receipt with claim range, scope, and expiry.
- Oracle: the registry answers exactly who holds what.

## Hard Boundaries

- Never write without a live claim.
- Never touch another session's scope.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- runtime-ports: [pwos-runtime-ports](../pwos-runtime-ports/SKILL.md)
- baseline session-lifecycle: [pwos-session-lifecycle](../pwos-session-lifecycle/SKILL.md)
