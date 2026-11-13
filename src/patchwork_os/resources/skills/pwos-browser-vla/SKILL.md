---
name: pwos-browser-vla
alias: browser-vla
description: "Use when executing hybrid browser automation, Vision-Language-Action (VLA) web benchmark/UI capture (vision_before -> action -> dom + vision_after), or enforcing the <=79 column Mermaid visual width gate."
category: browser-vla-and-visual-verification
tier: tier-1-visual-gate
paradigms:
  - workflow
  - graph-prompting
  - prompt-flow
  - meta-prompting
license: MIT
---

# Hybrid Browser VLA and Visual Gate Skeleton Procedure

## Overview

Generalizes Upstream-Agentic-OS's `hybrid-browser-control`, `exec-pw-cli`, and `closed_feedback_visual_gate.py` into `browser_vla.py`. Enforces closed-loop visual + DOM verification (`vision_before_digest -> browser action -> dom_after_digest + vision_after_digest`) for web data extraction and UI validation, alongside the `<= 79` character Mermaid terminal width gate.

## Invariants

1. Closed-Loop VLA Proof: Every browser interaction or web extraction must record `vision_before_digest`, `vision_after_digest` (`vision_before != vision_after`), and `dom_after_digest` verified by `verify_vla_capture_receipt`.
2. Dropdown and Pagination Completeness: When harvesting comparison or leaderboard surfaces, probe interactive comboboxes/dropdowns and full table rows rather than relying on static initial viewport text alone.
3. Terminal Visual Width Gate: Every Mermaid diagram in Markdown artifacts and wiki nodes must pass `validate_mermaid_visual_width` (`<= 79` columns per line, no standalone node pre-declarations before edges).
4. Windowless Browser Execution: Launch headless or attached browser sessions without stealing OS keyboard focus.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Pre-Action Visual Snapshot

Capture the initial viewport screenshot and compute `vision_before_digest` (`sha256:...`).

### Stage 2: Bounded Browser Action and Interactive Probe

Navigate to the target URL, dismiss obstructing modals/banners, and interact with target controls (such as model selector comboboxes or leaderboard tables).

### Stage 3: Post-Action DOM and Viewport Slice Extraction

Extract structured DOM tables/options, capture viewport slices across the scroll height, and compute `dom_after_digest` and `vision_after_digest`.

### Stage 4: VLA Receipt and Mermaid Visual Gate Verification

Run `verify_vla_capture_receipt` on the capture receipt and `validate_mermaid_visual_width` on any generated Markdown documentation.

## Artifacts and Verification Gates

- `vla-capture-receipt.json` verified by `verify_vla_capture_receipt`.
- Viewport slice PNGs (`slices/*.png`) with SHA-256 digests and `validate_mermaid_visual_width` pass report.

## Hard Boundaries

- Never accept a web-sourced or UI-rendering claim without matching `vision_before_digest`, `vision_after_digest`, and `dom_after_digest`.
- Never emit Mermaid lines exceeding 79 characters or pre-declare standalone nodes before edges.
