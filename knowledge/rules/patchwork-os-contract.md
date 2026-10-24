---
title: Patchwork-OS Operational & Hygiene Contract
layer: rules
updated: 2026-10-24
---

# Rules Layer: Deterministic Governance & Hygiene Contract

1. **Four Mandatory Paradigms**: Every non-trivial workflow combines `workflow`, `meta-prompting`, `graph-prompting`, and `prompt-flow`.
2. **Five-Role Orthogonal Separation & Session Hierarchy Routing**:
   - Enforce `Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator` across `planning`, `reasoning`, `adversarial_triage`, `synthesizing`, `meta_evaluating`, and `orchestrating`.
   - Route Rank-1 and Rank-2 `{runtime, model, effort}` deterministically across `{main_hub, main_spoke_sub_hub} x {task_category, complexity, urgency, importance}` via `resolve_orchestrator_session_routing`.
   - Every task contract requires a verified HMAC-SHA256 `lease_token`, `KK/KU/UK/UU` epistemic classification, `3xPR` progressive review gates, and `FRR` regression records.
3. **Generalized Persona Starter-Boost-Kit & Cross-Runtime Inter-CLI Dispatch**:
   - Synthesize bespoke SME and functional personas via `pwos-persona-agent` (`persona_setup.py`) using brainstorming elicitation (`pwos-grilling`, `pwos-quarry`, `pwos-deconstruct`, `pwos-crucible`) across organization, team, individual, task characteristics, expertise/exclusions, voice, lineage, and custom facets.
   - Delegate across `cc`, `codex`, `agy`, and `muse` via `pwos-deploy-cli` (`deploy_cli.py`) with parent/child lease isolation (`verify_parent_child_lease_isolation`) and completion receipts (`verify_inter_cli_completion_contract`).
4. **Three-Layer CMDS & EARS Spec Separation**:
   - `raw/` stores immutable source manifests.
   - `wiki/` stores synthesized architectural nodes linked via standard POSIX Markdown links (`[label](path.md)`).
   - `rules/` stores deterministic invariants enforced at Tier 0, including EARS specification validation (`WHEN/IF ... THE SYSTEM SHALL ...`).
5. **Three-Tier OS-Agnostic Hub-Spoke Projection**:
   - Bind `.agent-hub/` SSoT spokes via `SYMLINK -> NTFS_JUNCTION/HARDLINK -> ATOMIC_COPY_FALLBACK` with junction-safe unlinking (never recursively deleting link targets) and windowless execution.
6. **Zero Credential or Internal Host Leak & Compact Visual Diagrams**:
   - Satellite and blueprint files must pass `validate_patchwork_satellite` with zero live tokens, API keys, or internal hostnames, and every Mermaid line must remain `<= 79` characters.
7. **Two-Stage Deterministic AST + Zero-Thinking Escalation Ladder**:
   - Execute Stage-1 deterministic AST/Lint validation first (`0` tokens, blocking `SyntaxError` and bare `except:`), run Stage-2 local LLM (`thinking=False`, `temperature=0.0`), and escalate to Stage-3 counterpart roles only on `AMBIGUOUS`.
