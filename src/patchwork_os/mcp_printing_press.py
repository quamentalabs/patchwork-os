# SPDX-License-Identifier: MIT
"""Generalized 3-Tier Progressive MCP-to-CLI Printing-Press Bridge.

Assimilates and generalizes Upstream-Agentic-OS's ``mcp_cli_printing_press.py`` and
``Hermes-Agent`` 3-tier progressive disclosure pattern:
1. **Tier 0 (`list-tools`)**: Compact ~20-token/tool index without dumping
   10,000-token JSON schemas into theHop-0 context window.
2. **Tier 1 (`describe-tool`)**: On-demand input/output schema hydration for a
   single selected tool.
3. **Tier 2 (`call-tool`)**: Governed execution enforcing ``readOnlyHint``
   safety (mutating tools blocked unless ``allow_mutation=True`` /
   ``--allow-mutation`` is explicitly supplied) and emitting a SHA-256 receipt.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional, Sequence


def project_mcp_tools_tier0(tools: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Return Tier-0 compact tool summaries (`name`, `read_only`, 1-line summary)."""
    summaries: List[Dict[str, Any]] = []
    for tool in tools:
        annotations = tool.get("annotations") or {}
        read_only = bool(annotations.get("readOnlyHint", tool.get("read_only", True)))
        desc = str(tool.get("description", "")).strip().splitlines()[0] if tool.get("description") else ""
        summaries.append(
            {
                "name": str(tool.get("name", "")).strip(),
                "read_only": read_only,
                "summary": desc[:120],
            }
        )
    return summaries


def describe_mcp_tool_tier1(
    tools: Sequence[Mapping[str, Any]],
    tool_name: str,
) -> Dict[str, Any]:
    """Hydrate Tier-1 full schema for a single named MCP tool on demand."""
    target = tool_name.strip()
    for tool in tools:
        if str(tool.get("name", "")).strip() == target:
            annotations = tool.get("annotations") or {}
            return {
                "tier": 1,
                "name": target,
                "description": str(tool.get("description", "")),
                "read_only": bool(annotations.get("readOnlyHint", tool.get("read_only", True))),
                "input_schema": dict(tool.get("inputSchema") or tool.get("input_schema") or {}),
            }
    raise KeyError(f"MCP tool not found: {target!r}")


def gate_mcp_tool_call_tier2(
    tool_spec: Mapping[str, Any],
    arguments: Mapping[str, Any],
    *,
    allow_mutation: bool = False,
) -> Dict[str, Any]:
    """Enforce `readOnlyHint` mutation gate and emit a deterministic SHA-256 call receipt."""
    annotations = tool_spec.get("annotations") or {}
    read_only = bool(annotations.get("readOnlyHint", tool_spec.get("read_only", True)))
    if not read_only and not allow_mutation:
        return {
            "allowed": False,
            "reason": "MUTATING_MCP_TOOL_BLOCKED_WITHOUT_ALLOW_MUTATION",
            "tool_name": str(tool_spec.get("name", "")),
            "read_only": False,
        }
    payload = json.dumps(
        {"tool": tool_spec.get("name"), "arguments": dict(arguments)},
        sort_keys=True,
    ).encode("utf-8")
    return {
        "allowed": True,
        "reason": "ALLOWED",
        "tool_name": str(tool_spec.get("name", "")),
        "read_only": read_only,
        "call_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
    }
