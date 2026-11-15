---
name: pwos-artifact-forensics
alias: artifact-forensics
description: "Use when inspecting source, binaries, bundles, or runtime behavior to reconstruct cause from observed evidence."
category: reverse-engineering-and-roundtrip
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Artifact Forensics

## Overview

Evidence-first inspection of artifacts. Every claim cites bytes, strings,
frames, or hashes. Hypotheses are tested against the artifact itself, and
conclusions are rebuilt from source outward.

## Invariants

1. No promotional shortcuts, no bypass grants, no hidden mutations.
2. Each finding names the exact artifact bytes that support it.
3. Round-trip claims require an actual reverse pass, not forward packaging.
4. Unknown regions stay labeled as unknown.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Artifact Inventory

Record hashes, sizes, formats, and available tooling for each artifact.

### Stage 2: Static Inspection

Extract strings, symbols, frames, and structure without executing the target.

### Stage 3: Hypothesis Attack

Form competing explanations and design observations that distinguish them.

### Stage 4: Runtime Observation

Run bounded probes and record outputs as evidence, never as assertions.

### Stage 5: Causal Reconstruction

Rebuild the causal chain from source outward and compare against observation.

## Artifacts and Verification Gates

- Forensic receipt with hashes, hypotheses, and discriminating observations.
- Oracle: independent re-observation reproduces each cited byte claim.

## Hard Boundaries

- Never claim a cause that the artifact bytes do not support.
- Never execute a target beyond the declared bounded probe scope.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- atlas: [pwos-code-atlas](../pwos-code-atlas/SKILL.md)
- baseline rea: [pwos-rea](../pwos-rea/SKILL.md)
