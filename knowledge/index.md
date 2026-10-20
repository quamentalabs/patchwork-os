---
title: Patchwork-OS 3-Layer Knowledge Hub
category: architecture
tags: [patchwork-os, workflow, meta-prompting, graph-prompting, prompt-flow, cmds-llm-wiki]
updated: 2026-10-19
---

# Patchwork-OS Knowledge Hub (`index.md`)

This hub routes agents across the 3-layer CMDS knowledge architecture using lazy pointer hydration (`Leonxlnx/unlazy` pattern). Read this index first and hydrate individual spokes only on demand.

```mermaid
flowchart TD
  IDX["index.md (Hub Router)"] --> RAW["raw/source-manifest.md"]
  IDX --> WIKI["wiki/patchwork-os-architecture.md"]
  IDX --> RULES["rules/patchwork-os-contract.md"]
```

## Spoke Directory

- **Raw Layer (Immutable Source Manifest)**: [[raw/source-manifest.md]]
- **Wiki Layer (5-Pillar Hybrid Synthesis)**: [[wiki/patchwork-os-architecture.md]]
- **Rules Layer (Deterministic Contracts & Hygiene Gates)**: [[rules/patchwork-os-contract.md]]
