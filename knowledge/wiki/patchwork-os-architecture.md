---
title: Patchwork-OS 5-Pillar Hybrid Architecture
layer: wiki
updated: 2026-10-19
---

# Wiki Layer: 5-Pillar Hybrid Architecture

Synthesized from [raw/source-manifest.md](../raw/source-manifest.md) and governed by [rules/patchwork-os-contract.md](../rules/patchwork-os-contract.md).

```mermaid
flowchart TD
  P1["P1: Workflow (rea + Trail-Code)"] --> P2["P2: Meta-Prompting (agent-os)"]
  P2 --> P3["P3: Graph-Prompting (graft + cmds)"]
  P3 --> P4["P4: Prompt-Flow (AIS-OS)"]
  P4 --> P5["P5: Lazy Hydration (unlazy)"]
```

## 1. Pillar 1 — Workflow Engine (`morluto/rea` + `trailhq/Trail-Code`)
Combines immutable event-sourced execution logs with isolated git worktree hooks. Counterpart wave-DAG scheduling prevents cyclic retries.

## 2. Pillar 2 — Meta-Prompting (`NousResearch/hermes-agent` + `buildermethods/agent-os` + `mattpocock/skills`)
Unites Builder Methods' original open-source `buildermethods/agent-os` specification standards with Hermes skill evolution and Wayfinder deterministic CLI wrappers.

## 3. Pillar 3 — Graph-Prompting (`graft` + `johnfkoo951/cmds-llm-wiki` + `johnfkoo951/cmds-share`)
Pairs AST code-graph navigation (`skeleton`, `callers`) with the 3-layer CMDS knowledge hierarchy (`raw/`, `wiki/`, `rules/`).

## 4. Pillar 4 — Prompt-Flow (`nateherkai/AIS-OS`)
Enforces strict role separation (`Composer != Validator != Synthesizer`) across multi-agent verification pipelines.

## 5. Pillar 5 — Lazy Context Hydration (`Leonxlnx/unlazy`)
Loads compact hub indices and AST skeletons first, hydrating full document or code bodies only when required by the active task contract.
