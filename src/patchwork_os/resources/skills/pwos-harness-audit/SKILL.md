---
name: pwos-harness-audit
alias: harness-audit
description: "Use when auditing Hop-0 startup instruction budgets (preventing open-write-path-closed-exit), deduplicating hook event storms within a 1.5s window, or compiling prose rules into SHA-256-pinned adversarial harness contracts."
category: governance-and-harness-verification
tier: tier-0-deterministic-gate
paradigms:
  - meta-prompting
  - workflow
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Instruction Budget Guard and Adversarial Harness Audit Skeleton Procedure

## Overview

Uses the local helpers in `src/patchwork_os/harness_audit.py` to measure startup instruction budgets, detect repeated hook events, and compile governance rules into hash-pinned adversarial test contracts. This skeleton procedure does not install hooks or establish runtime enforcement.

## Invariants

1. Hop-0 Instruction Budget Cap: Audit total startup instruction characters via `audit_hop0_instruction_budget` (default cap `150,000` chars) before admitting new permanent Hop-0 rules.
2. Hook Storm Deduplication: Filter incoming hook events through `should_deduplicate_hook_event` (`1.5s` window) so case-duplicate workspace mounts never multiply subprocess invocations.
3. Canonical SHA-256 Harness Pinning: Every compiled harness contract (`compile_adversarial_harness_contract`) must bind `target_id` to `sha256:` plus the SHA-256 of canonical compact JSON for the target object with `target_id` omitted.
4. Cross-Runtime Harness Execution: A harness compiled by a Composer session must be verifiable by an independent Validator session.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Hop-0 Instruction Budget Audit

Measure character counts across root instruction files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `rules/*.md`) and run `audit_hop0_instruction_budget`.

### Stage 2: Hook Event Storm Deduplication Check

Verify that hook bootstrap entrypoints apply `should_deduplicate_hook_event` with a `1.5s` deduplication window.

### Stage 3: Adversarial Case Design

Construct positive, negative, and boundary test cases that attempt to falsify the target governance rule.

### Stage 4: Canonical Harness Compilation and Verification

Compile the target specification and adversarial cases via `compile_adversarial_harness_contract` and verify `target_id` integrity at Tier 0.

## Artifacts and Verification Gates

- Hop-0 budget audit report (`within_budget`, `total_chars`, `top_offenders`).
- Compiled `harness.json` with verified `target_id` SHA-256 digest.

## Hard Boundaries

- Never admit unbounded whole-file imports into Hop-0 when `within_budget` is false.
- Never treat a stale harness whose `target_id` does not match canonical compact JSON SHA-256 as binding.
