---
name: pwos-browser-bridge
alias: browser-bridge
description: "Use when driving an existing browser session through DOM and pixels with bounded actions and readback."
category: browser-driving
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Browser Bridge

## Overview

Attaches to an existing browser session and drives it through document and
pixel evidence. Every action is bounded and followed by readback. Headless
and interactive modes are distinct and never conflated.

## Invariants

1. Target window and tab are bound exactly before any input.
2. Notifications are sent only after the previous action is read back.
3. Actions never exceed the declared scope.
4. A missing session is reported, never simulated.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Session Attach

Bind the live session with its window, tab, and origin.

### Stage 2: DOM and Pixel Read

Capture both views and note which one grounds each claim.

### Stage 3: Bounded Action

Run the smallest action that satisfies the step, then read back.

### Stage 4: Notification and Wait

Notify through the exact target, then wait for observable effect.

### Stage 5: Headless or Interactive Disposition

Record which mode produced the result and any focus side effects.

## Artifacts and Verification Gates

- Step receipts with before and after captures and digests.
- Oracle: readback proves the intended visible effect occurred.

## Hard Boundaries

- Never type into an unbound or ambiguous target.
- Never claim an effect without a readback capture.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- runtime-ports: [pwos-runtime-ports](../pwos-runtime-ports/SKILL.md)
- baseline browser-vla: [pwos-browser-vla](../pwos-browser-vla/SKILL.md)
