---
name: pwos-setup
alias: setup
description: "Use when initializing a repository from the starter kit (where Patchwork-OS and pwos-* are working titles), customizing OS name and skill prefix, selecting regulatory/export-control regimes (ITAR/EAR, AWS Bedrock GovCloud, GCP Vertex AI, GitHub Enterprise, Air-Gapped), or loading the 3-layer CLI config contract."
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

Runtime-agnostic initialization, rebranding, skill-prefix customization, and compliance-boundary setup procedure for the starter kit. Because `Patchwork-OS` and `pwos-*` are working titles, this skill enables any organization, team, or individual to rename the OS, customize or strip the skill prefix (`<prefix>-*`), rename `deploy-cli` to `runtime-dispatch`, and bind ITAR/EAR/GovCloud/Vertex/Bedrock/Copilot/Kiro profiles without assuming Claude Code.

## Invariants

1. Runtime-Agnostic Elicitation: Never hard-depend on a single vendor UI tool such as Claude Code `AskUserQuestion`; emit a universal questionnaire schema compatible with AGY `ask_question`, CC `AskUserQuestion`, Kiro steering, Copilot chat, terminal stdin, and non-interactive JSON files.
2. Three-Layer CLI Config Precedence: Every setup parameter supports `config.json` (Layer 1 baseline), `input.json` (Layer 2 session/task overlay), and manual keyword arguments (`--set key=value` or CLI flags, Layer 3 highest precedence).
3. Dynamic Skill-Prefix and OS Rebranding: Re-prefix all core skills to `<skill_prefix>-*` (or unprefixed canonical names) and update `config/workspace-profile.json` while preserving optional backward-compatible aliases.
4. Brainstorming-Driven Persona Bootstrapping: Chain into [pwos-persona-agent](../pwos-persona-agent/SKILL.md) to synthesize role-disjoint SME and functional personas.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Emit or Load Agnostic Questionnaire and 3-Layer Config

Run `python -m patchwork_os.setup_init --emit-questionnaire` for interactive elicitation or supply `--config-json`, `--input-json`, and `--set key=value` overrides via `load_layered_config`.

### Stage 2: Resolve Compliance Regime and Cloud/Runtime Boundaries

Select `commercial_cloud`, `github_enterprise`, `itar_ear_aws_govcloud`, `itar_ear_gcp_vertex`, `itar_ear_dual_govcloud`, or `airgapped_local` and filter active cloud backends and runtime harnesses (`cc`, `codex`, `agy`, `muse`, `aws_kiro`, `github_copilot`, `custom_cli`).

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
