---
title: Patchwork-OS Operational & Hygiene Contract
layer: rules
updated: 2026-10-19
---

# Rules Layer: Deterministic Governance & Hygiene Contract

1. **Four Mandatory Paradigms**: Every non-trivial workflow combines `workflow`, `meta-prompting`, `graph-prompting`, and `prompt-flow`.
2. **Three-Layer CMDS Separation**:
   - `raw/` stores immutable source manifests.
   - `wiki/` stores synthesized architectural nodes linked via `[[...]]`.
   - `rules/` stores deterministic invariants enforced at Tier 0.
3. **Zero Credential or Internal Host Leak**:
   - Satellite and blueprint files must pass `validate_patchwork_satellite` with zero live tokens, API keys, or internal hostnames.
4. **Compact Visual Diagrams**:
   - Every Mermaid line must remain `<= 79` characters for terminal rendering compatibility.
5. **Near-Deterministic Escalation Ladder**:
   - Execute Tier-0 deterministic CLI validation first (`0` tokens), escalate to Tier-1 local LLM (`thinking=False`) only when structural checks require semantic disambiguation, and escalate to Tier-2 frontier LLM only on `AMBIGUOUS_ESCALATE`.
