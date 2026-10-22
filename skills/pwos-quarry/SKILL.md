---
name: pwos-quarry
alias: quarry
description: "Use when a plan, design, or requirement exists only in the operator's head and must be extracted to disk one question at a time before adversarial hardening in crucible."
category: requirement-extraction
tier: tier-1-epistemic-gate
paradigms:
  - workflow
  - prompt-flow
license: MIT
---

# Quarry Skeleton Procedure

## Overview

Durable pre-crucible extraction procedure that converts tacit operator intent into an immutable, disk-backed capture file before any design melting or code generation occurs.

## Invariants

1. Capture Is the Deliverable: Every operator answer must be written to disk before the next question is asked.
2. Resume Existing Captures First: Always check `.scratch/quarry/<YYYY-MM-DD>-<slug>.md` before starting; never restart an interview the operator already sat through.
3. Read Supplied Inputs First: Read all provided documents, links, or prior plans before asking anything; ask only net-new questions.
4. Canonical Capture Path: Store raw captures in `.scratch/quarry/` using normalized paths and keep raw captures separate from polished specs.
5. Recommended Answer per Cut: Each single-question cut carries a recommended default and options bounded by concise labels.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Existing Capture and Input Audit

Check `.scratch/quarry/` for an active capture on the topic and read all operator-supplied materials to eliminate redundant questions.

### Stage 2: Capture Skeleton Initialization

Create `.scratch/quarry/<YYYY-MM-DD>-<slug>.md` with subject, date, one-line goal, and empty section slots, then report its path in one line.

### Stage 3: Net-New Question Cut

Ask one structured question with a recommended answer covering the highest-leverage unsettled requirement.

### Stage 4: Immediate Disk Persistence

Append the operator's exact answer and updated frontier to the capture file on disk before formulating the next question.

### Stage 5: Charge Handoff to Crucible

Once all load-bearing requirements are extracted on disk, hash the capture and hand it off as the initial charge for [crucible](../pwos-crucible/SKILL.md).

## Artifacts and Verification Gates

- Durable capture markdown file at `.scratch/quarry/<YYYY-MM-DD>-<slug>.md`.
- SHA-256 digest of the completed capture ready for [crucible](../pwos-crucible/SKILL.md) Stage 1.

## Hard Boundaries

- Never hold interview answers only in conversation context without writing to disk.
- Never merge the raw quarry capture with the downstream polished plan or specification.
