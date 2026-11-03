---
title: Patchwork-OS Canonical Skill Skeleton Procedures
layer: skills
namespace_prefix: pwos-
license: Apache-2.0
---

# Patchwork-OS Canonical Skill Skeleton Procedures (skills/pwos-*)

This directory contains the 18 generalized, host-agnostic, runtime-agnostic Markdown skeleton procedures (SKILL.md) under the default pwos-* namespace (which can be dynamically re-prefixed to `<custom-prefix>-*` or unprefixed during [pwos-setup](pwos-setup/SKILL.md)). Each procedure governs agnostic initialization/rebranding, epistemic inquiry, requirement extraction, starter-boost-kit persona setup, adversarial design smelting, root-cause debugging, empirical TDD/STDD build order, MPT:N orchestration, compliance-aware inter-runtime dispatch, session continuity, progressive MCP-to-CLI bridging, browser VLA verification, instruction-budget harness auditing, and 4-stage FRR reverse engineering.

| Canonical Skill ID | Short Alias | Tier | Category | Canonical Skeleton Procedure |
| :--- | :--- | :--- | :--- | :--- |
| pwos-setup | setup | tier-0-bootstrap-gate | initialization-and-rebranding | [pwos-setup/SKILL.md](pwos-setup/SKILL.md) |
| pwos-grilling | grilling | tier-1-epistemic-gate | discovery-and-alignment | [pwos-grilling/SKILL.md](pwos-grilling/SKILL.md) |
| pwos-quarry | quarry | tier-1-epistemic-gate | requirement-extraction | [pwos-quarry/SKILL.md](pwos-quarry/SKILL.md) |
| pwos-deconstruct | deconstruct | tier-1-epistemic-gate | epistemic-analysis | [pwos-deconstruct/SKILL.md](pwos-deconstruct/SKILL.md) |
| pwos-persona-agent | persona-agent | tier-1-epistemic-gate | agent-setup-and-elicitation | [pwos-persona-agent/SKILL.md](pwos-persona-agent/SKILL.md) |
| pwos-crucible | crucible | tier-2-methodology-shim | adversarial-hardening | [pwos-crucible/SKILL.md](pwos-crucible/SKILL.md) |
| pwos-systematic-debugging | systematic-debugging | tier-2-methodology-shim | debugging-and-remediation | [pwos-systematic-debugging/SKILL.md](pwos-systematic-debugging/SKILL.md) |
| pwos-tdd | tdd | tier-2-methodology-shim | build-discipline | [pwos-tdd/SKILL.md](pwos-tdd/SKILL.md) |
| pwos-stdd | stdd | tier-3-high-order-lifecycle | autonomous-lifecycle | [pwos-stdd/SKILL.md](pwos-stdd/SKILL.md) |
| pwos-fable-mode | fable-mode | tier-2-methodology-shim | governance-and-verification | [pwos-fable-mode/SKILL.md](pwos-fable-mode/SKILL.md) |
| pwos-wfc | wfc | tier-3-high-order-lifecycle | orchestration-and-synthesis | [pwos-wfc/SKILL.md](pwos-wfc/SKILL.md) |
| pwos-runtime-dispatch | runtime-dispatch | tier-1-execution-gate | cross-runtime-orchestration | [pwos-runtime-dispatch/SKILL.md](pwos-runtime-dispatch/SKILL.md) |
| pwos-deploy-cli | deploy-cli | tier-3-high-order-lifecycle | cross-runtime-dispatch | [pwos-deploy-cli/SKILL.md](pwos-deploy-cli/SKILL.md) |
| pwos-session-lifecycle | session-lifecycle | tier-1-lifecycle-gate | session-continuity-and-messaging | [pwos-session-lifecycle/SKILL.md](pwos-session-lifecycle/SKILL.md) |
| pwos-mcp-bridge | mcp-bridge | tier-0-progressive-bridge | tool-bridge-and-context-efficiency | [pwos-mcp-bridge/SKILL.md](pwos-mcp-bridge/SKILL.md) |
| pwos-browser-vla | browser-vla | tier-1-visual-gate | browser-vla-and-visual-verification | [pwos-browser-vla/SKILL.md](pwos-browser-vla/SKILL.md) |
| pwos-harness-audit | harness-audit | tier-0-deterministic-gate | governance-and-harness-verification | [pwos-harness-audit/SKILL.md](pwos-harness-audit/SKILL.md) |
| pwos-rea | rea | tier-2-methodology-shim | reverse-engineering-and-roundtrip | [pwos-rea/SKILL.md](pwos-rea/SKILL.md) |

## End-to-End Cognitive Pipeline Flow

1. **Initialization, Discovery & Persona Setup**: [pwos-setup](pwos-setup/SKILL.md) -> [pwos-grilling](pwos-grilling/SKILL.md) -> [pwos-quarry](pwos-quarry/SKILL.md) -> [pwos-deconstruct](pwos-deconstruct/SKILL.md) -> [pwos-persona-agent](pwos-persona-agent/SKILL.md)
2. **Adversarial Design Smelting & Harness Audit**: [pwos-crucible](pwos-crucible/SKILL.md) + [pwos-harness-audit](pwos-harness-audit/SKILL.md)
3. **Multi-Persona Orchestration & Compliance-Aware Inter-Runtime Dispatch**: [pwos-wfc](pwos-wfc/SKILL.md) + [pwos-runtime-dispatch](pwos-runtime-dispatch/SKILL.md) ([pwos-deploy-cli](pwos-deploy-cli/SKILL.md)) + [pwos-fable-mode](pwos-fable-mode/SKILL.md)
4. **Implementation, Progressive MCP Bridge & Browser VLA**: [pwos-stdd](pwos-stdd/SKILL.md) -> [pwos-tdd](pwos-tdd/SKILL.md) / [pwos-systematic-debugging](pwos-systematic-debugging/SKILL.md) + [pwos-mcp-bridge](pwos-mcp-bridge/SKILL.md) + [pwos-browser-vla](pwos-browser-vla/SKILL.md)
5. **Session Continuity & Round-Trip Verification**: [pwos-session-lifecycle](pwos-session-lifecycle/SKILL.md) + [pwos-rea](pwos-rea/SKILL.md)
