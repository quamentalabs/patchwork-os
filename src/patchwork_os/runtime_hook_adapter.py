"""Multi-Runtime, Multi-Dev-Env & Multi-AI-Family Agnostic Hook/Lint Adapter and Software Factory Blueprints.

Provides:
1. Canonical Runtime / Dev-Environment / AI-Family Hook & Lint Adapter Matrix across
   ``cc``, ``codex``, ``agy``, ``muse``, and ``kiro`` (``aws_kiro``) spanning
   ``cli``, ``ide_extension``, ``desktop_app``, and ``crew`` surfaces.
2. Tool Vocabulary Normalization (including Kiro's ``execute_bash``, ``fs_read``,
   ``fs_write``, ``str_replace``, ``list_directory``, ``glob``, ``grep``, and
   ``invoke_subagent``) and ``PreToolUse`` / ``UserPromptSubmit`` / ``Stop`` wire
   protocols (including Kiro's ``exit 2 + stderr`` blocking contract).
3. Eight Core Agnostic Hook Contracts & Evaluators plus ``skill-brief`` and
   ``voyage-maps`` configuration schemas:
   - ``stance_consistency_hook``
   - ``insights_reminder_hook``
   - ``context_route_contract_hook``
   - ``skill_auto_context_gate``
   - ``voyage_map_home_guard``
   - ``model_hardcoding_gate``
   - ``fable_governance_gate``
   - ``windowless_conhost_prevention_gate``
4. Generalized Re-Implementation Blueprints (Concepts, Procedures, Patterns, and ADRs)
   for ``knowledge_vault``, ``converging_voyage``, ``rea_reverse_engineering``, and
   ``software_factory``.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

CANONICAL_RUNTIMES: tuple[str, ...] = ("cc", "codex", "agy", "muse", "kiro")
CANONICAL_DEV_ENV_SURFACES: tuple[str, ...] = (
    "cli",
    "ide_extension",
    "desktop_app",
    "crew",
)
CANONICAL_AI_FAMILIES: tuple[str, ...] = ("claude", "gpt", "gemini", "muse")

CANONICAL_TOOL_VOCABULARY_MAP: Dict[str, tuple[str, ...]] = {
    "shell": (
        "execute_bash",
        "run_command",
        "Bash",
        "PowerShell",
        "bash",
        "shell",
        "exec_command",
        "functions.exec_command",
    ),
    "read": (
        "fs_read",
        "read",
        "read_file",
        "Read",
        "view_file",
        "load_resource",
    ),
    "write": (
        "fs_write",
        "write",
        "write_file",
        "Write",
        "write_to_file",
    ),
    "edit": (
        "str_replace",
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "replace_file_content",
        "multi_replace_file_content",
        "apply_patch",
    ),
    "search": (
        "list_directory",
        "list_dir",
        "glob",
        "Glob",
        "find_by_name",
        "grep",
        "Grep",
        "grep_search",
    ),
    "subagent": (
        "invoke_subagent",
        "Agent",
        "dispatch_subagent",
    ),
}

SKILL_BRIEF_CONFIG_DEFAULT: Dict[str, Any] = {
    "schema_version": 1,
    "enabled": True,
    "skill_roots": [
        ".agents/skills",
        ".claude/skills",
        ".codex/skills",
        ".gemini/skills",
        ".kiro/skills",
        "skills",
    ],
    "skill_path_pattern": (
        r"(?:^|[/\\\\])(?:\.(?:agents|claude|codex|gemini|kiro)[/\\\\]skills|skills)"
        r"[/\\\\]([a-z0-9][a-z0-9-]*)[/\\\\]SKILL\.md$"
    ),
    "injection_tag": "SKILL_BRIEF",
}

VOYAGE_MAPS_CONFIG_DEFAULT: Dict[str, Any] = {
    "schema_version": 1,
    "canonical_home": "docs/voyage",
    "filename_regex": r"^voyage-map-[a-z0-9-]+-\d{8}\.md$",
    "edit_tools": [
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "replace_file_content",
        "multi_replace_file_content",
        "str_replace",
    ],
    "write_tools": [
        "Write",
        "write_to_file",
        "write_file",
        "fs_write",
        "write",
    ],
    "runtimes": ["cc", "codex", "agy", "muse", "kiro"],
}

RUNTIME_HOOK_ADAPTER_MATRIX: Dict[str, Dict[str, Any]] = {
    "cc": {
        "runtime": "cc",
        "ai_family": "claude",
        "supported_surfaces": ["cli", "ide_extension", "desktop_app"],
        "config_shape": "hooks-v1",
        "project_config_path": ".claude/settings.json",
        "user_config_path": "~/.claude/settings.json",
        "windowless_spawn_contract": {
            "interpreter": "pythonw.exe -X utf8 -B",
            "node_spawn_option": "windowsHide: true",
            "win32_creation_flag": "CREATE_NO_WINDOW (0x08000000)",
        },
        "event_map": {
            "session.start": "SessionStart",
            "prompt.submit": "UserPromptSubmit",
            "tool.pre": "PreToolUse",
            "tool.post": "PostToolUse",
            "turn.stop": "Stop",
            "context.precompact": "PreCompact",
            "context.postcompact": "PostCompact",
            "session.end": "SessionEnd",
        },
        "wire_protocol": {
            "pretool_block_exit_code": 0,
            "pretool_block_channel": "stdout_json_hookSpecificOutput_deny",
            "prompt_inject_channel": "stdout_json_additionalContext",
            "stop_block_channel": "stdout_json_decision_block",
        },
        "verification": "unverified_example",
    },
    "codex": {
        "runtime": "codex",
        "ai_family": "gpt",
        "supported_surfaces": ["cli", "ide_extension", "desktop_app"],
        "config_shape": "hooks-codex-v1",
        "project_config_path": ".codex/hooks.json",
        "user_config_path": "~/.codex/hooks.json",
        "windowless_spawn_contract": {
            "interpreter": "pythonw.exe -X utf8 -B",
            "transport": "portable_host_runtime.py --dispatch <base64_descriptor>",
            "win32_creation_flag": "CREATE_NO_WINDOW (0x08000000)",
        },
        "event_map": {
            "session.start": "SessionStart",
            "prompt.submit": "UserPromptSubmit",
            "tool.pre": "PreToolUse",
            "tool.post": "PostToolUse",
            "turn.stop": "Stop",
        },
        "wire_protocol": {
            "pretool_block_exit_code": 0,
            "pretool_block_channel": "stdout_json_decision_block",
            "prompt_inject_channel": "stdout_json_additionalContext",
            "stop_block_channel": "stdout_json_decision_block",
        },
        "verification": "unverified_example",
    },
    "agy": {
        "runtime": "agy",
        "ai_family": "gemini",
        "supported_surfaces": ["cli", "ide_extension", "desktop_app"],
        "config_shape": "hooks-agy-v1",
        "project_config_path": ".gemini/hooks.json",
        "user_config_path": "~/.gemini/antigravity/hooks.json",
        "windowless_spawn_contract": {
            "interpreter": "pythonw.exe -B (unquoted command string)",
            "grouped_tool_events": ["PreToolUse", "PostToolUse"],
            "win32_creation_flag": "CREATE_NO_WINDOW (0x08000000)",
        },
        "event_map": {
            "prompt.submit": "PreInvocation",
            "tool.pre": "PreToolUse",
            "tool.post": "PostToolUse",
            "turn.stop": "PostInvocation",
        },
        "wire_protocol": {
            "pretool_block_exit_code": 0,
            "pretool_block_channel": "stdout_json_decision_deny",
            "prompt_inject_channel": "stdout_json_inject_steps_ephemeral_message",
            "stop_block_channel": "stdout_json_decision_block",
        },
        "verification": "unverified_example",
    },
    "muse": {
        "runtime": "muse",
        "ai_family": "muse",
        "supported_surfaces": ["cli"],
        "config_shape": "hooks-v1",
        "project_config_path": ".muse/hooks.json",
        "user_config_path": "~/.muse/hooks.json",
        "windowless_spawn_contract": {
            "interpreter": "pythonw.exe -X utf8 -B",
            "win32_creation_flag": "CREATE_NO_WINDOW (0x08000000)",
        },
        "event_map": {
            "prompt.submit": "UserPromptSubmit",
            "tool.pre": "PreToolUse",
            "turn.stop": "Stop",
        },
        "wire_protocol": {
            "pretool_block_exit_code": 0,
            "pretool_block_channel": "stdout_json_decision_block",
            "prompt_inject_channel": "stdout_raw_text",
            "stop_block_channel": "stdout_json_decision_block",
        },
        "verification": "unverified_example",
    },
    "kiro": {
        "runtime": "kiro",
        "aliases": ["aws_kiro", "kiro-cli", "kiro-ide", "kiro-crew"],
        "ai_family": "claude",
        "supported_surfaces": ["cli", "ide_extension", "crew"],
        "config_shape": "hooks-kiro-v1",
        "project_config_path": ".kiro/hooks",
        "user_config_path": "~/.kiro/hooks",
        "skills_paths": [".kiro/skills", "~/.kiro/skills"],
        "steering_paths": [".kiro/steering", "~/.kiro/steering"],
        "agents_crew_paths": [".kiro/agents", "~/.kiro/agents"],
        "mcp_paths": [".kiro/settings/mcp.json", "~/.kiro/settings/mcp.json"],
        "specs_path": ".kiro/specs",
        "windowless_spawn_contract": {
            "interpreter": "pythonw.exe -X utf8 -B",
            "node_process_runner_patch": "windowsHide:!0 on all shell:!0 spawn sites in acp-server.js and extension.js",
            "win32_creation_flag": "CREATE_NO_WINDOW (0x08000000)",
        },
        "event_map": {
            "session.start": "SessionStart",
            "prompt.submit": "UserPromptSubmit",
            "tool.pre": "PreToolUse",
            "tool.post": "PostToolUse",
            "context.precompact": "PreCompact",
            "context.postcompact": "PostCompact",
            "turn.stop": "Stop",
            "session.end": "SessionEnd",
        },
        "wire_protocol": {
            "pretool_block_exit_code": 2,
            "pretool_block_channel": "stderr_message_with_exit_2",
            "prompt_inject_channel": "stdout_raw_text_wrapped_in_HOOK_INSTRUCTION",
            "stop_block_channel": "stdout_json_or_stderr_notice",
        },
        "verification": "unverified_example",
    },
}

EIGHT_CORE_HOOK_CONTRACTS: tuple[Dict[str, Any], ...] = (
    {
        "hook_id": "stance-consistency-hook",
        "canonical_event": "prompt.submit",
        "enforcement": "advisory",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "purpose": "Injects active persona/stance selection consistency contract at turn start.",
    },
    {
        "hook_id": "insights-reminder-hook",
        "canonical_event": "prompt.submit",
        "enforcement": "advisory",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "purpose": "Injects concise analytical insight-block reminder across all runtimes.",
    },
    {
        "hook_id": "context-route-contract-hook",
        "canonical_event": "tool.pre",
        "secondary_event": "turn.stop",
        "enforcement": "blocking",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "fs_read|read|read_file|Read|view_file|glob|Glob|grep|Grep|list_directory|execute_bash|run_command|Bash|shell",
        "purpose": "Enforces AST-graph + Knowledge-Vault lookup before exhaustive search and blocks premature absence claims on Stop.",
    },
    {
        "hook_id": "skill-auto-context-gate",
        "canonical_event": "tool.pre",
        "enforcement": "advisory",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "fs_read|read|read_file|Read|view_file|fs_write|write|write_file|Write|str_replace|Edit|execute_bash|run_command|Bash|shell|grep|Grep",
        "purpose": "Auto-injects [SKILL_BRIEF] and compact AST codemaps when reading or editing skill/code paths.",
    },
    {
        "hook_id": "voyage-map-home-guard",
        "canonical_event": "tool.pre",
        "enforcement": "advisory",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "fs_write|write|write_file|Write|write_to_file|str_replace|Edit|MultiEdit|replace_file_content",
        "purpose": "Routes converging-voyage map documents to canonical docs/voyage/ directory.",
    },
    {
        "hook_id": "model-hardcoding-gate",
        "canonical_event": "tool.pre",
        "enforcement": "blocking",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "execute_bash|run_command|Bash|shell|fs_write|write|write_file|Write|str_replace|Edit",
        "purpose": "Blocks hardcoded model identifiers outside centralized model registry configuration.",
    },
    {
        "hook_id": "fable-governance-gate",
        "canonical_event": "tool.pre",
        "enforcement": "blocking",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "fs_write|write|write_file|Write|write_to_file|str_replace|Edit|MultiEdit|replace_file_content",
        "purpose": "Enforces 3xPR, FRR, epistemic KK/KU/UK/UU/no-tradeoff completeness, and guarded test assertion preservation.",
    },
    {
        "hook_id": "windowless-conhost-prevention-gate",
        "canonical_event": "tool.pre",
        "enforcement": "blocking",
        "supported_runtimes": list(CANONICAL_RUNTIMES),
        "matcher": "execute_bash|run_command|Bash|PowerShell|shell|exec_command",
        "purpose": "Prevents unwrapped console-spawning shells (powershell, pwsh, cmd, Start-Process, conhost, wt) on Windows while permitting direct windowless binary invocations.",
    },
)

GENERALIZED_REIMPLEMENTATION_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "knowledge_vault": {
        "concept": "3-Layer Plain-Markdown Knowledge Hub-and-Spoke Vault (CMDS: raw/, wiki/, rules/) with Progressive Disclosure.",
        "invariants": [
            "Zero proprietary database or Obsidian lock-in (.obsidian, .canvas, and [[wikilink]] forbidden).",
            "Turn-start query-first discipline: query AST code graph (graft) then Knowledge-Vault index before exhaustive grep/read.",
            "Progressive disclosure: load compact index.md (<4KB) at Hop 0 and hydrate individual spoke documents on demand.",
        ],
        "procedure_stages": [
            "Stage 1: Initialize raw/, wiki/, rules/, and root index.md with POSIX relative links.",
            "Stage 2: Bind spoke projections via 3-tier OS-agnostic links (symlink -> junction/hardlink -> atomic copy).",
            "Stage 3: Enforce turn-start query receipt before broad repository search.",
            "Stage 4: Audit link graph completeness (0 orphan nodes, 0 forbidden tokens).",
        ],
        "adr_decisions": [
            "ADR-KV-01: Plain Markdown over proprietary vault databases for ITAR/air-gap portability.",
            "ADR-KV-02: Hop-0 150,000-character ceiling to prevent context truncation.",
        ],
    },
    "converging_voyage": {
        "concept": "Deterministic Multi-Branch / Multi-Worktree Convergence Lifecycle with 2-Stage Guarded Main Landing and Lease Self-Healing.",
        "invariants": [
            "All voyage map artifacts reside under docs/voyage/ (enforced by voyage-map-home-guard across all 5 runtimes).",
            "Two-stage execution: --dry-run preflight must pass before --execute mutates refs.",
            "Expected-old-OID atomic ref update instead of mutating a dirty destination worktree.",
            "Cryptographic HMAC-SHA256 session lease self-healing without clobbering foreign session claims.",
        ],
        "procedure_stages": [
            "Stage 1: Author or update voyage map in docs/voyage/voyage-map-<slug>-<YYYYMMDD>.md.",
            "Stage 2: Claim explicit target write paths in the shared session lease registry.",
            "Stage 3: Run --dry-run landing preflight to verify clean-tree, parity gates, and expected old OID.",
            "Stage 4: Execute atomic ref update and emit convergence receipt.",
        ],
        "adr_decisions": [
            "ADR-CV-01: Never git reset --hard or overwrite untracked/foreign files in shared worktrees.",
            "ADR-CV-02: Separate preflight observation from ref mutation.",
        ],
    },
    "rea_reverse_engineering": {
        "concept": "4-Stage Forward-Reverse-Roundtrip (FRR) Deconstruction Engine for Binaries, ASAR/VSIX/JS Bundles, Protocols, and Runtimes.",
        "invariants": [
            "Zero speculative extrapolation: every claim cites observed binary offsets, bundle AST spans, or SHA-256 digests.",
            "Spawn-chain & windowless verification: audit every child_process.spawn / exec / CreateProcessW site for windowsHide:true and CREATE_NO_WINDOW.",
            "Hook & protocol schema extraction: extract exact validator schemas (e.g., Zod/Protobuf/JSON) from runtime bundles before authoring adapters.",
            "Second-generation round-trip closure: unpack .bundle and .zip in a clean sandbox, run tests, re-export, and verify 0 tree mismatches.",
        ],
        "procedure_stages": [
            "Stage 1 (Forward Inventory): Fingerprint PE64/ELF/Mach-O headers, ASAR/VSIX/JS bundles, and process spawn trees.",
            "Stage 2 (Reverse Deconstruction): Extract internal hook schemas, tool names, and stdio/exit-code contracts.",
            "Stage 3 (Subsystem Remediation & Sandbox Execution): Patch missing windowsHide flags, project runtime adapters, and verify 0 console popups.",
            "Stage 4 (Round-Trip Closure): Re-bundle, re-clone, and assert 100% SHA-256 byte identity across all tracked files.",
        ],
        "adr_decisions": [
            "ADR-REA-01: Root-cause elimination in runtime spawners over external shell-wrapper monkey patches.",
            "ADR-REA-02: Empirical live-session measurement across CLI, IDE extension, desktop app, and crew surfaces.",
        ],
    },
    "software_factory": {
        "concept": "Autonomous Multi-Runtime Software Factory uniting WFC DAG Planning, 5-Wave MPT:N Role-Disjoint Synthesis, and 9-Step TDD.",
        "invariants": [
            "Strict 5-role orthogonality: Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator.",
            "Cross-runtime counterpart coverage: pair distinct runtimes/models (e.g., cc + kiro, codex + agy) so no runtime grades its own homework.",
            "9-step TDD + mutation kill gate: verify tests fail when production logic is mutated.",
            "Delivery-first anti-choke budget: cap non-critical meta-machinery review loops to 1 review + 1 fix + 1 re-review before shipping consumer value.",
        ],
        "procedure_stages": [
            "Stage 1 (Planning Wave): Decompose EARS requirements.md -> design.md -> tasks.md and compile WFC DAG.",
            "Stage 2 (Reasoning & Implementation Wave): Execute leased worker legs under 9-step TDD.",
            "Stage 3 (Adversarial Triage Wave): Run Tier-0 AST/lint gates and independent Validator review.",
            "Stage 4 (Synthesis & Orchestration Wave): Reconcile findings and fold verified fixes into consumer artifacts.",
            "Stage 5 (Meta-Evaluation & Landing Wave): Audit FRR receipts, update Knowledge-Vault, and land via Converging-Voyage.",
        ],
        "adr_decisions": [
            "ADR-SF-01: Pre-bound task templates with HMAC lease tokens and SHA-256 diff pinning.",
            "ADR-SF-02: Unified 8-hook governance adapter across cc, codex, agy, muse, and kiro.",
        ],
    },
}


def normalize_runtime_id(runtime: str) -> str:
    """Normalize runtime alias (`aws_kiro`, `claude`, `cc`, etc.) to canonical runtime ID."""
    cleaned = (runtime or "").strip().lower()
    if cleaned in ("claude", "cc", "claude-code"):
        return "cc"
    if cleaned in ("aws_kiro", "kiro", "kiro-cli", "kiro-ide", "kiro-crew"):
        return "kiro"
    if cleaned in CANONICAL_RUNTIMES:
        return cleaned
    raise ValueError(f"Unsupported runtime identifier: {runtime!r}")


def normalize_tool_category(tool_name: str) -> str:
    """Map any runtime-specific tool name (`execute_bash`, `fs_read`, `str_replace`, etc.) to its canonical category."""
    cleaned = (tool_name or "").strip()
    for category, names in CANONICAL_TOOL_VOCABULARY_MAP.items():
        if cleaned in names:
            return category
    return "other"


def format_hook_verdict(
    runtime: str,
    canonical_event: str,
    decision: str,
    *,
    reason: str = "",
    additional_context: str = "",
) -> Dict[str, Any]:
    """Format a canonical hook verdict into the exact wire protocol of the target runtime."""
    rt = normalize_runtime_id(runtime)
    dec = decision.strip().lower()

    if canonical_event == "tool.pre":
        if dec in ("deny", "block"):
            if rt == "kiro":
                return {
                    "runtime": rt,
                    "exit_code": 2,
                    "stdout": "",
                    "stderr": reason or "Blocked by PreToolUse governance gate.",
                    "status": "blocked",
                }
            if rt == "cc":
                payload = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
                return {
                    "runtime": rt,
                    "exit_code": 0,
                    "stdout": json.dumps(payload, ensure_ascii=False),
                    "stderr": "",
                    "status": "blocked",
                }
            if rt == "agy":
                payload = {"decision": "deny", "reason": reason}
                return {
                    "runtime": rt,
                    "exit_code": 0,
                    "stdout": json.dumps(payload, ensure_ascii=False),
                    "stderr": "",
                    "status": "blocked",
                }
            payload = {"decision": "block", "reason": reason}
            return {
                "runtime": rt,
                "exit_code": 0,
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
                "status": "blocked",
            }
        # allow / advisory
        if additional_context:
            if rt == "kiro":
                return {
                    "runtime": rt,
                    "exit_code": 0,
                    "stdout": additional_context,
                    "stderr": "",
                    "status": "allowed_with_context",
                }
            if rt == "agy":
                payload = {
                    "decision": "allow",
                    "inject_steps": [{"ephemeral_message": additional_context}],
                }
            else:
                payload = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": additional_context,
                    }
                }
            return {
                "runtime": rt,
                "exit_code": 0,
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
                "status": "allowed_with_context",
            }
        return {
            "runtime": rt,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "status": "allowed",
        }

    if canonical_event == "prompt.submit":
        if rt in ("kiro", "muse"):
            return {
                "runtime": rt,
                "exit_code": 0,
                "stdout": additional_context,
                "stderr": "",
                "status": "injected",
            }
        if rt == "agy":
            payload = {"inject_steps": [{"ephemeral_message": additional_context}]}
        else:
            payload = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": additional_context,
                }
            }
        return {
            "runtime": rt,
            "exit_code": 0,
            "stdout": json.dumps(payload, ensure_ascii=False),
            "stderr": "",
            "status": "injected",
        }

    # turn.stop
    if dec in ("deny", "block"):
        payload = {"decision": "block", "reason": reason}
        return {
            "runtime": rt,
            "exit_code": 0,
            "stdout": json.dumps(payload, ensure_ascii=False),
            "stderr": "",
            "status": "blocked",
        }
    return {"runtime": rt, "exit_code": 0, "stdout": "", "stderr": "", "status": "ok"}


_UNWRAPPED_CONSOLE_RE = re.compile(
    r"(?:^|[;&|]\s*)(?:Start-Process|powershell(?:\.exe)?|pwsh(?:\.exe)?|cmd(?:\.exe)?|conhost(?:\.exe)?|wt(?:\.exe)?)\b",
    re.IGNORECASE,
)
_HARDCODED_MODEL_RE = re.compile(
    r"\b(?:gpt-4o|claude-3-5-sonnet-20241022|gemini-1\.5-pro)\b",
    re.IGNORECASE,
)


def evaluate_core_hook_gate(
    hook_id: str,
    runtime: str,
    tool_name: str = "",
    tool_input: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate one of the 8 core runtime-agnostic hooks and return the wire-formatted verdict."""
    rt = normalize_runtime_id(runtime)
    category = normalize_tool_category(tool_name)
    inp = dict(tool_input or {})

    command_text = str(
        inp.get("command")
        or inp.get("CommandLine")
        or inp.get("cmd")
        or ""
    )
    target_path = str(
        inp.get("file_path")
        or inp.get("path")
        or inp.get("Path")
        or inp.get("TargetFile")
        or ""
    ).replace("\\", "/")
    content_text = str(
        inp.get("content")
        or inp.get("Content")
        or inp.get("new_str")
        or inp.get("new_string")
        or inp.get("Replacement")
        or ""
    )

    if hook_id == "windowless-conhost-prevention-gate":
        if category == "shell" and _UNWRAPPED_CONSOLE_RE.search(command_text):
            return format_hook_verdict(
                rt,
                "tool.pre",
                "deny",
                reason="COMMAND_ROUTE_UNWRAPPED_CONSOLE_REFUSED: Use direct windowless binary invocation (python.exe / pythonw.exe -X utf8 -B) without spawning a console shell.",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "model-hardcoding-gate":
        haystack = f"{command_text}\n{content_text}"
        if category in ("shell", "write", "edit") and _HARDCODED_MODEL_RE.search(haystack):
            return format_hook_verdict(
                rt,
                "tool.pre",
                "deny",
                reason="MODEL_HARDCODING_REFUSED: Resolve model identifiers from centralized models.json instead of hardcoding legacy model IDs.",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "voyage-map-home-guard":
        if category in ("write", "edit") and "voyage-map-" in target_path and not target_path.startswith("docs/voyage/"):
            return format_hook_verdict(
                rt,
                "tool.pre",
                "allow",
                additional_context=f"[VOYAGE_MAP_HOME_GUARD] Route voyage maps to {VOYAGE_MAPS_CONFIG_DEFAULT['canonical_home']}/.",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "skill-auto-context-gate":
        m = re.search(SKILL_BRIEF_CONFIG_DEFAULT["skill_path_pattern"], target_path)
        if category in ("read", "write", "edit") and m:
            skill_slug = m.group(1)
            digest = hashlib.sha256(skill_slug.encode("utf-8")).hexdigest()[:12]
            return format_hook_verdict(
                rt,
                "tool.pre",
                "allow",
                additional_context=f"[SKILL_BRIEF skill={skill_slug} sha={digest}]",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "fable-governance-gate":
        if category in ("write", "edit") and "tradeoff_shortcut_allowed: true" in content_text:
            return format_hook_verdict(
                rt,
                "tool.pre",
                "deny",
                reason="FABLE_NO_TRADEOFF_VIOLATION: Premise-compromising shortcuts are forbidden.",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "context-route-contract-hook":
        if category == "shell" and re.search(r"\bgrep\s+-rn\b", command_text) and not inp.get("graft_queried", False):
            return format_hook_verdict(
                rt,
                "tool.pre",
                "deny",
                reason="CONTEXT_ROUTE_QUERY_FIRST_REFUSED: Query AST graph (graft) and Knowledge-Vault before running raw recursive grep.",
            )
        return format_hook_verdict(rt, "tool.pre", "allow")

    if hook_id == "stance-consistency-hook":
        return format_hook_verdict(
            rt,
            "prompt.submit",
            "allow",
            additional_context="[STANCE_CONSISTENCY] Maintain assigned persona stance and orthogonal role boundaries.",
        )

    if hook_id == "insights-reminder-hook":
        return format_hook_verdict(
            rt,
            "prompt.submit",
            "allow",
            additional_context="[INSIGHTS_REMINDER] Surface concise architectural insights alongside verified changes.",
        )

    raise ValueError(f"Unknown hook_id: {hook_id!r}")


def render_kiro_hook_files(
    *,
    repo_root: str = "/workspace/patchwork-os",
    interpreter: str = "pythonw",
) -> Dict[str, Dict[str, Any]]:
    """Render Kiro v1 hook files (`.kiro/hooks/<hook_id>.json`) for all 8 core hooks."""
    root = repo_root.rstrip("/\\").replace("\\", "/")
    files: Dict[str, Dict[str, Any]] = {}
    for contract in EIGHT_CORE_HOOK_CONTRACTS:
        hid = contract["hook_id"]
        canonical_event = contract["canonical_event"]
        native_event = RUNTIME_HOOK_ADAPTER_MATRIX["kiro"]["event_map"][canonical_event]
        entry: Dict[str, Any] = {
            "name": hid,
            "description": contract["purpose"],
            "trigger": native_event,
        }
        if "matcher" in contract:
            entry["matcher"] = contract["matcher"]
        entry["action"] = {
            "type": "command",
            "command": f"{interpreter} -X utf8 -B {root}/scripts/hooks/{hid.replace('-', '_')}.py --runtime kiro",
        }
        entry["timeout"] = 10
        entry["enabled"] = True
        files[f"{hid}.json"] = {
            "version": "v1",
            "hooks": [entry],
        }
    return files
