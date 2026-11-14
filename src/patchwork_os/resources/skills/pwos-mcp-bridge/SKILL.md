---
name: pwos-mcp-bridge
alias: mcp-bridge
description: "Use when bridging MCP servers into zero-daemon 3-tier progressive CLI subcommands (list-tools -> describe-tool -> call-tool) with readOnlyHint mutation gating and SHA-256 call receipts."
category: tool-bridge-and-context-efficiency
tier: tier-0-progressive-bridge
paradigms:
  - graph-prompting
  - workflow
  - prompt-flow
  - meta-prompting
license: Apache-2.0
---

# Progressive MCP-to-CLI Printing-Press Bridge Skeleton Procedure

## Overview

Generalizes Upstream-Agentic-OS's `mcp_cli_printing_press.py` and Hermes-Agent 3-tier progressive disclosure into `mcp_printing_press.py`. Replaces memory-heavy persistent MCP daemons and 10,000-token startup schema dumps with on-demand Tier-0/1/2 CLI discovery and deterministic mutation gating.

## Invariants

1. Zero Idle Daemon Overhead: Invoke MCP surfaces on demand rather than keeping duplicate Node.js/Python daemons resident in virtual commit memory (`WinError 1455` prevention).
2. Three-Tier Progressive Disclosure: Expose compact ~20-token tool summaries at Tier 0 (`project_mcp_tools_tier0`), hydrate full JSON schemas only for selected tools at Tier 1 (`describe_mcp_tool_tier1`), and execute gated calls at Tier 2 (`gate_mcp_tool_call_tier2`).
3. Read-Only Default Safety Gate: Block any MCP tool where `readOnlyHint` is false unless `allow_mutation=True` (`--allow-mutation`) is explicitly supplied.
4. Cryptographic Call Provenance: Emit a deterministic `call_sha256` receipt for every allowed Tier-2 tool invocation.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Tier-0 Compact Tool Listing

Call `project_mcp_tools_tier0` to list tool names, `read_only` flags, and 1-line descriptions without loading full parameter schemas.

### Stage 2: Tier-1 On-Demand Schema Hydration

Call `describe_mcp_tool_tier1` only for the specific tool required by the current task step.

### Stage 3: Tier-2 Mutation Gate Evaluation

Pass the tool specification and arguments to `gate_mcp_tool_call_tier2` to enforce `readOnlyHint` safety before execution.

### Stage 4: Ephemeral Execution and Receipt Recording

Execute the allowed tool call and persist the returned `call_sha256` provenance receipt.

## Artifacts and Verification Gates

- Tier-0 tool index and Tier-1 hydrated tool schema JSON.
- Tier-2 `call_sha256` execution receipt or `MUTATING_MCP_TOOL_BLOCKED_WITHOUT_ALLOW_MUTATION` refusal.

## Hard Boundaries

- Never dump raw multi-thousand-token MCP tool schemas into Hop-0 startup instructions.
- Never execute a mutating MCP tool without explicit `allow_mutation=True` authorization.
