---
name: pwos-skill-authoring
alias: skill-authoring
description: "Use when creating or upgrading a skill with frontmatter schema, ordered stages, and mirror packaging."
category: skills-and-packages
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Skill Authoring

## Overview

Creates a portable skill document that validates against the public schema,
mirrors byte-identically into the packaged resources, and states its
acceptance oracle plainly. The same file serves readers and validators.

## Invariants

1. Frontmatter carries name, description, and license metadata.
2. Ordered stages are at least four and each is actionable.
3. The packaged mirror is byte-identical to the source.
4. The oracle is executable or directly checkable, never rhetorical.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Capability Scoping

Name the capability and its explicit boundaries.

### Stage 2: Schema Draft

Write frontmatter and the five required sections.

### Stage 3: Stage Authorship

Draft at least four ordered stages with distinct inputs and outputs.

### Stage 4: Oracle and Mirror

Run the validator and copy the mirror byte-identically.

### Stage 5: Manifest Entry

Record paths, hashes, and coverage for the integrator.

## Artifacts and Verification Gates

- Validation receipt with schema result and mirror hash.
- Oracle: the validator reports the skill as valid.

## Hard Boundaries

- Never reuse boilerplate across skills.
- Never ship a mirror that differs from its source.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- workflow-router: [pwos-workflow-router](../pwos-workflow-router/SKILL.md)
