---
name: pwos-role-catalog
alias: role-catalog
description: "Use when defining persistent role identities distinct from task, runtime, model, effort, and authority."
category: roles-and-identity
tier: tier-2-methodology-shim
paradigms:
  - workflow
license: Apache-2.0
---

# Role Catalog

## Overview

A role is a persistent, versioned definition of responsibility and authority
scope. Roles are edited and versioned like code. No runtime, model, or task
instance is baked into a role definition.

## Invariants

1. Role identity survives runtime, model, and effort changes.
2. Every edit creates a new version; history is preserved.
3. Role definitions stay generic; diaries and private notes stay out.
4. Authority is expressed as scope, never as assumed privilege.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Role Definition

Describe responsibility, scope, and escalation paths in generic terms.

### Stage 2: Versioning

Publish each change as a new version with rationale.

### Stage 3: Cross-Linking

Link the role to scoped memory, procedures, decisions, and patterns.

### Stage 4: Binding

Bind a live seat to one role version for a bounded assignment.

### Stage 5: Review

Retire or revise roles whose assignments no longer match scope.

## Artifacts and Verification Gates

- Role registry with versions, links, and binding receipts.
- Oracle: a binding resolves to exactly one role version.

## Hard Boundaries

- Never export private persona biographies.
- Never bind a role beyond its declared authority scope.

## Related

- Architecture: [portable-agent-infrastructure](../../docs/architecture/portable-agent-infrastructure.md)
- memory-hub: [pwos-memory-hub](../pwos-memory-hub/SKILL.md)
- baseline persona-agent: [pwos-persona-agent](../pwos-persona-agent/SKILL.md)
