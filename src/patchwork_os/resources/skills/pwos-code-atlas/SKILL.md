---
name: pwos-code-atlas
alias: code-atlas
description: "Use when mapping a codebase with a deterministic AST symbol caller graph, lexical fallback, and content-hash freshness."
category: code-intelligence
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Code Atlas

## Overview

Deterministic map of files, symbols, callers, and ports. The index is derived
from tokens and structure, never from model memory. Optional semantic
synthesis runs as a separate, clearly labeled consumer.

## Invariants

1. Every node cites an exact file span and content hash.
2. Freshness is proven by hash comparison, not by timestamps alone.
3. Lexical fallback never upgrades a guess into a structural claim.
4. Graph size is reported; truncated results are not presented as complete.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Inventory and Candidate Selection

List target files and choose ranked candidates by symbol and name match.

### Stage 2: AST Extraction

Parse files into nodes and edges with exact spans and hashes.

### Stage 3: Lexical Fallback

Where parsing fails, mark the gap explicitly and serve token matches.

### Stage 4: Snapshot and Freshness

Record content hashes and compare on the next run before reuse.

### Stage 5: Separated Synthesis

Optional semantic summary links back to nodes; it never rewrites them.

## Artifacts and Verification Gates

- Index receipt with per-file hashes, node count, edge count, and gaps.
- Oracle: querying a known symbol returns its exact span and hash.

## Hard Boundaries

- Never present a partial index as exhaustive.
- Never embed semantic commentary into the structural index.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- forensics: [pwos-artifact-forensics](../pwos-artifact-forensics/SKILL.md)
