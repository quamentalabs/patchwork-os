---
name: tdd
description: "Use when building or extending any repeatable script, compiler, hook, or CLI tool, enforcing the 9-step hand-compose, register-early, scriptify, run-x3 byte-comparison, and mutation meta-evaluation chain."
category: build-discipline
tier: tier-2-methodology-shim
paradigms:
  - workflow
  - prompt-flow
license: MIT
---

# Tdd Skeleton Procedure

## Overview

Nine-step empirical build order ensuring that every automated tool or generator is preceded by a hand-composed known-good instance at the real consumer and verified for byte-level determinism across three consecutive runs.

## Invariants

1. Hand-Compose Before Generator: Assemble and verify one working instance by hand at the real consumer before writing a generator or script.
2. Dogfood Before Full Polish: Register and exercise the working capability at 70 to 80 percent observed reproducibility within bounded scope rather than stalling delivery.
3. Run x3 Byte Determinism: Execute the scripted tool three consecutive times against a restored watch directory and verify identical exit code, stdout, stderr, and artifact SHA-256 hashes.
4. Tests Guard Capabilities: Regression tests lock in a working capability and encode every obstacle encountered during hand-composition.
5. Planned Mutation Meta-Evaluation: Verify that the regression suite kills scoped in-memory mutations (`0` survivors).

## Skeleton Procedure (Ordered Stages)

### Step 1: Hand-Compose at Real Consumer

Manually construct one input/output instance and make it succeed at the actual downstream consumer before writing automation code.

### Step 2: Record Verbatim Success Pattern and Obstacles

Write down the exact invocation, arguments, return code, and every obstacle or edge case discovered during Step 1.

### Step 3: Register and Dogfood Early

Expose the working capability for real use immediately while keeping unobserved lanes explicitly marked `not_run`.

### Step 4: Scriptify

Implement the script or module to reproduce the hand-composed known-good artifact deterministically.

### Step 5: Run x3 and Compare Bytes

Run the script three times in a clean sandbox and assert byte-for-byte identity across all outputs and SHA-256 digests.

### Step 6: Write Regression Tests from Obstacles

Create unit and integration tests that assert byte parity with the hand-composed instance and cover every obstacle from Step 2.

### Step 7: Execute Semantic Test Suite Once

Run the target test suite once to confirm green status without redundant re-runs.

### Step 8: Scoped Mutation Meta-Evaluation

Mutate each critical guard, verify the test suite fails (`CAUGHT`), and restore exact source bytes.

### Step 9: Closed-Loop Iteration

When a new consumer boundary fails, return to Step 1 for that specific delta.

## Artifacts and Verification Gates

- Hand-composed known-good specimen and obstacle log.
- Run-x3 byte-parity receipt and regression test suite with mutation verification.

## Hard Boundaries

- Never treat a green unit test suite as proof that the output works at an untested real consumer.
- Never normalize away non-deterministic byte drift across the triple run.
