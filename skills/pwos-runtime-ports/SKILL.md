---
name: pwos-runtime-ports
alias: runtime-ports
description: "Use when discovering runtime capabilities and contracting launch, capture, acknowledgement, cleanup, and quota."
category: runtime-and-ports
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Runtime Ports

## Overview

Portable contracts for what a runtime can actually do. Discovery is honest:
unsupported and not_run are first-class outcomes. No fake parity is claimed
for capabilities a runtime does not offer.

## Invariants

1. Discovery reads the runtime itself, not its documentation.
2. Shared-memory hosts avoid double-counting physical memory and commit
   backing across storage volumes.
3. Launch and cleanup are paired in every receipt.
4. Acknowledgement requires observable evidence, not a queued signal.
5. Quota and resource use are recorded beside their effect. One quota signal
   never removes the runtime; quota exhaustion reports deferred-until-reset
   with re-measure, not unsupported.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Capability Discovery

Enumerate host paths, terminals, launchers, and capture methods.

### Stage 2: Contract Binding

Record the exact contract the caller will use. For terminal input delivery,
bind the target pane or process identity, read back buffer emptiness before
typing, require transcript-observed acknowledgement, and report the exact
result unsupported when buffer capture is absent.

### Stage 3: Launch and Capture

Start the target and capture its output with bounds.

### Stage 4: Acknowledgement

Verify the effect through observable state, not through intent.

### Stage 5: Cleanup and Quota

Release resources and record quota consumed.

## Artifacts and Verification Gates

- Port receipt with discovery, contract, outcome, and cleanup evidence.
- Oracle: a repeated run reports the same capability set.

## Hard Boundaries

- Never claim an unsupported capability as available.
- Never report not_run as success.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- session-ownership: [pwos-session-ownership](../pwos-session-ownership/SKILL.md)
- baseline runtime-dispatch: [pwos-runtime-dispatch](../pwos-runtime-dispatch/SKILL.md)
- baseline deploy-cli: [pwos-deploy-cli](../pwos-deploy-cli/SKILL.md)
- integrated terminal-messaging: [pwos-terminal-messaging](../pwos-terminal-messaging/SKILL.md)
