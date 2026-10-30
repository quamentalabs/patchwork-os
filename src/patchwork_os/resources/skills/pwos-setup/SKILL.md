---
name: pwos-setup
alias: setup
description: "Use for starter-kit naming, prefix customization and three-layer configuration. Stored provider/regime labels are unverified examples and do not determine compliance, isolation or service availability."
category: initialization-and-rebranding
tier: tier-0-bootstrap-gate
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: MIT
---

# Agnostic Starter-Kit Setup and Rebranding Skeleton Procedure

## Overview

Starter-kit initialization, rebranding and prefix customization can store example regime/backend/runtime labels. The questionnaire and emitted profile carry `verification=unverified_example` and `compliance_assessed=False`. Names such as ITAR/EAR, GovCloud, Vertex or air-gapped are requested configuration labels, not verified provider support, isolation or company approval. Setup writes files and is outside the README plan-only evaluation sample.

## Invariants

1. Runtime-Agnostic Elicitation: Never hard-depend on a single vendor UI tool such as Claude Code `AskUserQuestion`; emit a universal questionnaire schema compatible with AGY `ask_question`, CC `AskUserQuestion`, Kiro steering, Copilot chat, terminal stdin, and non-interactive JSON files.
2. Three-Layer CLI Config Precedence: Every setup parameter supports `config.json` (Layer 1 baseline), `input.json` (Layer 2 session/task overlay), and manual keyword arguments (`--set key=value` or CLI flags, Layer 3 highest precedence).
3. Dynamic Skill-Prefix and OS Rebranding: Re-prefix all core skills to `<skill_prefix>-*` (or unprefixed canonical names) and update `config/workspace-profile.json` while preserving optional backward-compatible aliases.
4. Brainstorming-Driven Persona Bootstrapping: Chain into [pwos-persona-agent](../pwos-persona-agent/SKILL.md) to synthesize role-disjoint SME and functional personas.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Emit or Load Agnostic Questionnaire and 3-Layer Config

Run `python -m patchwork_os.setup_init --emit-questionnaire` for interactive elicitation or supply `--config-json`, `--input-json`, and `--set key=value` overrides via `load_layered_config`.

### Stage 2: Resolve Compliance Regime and Cloud/Runtime Boundaries

Store one of the existing example regime selectors and the requested backend/runtime labels. All six choices are unverified examples; selection does not configure or validate a regulatory/credential boundary or prove model access.

### Stage 3: Apply OS Rebranding and Skill-Prefix Transformation

Materialize re-prefixed skill directories under `skills/<prefix>-*` (generalizing `deploy-cli` to `runtime-dispatch` while optionally retaining `deploy-cli` alias) and rewrite display titles to the chosen `os_name`.

### Stage 4: Bootstrap Persona Starter-Boost-Kit

Invoke `bootstrap_persona_starter_kit` to generate the 5 orthogonal role personas (`COMPOSER`, `CRITICIZER`, `VALIDATOR`, `SYNTHESIZER`, `META_EVALUATOR`) and custom SME profiles.

### Stage 5: Tier-0 Verification and Workspace Profile Emission

Write `config/workspace-profile.json` with full `_config_provenance` and verify all skills via `validate_skills_directory`.

## Artifacts and Verification Gates

- `config/workspace-profile.json` with `_config_provenance` recording all applied config layers.
- Re-prefixed `skills/<prefix>-*/SKILL.md` directories and `.agents/agents/*.md` persona definitions.

## Hard Boundaries

- Never assume Claude Code is the active setup host; every step must work in `agy`, `codex`, `cc`, `muse`, `aws_kiro`, `github_copilot`, and headless CLI.
- Never overwrite user-supplied `manual_set` keyword overrides with lower-precedence `config.json` defaults.
