---
title: Patchwork-OS Canonical Skill Skeleton Procedures
layer: skills
license: MIT
---

# Patchwork-OS Canonical Skill Skeleton Procedures (`skills/`)

This directory contains the 10 generalized, host-agnostic, runtime-agnostic Markdown skeleton procedures (`SKILL.md`) that govern epistemic inquiry, requirement extraction, adversarial design smelting, root-cause debugging, empirical TDD/STDD build order, `MPT:N` orchestration, and 4-stage FRR reverse engineering.

| Skill ID | Tier | Category | Canonical Skeleton Procedure |
| :--- | :--- | :--- | :--- |
| `grilling` | `tier-1-epistemic-gate` | `discovery-and-alignment` | [grilling/SKILL.md](grilling/SKILL.md) |
| `quarry` | `tier-1-epistemic-gate` | `requirement-extraction` | [quarry/SKILL.md](quarry/SKILL.md) |
| `deconstruct` | `tier-1-epistemic-gate` | `epistemic-analysis` | [deconstruct/SKILL.md](deconstruct/SKILL.md) |
| `crucible` | `tier-2-methodology-shim` | `adversarial-hardening` | [crucible/SKILL.md](crucible/SKILL.md) |
| `systematic-debugging` | `tier-2-methodology-shim` | `debugging-and-remediation` | [systematic-debugging/SKILL.md](systematic-debugging/SKILL.md) |
| `tdd` | `tier-2-methodology-shim` | `build-discipline` | [tdd/SKILL.md](tdd/SKILL.md) |
| `stdd` | `tier-3-high-order-lifecycle` | `autonomous-lifecycle` | [stdd/SKILL.md](stdd/SKILL.md) |
| `fable-mode` | `tier-2-methodology-shim` | `governance-and-verification` | [fable-mode/SKILL.md](fable-mode/SKILL.md) |
| `wfc` | `tier-3-high-order-lifecycle` | `orchestration-and-synthesis` | [wfc/SKILL.md](wfc/SKILL.md) |
| `rea` | `tier-2-methodology-shim` | `reverse-engineering-and-roundtrip` | [rea/SKILL.md](rea/SKILL.md) |

## End-to-End Cognitive Pipeline Flow

1. **Discovery & Extraction**: [grilling](grilling/SKILL.md) -> [quarry](quarry/SKILL.md) -> [deconstruct](deconstruct/SKILL.md)
2. **Adversarial Design Smelting**: [crucible](crucible/SKILL.md) (`Charge -> Blind Heat -> Seeded-Flaw Assay -> Fused`)
3. **Multi-Persona Orchestration**: [wfc](wfc/SKILL.md) + [fable-mode](fable-mode/SKILL.md) (`MPT:N` 5-Wave role-disjoint pipeline)
4. **Implementation & Remediation**: [stdd](stdd/SKILL.md) -> [tdd](tdd/SKILL.md) / [systematic-debugging](systematic-debugging/SKILL.md)
5. **Round-Trip Verification**: [rea](rea/SKILL.md) (`Forward -> Reverse -> Round-Trip` byte-parity gate)
