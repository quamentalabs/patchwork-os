---
title: Patchwork-OS Canonical Skill Skeleton Procedures
layer: skills
namespace_prefix: pwos-
license: MIT
---

# Patchwork-OS Canonical Skill Skeleton Procedures (skills/pwos-*)

This directory contains the 10 generalized, host-agnostic, runtime-agnostic Markdown skeleton procedures (SKILL.md) under the canonical pwos-* namespace (mirroring internal ugi-* skill isolation while preventing collisions with built-in runtime skills). Each procedure governs epistemic inquiry, requirement extraction, adversarial design smelting, root-cause debugging, empirical TDD/STDD build order, MPT:N orchestration, and 4-stage FRR reverse engineering.

| Canonical Skill ID | Short Alias | Tier | Category | Canonical Skeleton Procedure |
| :--- | :--- | :--- | :--- | :--- |
| pwos-grilling | grilling | 	ier-1-epistemic-gate | discovery-and-alignment | [pwos-grilling/SKILL.md](pwos-grilling/SKILL.md) |
| pwos-quarry | quarry | 	ier-1-epistemic-gate | 
equirement-extraction | [pwos-quarry/SKILL.md](pwos-quarry/SKILL.md) |
| pwos-deconstruct | deconstruct | 	ier-1-epistemic-gate | epistemic-analysis | [pwos-deconstruct/SKILL.md](pwos-deconstruct/SKILL.md) |
| pwos-crucible | crucible | 	ier-2-methodology-shim | dversarial-hardening | [pwos-crucible/SKILL.md](pwos-crucible/SKILL.md) |
| pwos-systematic-debugging | systematic-debugging | 	ier-2-methodology-shim | debugging-and-remediation | [pwos-systematic-debugging/SKILL.md](pwos-systematic-debugging/SKILL.md) |
| pwos-tdd | 	dd | 	ier-2-methodology-shim | uild-discipline | [pwos-tdd/SKILL.md](pwos-tdd/SKILL.md) |
| pwos-stdd | stdd | 	ier-3-high-order-lifecycle | utonomous-lifecycle | [pwos-stdd/SKILL.md](pwos-stdd/SKILL.md) |
| pwos-fable-mode | able-mode | 	ier-2-methodology-shim | governance-and-verification | [pwos-fable-mode/SKILL.md](pwos-fable-mode/SKILL.md) |
| pwos-wfc | wfc | 	ier-3-high-order-lifecycle | orchestration-and-synthesis | [pwos-wfc/SKILL.md](pwos-wfc/SKILL.md) |
| pwos-rea | 
ea | 	ier-2-methodology-shim | 
everse-engineering-and-roundtrip | [pwos-rea/SKILL.md](pwos-rea/SKILL.md) |

## End-to-End Cognitive Pipeline Flow

1. **Discovery & Extraction**: [pwos-grilling](pwos-grilling/SKILL.md) -> [pwos-quarry](pwos-quarry/SKILL.md) -> [pwos-deconstruct](pwos-deconstruct/SKILL.md)
2. **Adversarial Design Smelting**: [pwos-crucible](pwos-crucible/SKILL.md) (Charge -> Blind Heat -> Seeded-Flaw Assay -> Fused)
3. **Multi-Persona Orchestration**: [pwos-wfc](pwos-wfc/SKILL.md) + [pwos-fable-mode](pwos-fable-mode/SKILL.md) (MPT:N 5-Wave role-disjoint pipeline)
4. **Implementation & Remediation**: [pwos-stdd](pwos-stdd/SKILL.md) -> [pwos-tdd](pwos-tdd/SKILL.md) / [pwos-systematic-debugging](pwos-systematic-debugging/SKILL.md)
5. **Round-Trip Verification**: [pwos-rea](pwos-rea/SKILL.md) (Forward -> Reverse -> Round-Trip byte-parity gate)
