---
name: pwos-runtime-dispatch
alias: runtime-dispatch
description: "Use when routing or dispatching work across heterogeneous agent runtimes (cc, codex, agy, muse, aws_kiro, github_copilot, custom_cli) and compliance regimes (Commercial, GitHub Enterprise, ITAR/EAR AWS Bedrock GovCloud, ITAR/EAR GCP Vertex AI, Air-Gapped) with Inter-Runtime Synthesis."
category: cross-runtime-orchestration
tier: tier-1-execution-gate
paradigms:
  - workflow
  - meta-prompting
  - graph-prompting
  - prompt-flow
license: MIT
---

# Generalized Compliance-Aware Inter-Runtime Dispatch Skeleton Procedure

## Overview

Generalized cross-runtime dispatcher (`runtime_dispatch.py`) superseding the Augi-specific `deploy-cli` name while retaining backward-compatible alias support. Decouples regulatory compliance regime, cloud hosting backend, runtime harness, and foundation model so organizations under ITAR/EAR (AWS Bedrock GovCloud or GCP Vertex AI Assured Workloads), GitHub Enterprise, or air-gapped environments achieve **Inter-Runtime Synthesis** (`Composer Runtime != Validator Runtime`).

## Invariants

1. Compliance-First Model and Backend Filtering: Under `itar_ear_aws_govcloud`, automatically exclude unavailable commercial-only models (`fable-5-1`, `gpt-6-astra`, `gpt-6.1-sol`, `muse-wonder-full`, `gemini-4-argon`) and route to Bedrock-compliant models (`opus`, `sonnet`, `amazon-nova-2.0`, `muse-spark-open`, `mistral-large-4`, `llama-4`). Under `itar_ear_gcp_vertex`, route to Vertex-compliant `gemini-4-argon-high`, `gemini-3.8-flash-high`, and Vertex Partner `opus`/`sonnet`.
2. Inter-Runtime Synthesis Over Shared Models: Even when two seats run the same underlying model on a restricted cloud (e.g., Bedrock Claude Opus/Sonnet), pair distinct runtime harnesses (such as `cc` + `aws_kiro` on Bedrock, or `agy` + `cc` on Vertex, or `github_copilot` + `codex` on GitHub Enterprise) to combine orthogonal harness strengths.
3. Three-Layer CLI Config Precedence: Resolve all routing and dispatch parameters through `config.json` -> `input.json` -> `--set key=value` / manual CLI flags.
4. Parent-Child Lease Isolation: Enforce `verify_parent_child_lease_isolation` and `verify_inter_cli_completion_contract` on every dispatched leg.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Load 3-Layer Configuration and Compliance Regime

Invoke `resolve_extensible_compliance_routing` with `config_json`, `input_json`, `manual_set_pairs`, and `manual_kwargs` to determine active compliance boundaries and enabled runtime harnesses.

### Stage 2: Select Rank-1 Composer and Rank-2 Counterpart Runtimes

Map `{session_tier, task_category, complexity, urgency, importance}` against the VLA-benchmarked 272-model leaderboard catalog to select orthogonal Rank-1 and Rank-2 `{backend, runtime, model, effort}` tuples.

### Stage 3: Compile Inter-Runtime Synthesis Plan

Run `plan_inter_runtime_synthesis` to bind `L1-COMPOSE` (`COMPOSER`) and `L2-VALIDATE` (`VALIDATOR`) across distinct runtime harnesses (`cross_runtime_diverse: True`) with unique child session IDs.

### Stage 4: Execute Windowless Cross-Runtime Dispatch

Launch child runtime legs with UTF-8 I/O, `first_prompt_sha256` pinning, and isolated child lease tokens.

### Stage 5: Verify Completion Contract and Absorb Receipts

Validate child exit code, prompt digest match, and non-empty artifact emission via `verify_inter_cli_completion_contract`.

## Artifacts and Verification Gates

- `inter-runtime-synthesis-plan.json` recording `compliance_regime`, `legs`, and `inter_runtime_synthesis`.
- Child completion receipts verified at Tier 0.

## Hard Boundaries

- Never route ITAR/EAR workloads to unapproved public consumer endpoints.
- Never assign the same runtime session to validate its own unreviewed composition when a counterpart runtime harness is available.
