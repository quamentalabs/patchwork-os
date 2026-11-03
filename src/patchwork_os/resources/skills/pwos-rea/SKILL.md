---
name: pwos-rea
alias: rea
description: "Use when reverse engineering binaries, CLI runtimes, bundles, protocols, or multi-store distributions and verifying end-to-end Forward-Reverse-Roundtrip (FRR) byte parity."
category: reverse-engineering-and-roundtrip
tier: tier-2-methodology-shim
paradigms:
  - workflow
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Rea Skeleton Procedure

## Overview

Four-stage reverse-engineering and round-trip verification procedure combining static surface fingerprinting, clean-sandbox reverse unpacking, isolated subsystem execution, and second-generation re-export byte-parity checks.

## Invariants

1. Zero Speculative Extrapolation: Every structural claim must cite observed binary strings, AST spans, protocol frames, or SHA-256 byte digests.
2. Clean-Sandbox Reverse Unpack: Always unpack bundles (`.bundle`, `.zip`, archives) into an isolated temporary directory before comparing file hashes.
3. Cross-Store Byte Identity: Compare every tracked file's raw byte SHA-256 across the source repository, reverse-cloned bundle, and unpacked archive (`tree_mismatch_count == 0`).
4. Line-Ending Normalization Guard: Enforce `.gitattributes` (`* text=auto eol=lf`) so cross-OS Git clones never mutate blob SHA-256 digests.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Forward Inventory and Surface Fingerprinting

Inventory source commits, tree OIDs, binary imports, MCP/CLI bridges, and distribution package SHA-256 hashes.

### Stage 2: Reverse Unpack and Byte-Parity Audit

Clone the `.bundle` and extract the `.zip` in an isolated temp sandbox, comparing per-file SHA-256 hashes against the source tree.

### Stage 3: Isolated Subsystem Execution inside Reverse Clone

Run clean-room hygiene checks, pure-Markdown LLM-Wiki graph builds, hybrid statusline rendering, and unit tests inside the unpacked clone.

### Stage 4: Second-Generation Round-Trip Re-Export

Re-export a second-generation `.bundle` and `.zip` from the reverse clone, clone again, and verify `HEAD`, `HEAD^{tree}`, and per-file SHA-256 invariance.

## Artifacts and Verification Gates

- 4-stage Reverse Engineering & Round-Trip Receipt (`rea-patchwork-roundtrip-receipt.json`).

## Hard Boundaries

- Never declare round-trip parity from forward packaging alone without unpacking and re-cloning in a clean sandbox.
