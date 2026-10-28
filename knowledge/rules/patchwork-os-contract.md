---
title: Patchwork-OS Operational & Hygiene Contract
layer: rules
updated: 2026-10-24
---

# Rules Layer: Deterministic Governance & Hygiene Contract

This rules layer records intended design requirements, as do the architecture and skill documents linked from the index. Text here does not prove native enforcement, live delegation, model calls or authentication. APIs require explicit invocation; the local evaluation is only the README plan example.

1. **Four Mandatory Paradigms**: Every non-trivial workflow combines `workflow`, `meta-prompting`, `graph-prompting`, and `prompt-flow`.
2. **Five-Role Orthogonal Separation & Session Hierarchy Routing**:
   - Intended role separation: `Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator` across the named cognitive stages; a declaration is not an independently observed deployment.
   - Route Rank-1 and Rank-2 `{runtime, model, effort}` deterministically across `{main_hub, main_spoke_sub_hub} x {task_category, complexity, urgency, importance}` via `resolve_orchestrator_session_routing`.
   - Intended task records include a MAC-bound `lease_token`, `KK/KU/UK/UU`, `3xPR` and `FRR`. Generation and verification require an explicit caller-managed secret; missing/empty/public-default secrets are refused. The retained 16-hex tag and template checks do not implement key management, replay prevention, authorization or company approval.
3. **Generalized Persona Starter-Boost-Kit & Cross-Runtime Inter-CLI Dispatch**:
   - Synthesize bespoke SME and functional personas via `pwos-persona-agent` (`persona_setup.py`) using brainstorming elicitation (`pwos-grilling`, `pwos-quarry`, `pwos-deconstruct`, `pwos-crucible`) across organization, team, individual, task characteristics, expertise/exclusions, voice, lineage, and custom facets.
   - Intended delegation spans those runtime labels. `deploy_cli.py` provides plans and supplied path/hash/status checks only; live launch, lease acquisition and independent receipt acceptance are not implemented by that planner.
4. **Three-Layer CMDS & EARS Spec Separation**:
   - `raw/` stores immutable source manifests.
   - `wiki/` stores synthesized architectural nodes linked via standard POSIX Markdown links (`[label](path.md)`).
   - `rules/` stores intended invariants, including EARS specification validation (`WHEN/IF ... THE SYSTEM SHALL ...`); automatic Tier-0 enforcement is not established by storing this file.
5. **Three-Tier OS-Agnostic Hub-Spoke Projection**:
   - Bind `.agent-hub/` SSoT spokes via `SYMLINK -> NTFS_JUNCTION/HARDLINK -> ATOMIC_COPY_FALLBACK` with junction-safe unlinking (never recursively deleting link targets) and windowless execution.
6. **Zero Credential or Internal Host Leak & Compact Visual Diagrams**:
   - Satellite and blueprint files must pass `validate_patchwork_satellite` with zero live tokens, API keys, or internal hostnames, and every Mermaid line must remain `<= 79` characters.
7. **Two-Stage Deterministic AST + Zero-Thinking Escalation Ladder**:
   - Intended order: local AST/lint checks, then separately implemented model escalation for ambiguous cases. Routing data or this rule does not execute a local LLM or authorize data transmission.
