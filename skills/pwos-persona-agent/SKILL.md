---
name: pwos-persona-agent
alias: persona-agent
description: "Use when bootstrapping, customizing, or selecting generalized SME and functional persona agents via brainstorming skills (grilling, quarry, deconstruct, crucible) tailored to organization, team, individual, task characteristics, expertise, personality, and background."
category: agent-setup-and-elicitation
tier: tier-1-epistemic-gate
paradigms:
  - meta-prompting
  - workflow
  - graph-prompting
  - prompt-flow
license: Apache-2.0
---

# Persona-Agent Starter-Boost-Kit Skeleton Procedure

## Overview

Generalized Starter-Boost-Kit for eliciting, synthesizing, and binding SME and functional persona agents in Patchwork-OS. Through interactive brainstorming skills ([pwos-grilling](../pwos-grilling/SKILL.md), [pwos-quarry](../pwos-quarry/SKILL.md), [pwos-deconstruct](../pwos-deconstruct/SKILL.md), and [pwos-crucible](../pwos-crucible/SKILL.md)), this procedure captures high-alignment context across organization, team, individual, task characteristics, domain expertise, personality/voice, background/lineage, and open-ended custom facets, then compiles role-disjoint agent definitions and model-tier bindings.

## Invariants

1. Brainstorming-Driven Elicitation: Never freeze a static one-size-fits-all persona roster when domain context is unprobed; elicit alignment facets through `pwos-grilling`, `pwos-quarry`, `pwos-deconstruct`, and `pwos-crucible` before binding seats.
2. Multi-Facet Alignment Coverage (Open-Ended): Every synthesized persona profile must bind organization/company context, team topology, individual working style, task characteristics, SME domain expertise (plus explicit exclusions), personality/voice stance, background/lineage, and extensible `custom_facets`.
3. Four-Way Role Orthogonality: Every persona seat maps to exactly one cognitive role tier (`composer`, `validator`, `synthesizer`, or `meta_evaluator`) with explicit counterpart pairing.
4. Dual-Axis Model and Effort Binding: Bind planning/reasoning/synthesis seats to frontier reasoning models and execution/validation/coding seats to low-hallucination agentic execution models.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Brainstorming Elicitation (Grilling, Quarry, Deconstruct)

Run [pwos-grilling](../pwos-grilling/SKILL.md) and [pwos-quarry](../pwos-quarry/SKILL.md) to extract organization rules, team workflows, individual preferences, task complexity/urgency/importance, required SME specialties, and desired persona voice/background, then classify KK/KU/UK/UU via [pwos-deconstruct](../pwos-deconstruct/SKILL.md).

### Stage 2: Multi-Facet Persona Profile Synthesis

Compile a `PersonaAlignmentProfile` combining starter archetype slots with the elicited facets (organization, team, individual, task, expertise, personality, background, and arbitrary `custom_facets`), including explicit `does_not_include` anti-scope boundaries.

### Stage 3: Crucible Adversarial Assay of Persona Boundaries

Stress-test the candidate persona roster via [pwos-crucible](../pwos-crucible/SKILL.md) to eliminate role overlap (`Composer != Validator != Synthesizer != Meta-Evaluator`) and verify that every primary composer seat has an adversarial counterpart covering its blind spots.

### Stage 4: Agent Markdown and Seat-Model-Tier Emission

Render portable `.agents/agents/<persona-slug>.md` files and update `seat-model-tier.json` (`fable_roles`, `opus_roles`, `sonnet_roles`) plus WFC/MPT routing bindings.

### Stage 5: Round-Trip Verification and Hub-Spoke Registration

Validate the generated persona files and roster bindings at Tier 0 (0 LLM tokens) and register the resulting roster in the CMDS `wiki/` and `rules/` layers.

## Artifacts and Verification Gates

- `.agents/agents/<persona-slug>.md` and `persona-alignment-profile.json`.
- `seat-model-tier.json` and `vla-wfc-mpt-hub-spoke-map.json` with verified 4-way role disjointness.

## Hard Boundaries

- Never limit persona setup to fixed fields; always preserve extensible `custom_facets` for domain-specific or user-specific dimensions.
- Never assign the same persona to both compose and validate the same artifact.
