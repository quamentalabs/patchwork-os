---
name: systematic-debugging
description: "Use when a test, script, hook, or runtime behaves unexpectedly or fails, enforcing a read-only 5-stage root-cause analysis and weighted matrix before any RED-GREEN-MUTATION fix."
category: debugging-and-remediation
tier: tier-2-methodology-shim
paradigms:
  - workflow
  - prompt-flow
license: MIT
---

# Systematic Debugging Skeleton Procedure

## Overview

Seven-phase disciplined debugging procedure combining prior-lesson ledger lookup, read-only 5-stage root-cause analysis, minimal deterministic reproduction (`RED`), structural remediation (`GREEN`), and scoped mutation verification.

## Invariants

1. Iron Law of Debugging: No code fix is permitted without prior root-cause isolation and a deterministic reproduction test.
2. Ledger Query First (Phase 0): Query the project lesson ledger and knowledge hub before any filesystem search or claim of absence.
3. Read-Only Until Phase 2 Stop: Phases 0 through 2 perform zero repository edits; stop after presenting the weighted fix matrix unless a fix was explicitly requested.
4. Telemetry Over Speculation: Empirical logs, stack traces, byte digests, and sensor captures outrank intuition.
5. Mutation Verification Required: Every reproduction test must fail when the repaired guard is mutated in memory.

## Skeleton Procedure (Ordered Stages)

### Phase 0: Knowledge Hub and Ledger Pre-Query

Query the memory hub and failure ledger for prior occurrences, recording returned event IDs and searched roots before exploring files.

### Phase 1: Read-Only 5-Stage Root-Cause Analysis

Execute (1) Symptom & Telemetry Capture, (2) Boundary & Input Isolation, (3) Mechanism & State Trace, (4) Adversarial Hypothesis Falsification, and (5) Root-Cause Pinpointing without editing source files.

### Phase 2: Five Remediation Proposals and Weighted Matrix

Score candidate fixes across correctness, blast radius, determinism, and maintenance cost (HARD STOP here if analysis-only was requested).

### Phase 3: Minimal Deterministic Reproduction (RED)

Write a minimal automated test that deterministically reproduces the exact failure for the diagnosed reason.

### Phase 4: Minimal Structural Remediation (GREEN)

Apply the smallest structural code change at the root cause that turns the reproduction test green.

### Phase 5: Scoped Mutation Check

Temporarily invert or disable the new guard in a scoped check to confirm the regression test catches the mutation (`CAUGHT`).

### Phase 6: Regression Suite and Post-Mortem Closure

Run the relevant test suite once and record the root cause, fix digest, and prevention rule in the knowledge hub.

## Artifacts and Verification Gates

- Read-only 5-stage root-cause report with weighted remediation matrix.
- Deterministic RED/GREEN reproduction test and mutation kill receipt.

## Hard Boundaries

- Never apply speculative shot-in-the-dark edits before isolating the root cause.
- Never report an unexecuted check as verified; keep unrun checks marked `not_run`.
