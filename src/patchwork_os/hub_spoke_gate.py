# SPDX-License-Identifier: MIT
"""Host/Runtime-Agnostic 5-Role Hub-Spoke Binder, EARS Spec Validator, and Zero-Thinking Gate Router.

Synthesizes the atomic mechanisms from the Spec-Driven IDE vs Agentic CLI comparative architecture
via Synergetic Assimilation + Counterpart Limit Coverage:
1. Five-Role Orthogonal Separation (`Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator`)
2. HMAC-SHA256 token helper with caller-managed secret & task-template checks (`KK/KU/UK/UU` + `3xPR` + `FRR`)
3. Three-Tier OS-Agnostic Hub-Spoke Projection (`SYMLINK -> NTFS_JUNCTION/HARDLINK -> ATOMIC_COPY_FALLBACK`)
4. Four-Stage EARS Spec-Driven Workflow (`requirements.md -> design.md -> tasks.md -> bidirectional sync`)
5. Two-Stage Deterministic AST/Lint + Zero-Thinking Local LLM Gate & Pinpoint Escalation Router
6. Five-Phase Serial-Parallel Tessellation Execution Planner
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence

RoleType = Literal[
    "COMPOSER",
    "CRITICIZER",
    "VALIDATOR",
    "SYNTHESIZER",
    "META_EVALUATOR",
]

EscalationTarget = Literal[
    "NONE",
    "PLANNER_VALIDATOR",
    "SYNTHESIZER_HARVESTER",
    "COMPOSER_EXECUTOR",
    "CRITIC_COUNTERPART",
    "META_EVALUATOR_AUDITOR",
]

TokenBudgetTier = Literal["NANO_LOCAL", "FLASH_SYNTH", "HEAVY_DUAL_CORE"]

CANONICAL_FIVE_ROLES: tuple[RoleType, ...] = (
    "COMPOSER",
    "CRITICIZER",
    "VALIDATOR",
    "SYNTHESIZER",
    "META_EVALUATOR",
)

CANONICAL_COGNITIVE_PHASES: tuple[str, ...] = (
    "planning",
    "reasoning",
    "adversarial_triage",
    "synthesizing",
    "meta_evaluating",
    "orchestrating",
)

HUB_SUBDIRS: tuple[str, ...] = (
    "personas",
    "skills",
    "steering",
    "memory-graft",
    "leases",
    "scripts",
)

EARS_REQUIREMENT_RE = re.compile(
    r"\b(?:WHEN|WHILE|WHERE|IF)\b.+?\bTHE\s+SYSTEM\s+SHALL\b",
    re.IGNORECASE | re.DOTALL,
)

UNFILLED_TEMPLATE_RE = re.compile(
    r"\[Fill\s+[^\]]+\]|<TODO[^>]*>|\bTBD_PLACEHOLDER\b|\bPENDING\b"
)

# Deprecated public sentinel retained for compatibility; never a usable secret.
DEFAULT_LEASE_KEY = b"patchwork-os-clean-room-hmac-key-v2"


def _require_lease_secret(secret: bytes) -> None:
    if not isinstance(secret, bytes) or not secret or secret == DEFAULT_LEASE_KEY:
        raise ValueError("explicit non-empty non-public bytes secret required")


@dataclass(frozen=True)
class GateVerdictResult:
    """Structured verdict emitted by the 2-stage deterministic + zero-thinking local gate."""

    verdict: Literal["PASS", "FAIL", "AMBIGUOUS"]
    confidence: float
    violated_invariant: Optional[str] = None
    escalate_to: EscalationTarget = "NONE"
    escalation_reason: str = ""
    token_budget_tier: TokenBudgetTier = "NANO_LOCAL"
    thinking_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "violated_invariant": self.violated_invariant,
            "escalate_to": self.escalate_to,
            "escalation_reason": self.escalation_reason,
            "token_budget_tier": self.token_budget_tier,
            "thinking_enabled": self.thinking_enabled,
        }


def verify_five_role_orthogonality(roster: Dict[str, str]) -> Dict[str, Any]:
    """Verify strict 5-way role separation (`Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator`)."""
    reasons: List[str] = []
    normalized: Dict[str, str] = {}

    for role in CANONICAL_FIVE_ROLES:
        agent = str(roster.get(role, roster.get(role.lower(), ""))).strip()
        if not agent or agent.upper() == "PENDING":
            reasons.append(f"MISSING_ROLE_ASSIGNMENT:{role}")
        else:
            normalized[role] = agent

    seen_agents: Dict[str, List[str]] = {}
    for role, agent in normalized.items():
        seen_agents.setdefault(agent, []).append(role)

    collisions: List[str] = []
    for agent, roles in sorted(seen_agents.items()):
        if len(roles) > 1:
            collision = f"{agent}:{'+'.join(roles)}"
            collisions.append(collision)
            reasons.append(f"ROLE_ORTHOGONALITY_COLLISION:{collision}")

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "collisions": collisions,
        "roster": normalized,
    }


def generate_lease_token(
    task_id: str,
    role: RoleType,
    agent_id: str,
    diff_hash: str,
    secret: bytes,
) -> str:
    """Bind fields with HMAC-SHA256 using an explicit caller-managed secret.

    The consumer must manage an appropriate private high-entropy key. The
    legacy 16-hex tag format is retained. This helper implements neither key
    management, replay prevention, authorization nor company approval.
    """
    _require_lease_secret(secret)
    if role not in CANONICAL_FIVE_ROLES:
        raise ValueError(f"Unsupported role: {role!r}")
    if not task_id.strip() or not agent_id.strip() or not diff_hash.strip():
        raise ValueError("task_id, agent_id, and diff_hash must be non-empty")
    payload = f"{task_id.strip()}:{role}:{agent_id.strip()}:{diff_hash.strip()}".encode("utf-8")
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:16]
    return f"LEASE-v2-{task_id.strip()}-{role}-{agent_id.strip()}-{sig}"


def verify_lease_token(
    token: str,
    *,
    task_id: str,
    role: RoleType,
    agent_id: str,
    diff_hash: str,
    secret: bytes,
) -> bool:
    """Compare a MAC-bound token using an explicit secret, not an authority grant.

    Missing secret raises TypeError; empty/public/non-bytes keys raise
    ValueError before comparison. Other invalid field bindings return False.
    """
    _require_lease_secret(secret)
    try:
        expected = generate_lease_token(task_id, role, agent_id, diff_hash, secret=secret)
    except ValueError:
        return False
    return hmac.compare_digest(token.strip(), expected)


def verify_task_contract_template(
    template_text: str,
    *,
    require_completed: bool = False,
) -> Dict[str, Any]:
    """Validate an in-place edited task contract markdown document (`KK/KU/UK/UU` + `3xPR` + `FRR`)."""
    reasons: List[str] = []
    required_markers = (
        "lease_token:",
        "## 1. Epistemic Matrix (KK / KU / UK / UU)",
        "## 2. Synergetic Assimilation & Counterpart Limit Coverage",
        "## 3. 3xPR Gate",
        "## 4. FRR (Failure & Regression Record)",
    )
    for marker in required_markers:
        if marker not in template_text:
            reasons.append(f"MISSING_CONTRACT_MARKER:{marker}")

    def _extract_field(key: str) -> str:
        m = re.search(rf"^\s*{re.escape(key)}:\s*\"?([^\"\n#]+)\"?", template_text, re.MULTILINE)
        return m.group(1).strip() if m else ""

    composer = _extract_field("composer_agent")
    criticizer = _extract_field("criticizer_agent")
    validator = _extract_field("validator_agent") or _extract_field("planner_validator_agent")
    synthesizer = _extract_field("synthesizer_agent")
    meta_eval = _extract_field("meta_evaluator_agent")

    if composer and validator and composer != "PENDING" and composer == validator:
        reasons.append(f"ORTHOGONALITY_VIOLATION_COMPOSER_EQUALS_VALIDATOR:{composer}")
    if composer and criticizer and composer != "PENDING" and composer == criticizer:
        reasons.append(f"ORTHOGONALITY_VIOLATION_COMPOSER_EQUALS_CRITICIZER:{composer}")

    roster_check = verify_five_role_orthogonality(
        {
            "COMPOSER": composer,
            "CRITICIZER": criticizer,
            "VALIDATOR": validator,
            "SYNTHESIZER": synthesizer,
            "META_EVALUATOR": meta_eval,
        }
    )
    if require_completed and not roster_check["valid"]:
        reasons.extend(roster_check["reasons"])

    unfilled: List[str] = []
    if require_completed:
        for match in UNFILLED_TEMPLATE_RE.finditer(template_text):
            tok = match.group(0)
            unfilled.append(tok)
        if unfilled:
            reasons.append(f"UNFILLED_TEMPLATE_PLACEHOLDERS:{len(unfilled)}")

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "unfilled_placeholders": unfilled,
        "roster_orthogonality": roster_check,
    }


def _is_reparse_or_junction(path: Path) -> bool:
    """Safely detect symlinks and Windows NTFS junctions without following the target."""
    if path.is_symlink():
        return True
    is_junc = getattr(path, "is_junction", None)
    if callable(is_junc):
        try:
            if is_junc():
                return True
        except OSError:
            pass
    try:
        st = os.lstat(path)
        return bool(getattr(st, "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def _safe_remove_destination(dst: Path) -> None:
    """Remove an existing destination link, junction, file, or directory without deleting link targets."""
    if _is_reparse_or_junction(dst):
        try:
            dst.unlink()
            return
        except OSError:
            os.rmdir(dst)
            return
    if dst.is_dir():
        shutil.rmtree(dst)
    elif dst.exists():
        dst.unlink()


def safe_bind_spoke(
    src: Path,
    dst: Path,
    *,
    is_dir: bool = False,
    allow_junction: bool = True,
    overwrite_existing: bool = False,
) -> Dict[str, str]:
    """Bind through the existing fallback ladder, preserving existing destinations by default.

    Replacement is opt-in. Existing copies are preserved rather than implicitly
    synchronized. The legacy ATOMIC_COPY_FALLBACK label is not an atomicity claim.
    Callers must serialize destination writers; this is not a race-safe publish.
    """
    src_resolved = src.resolve(strict=True)
    if src_resolved.is_dir() != is_dir:
        raise ValueError("BIND_SOURCE_KIND_MISMATCH")
    if dst.name == "..":
        raise ValueError("BIND_DESTINATION_PARENT_COMPONENT")
    # Resolve parent aliases, but retain the destination entry itself for links.
    dst_entry = dst.parent.resolve() / dst.name
    if (
        src_resolved == dst_entry
        or dst_entry in src_resolved.parents
        or (is_dir and src_resolved in dst_entry.parents)
    ):
        raise ValueError("BIND_SOURCE_DESTINATION_OVERLAP")
    binding = {"source": src_resolved.as_posix(), "destination": dst.as_posix()}
    if _is_reparse_or_junction(dst):
        if dst.resolve() == src_resolved:
            if dst.is_symlink():
                tier = "SYMLINK"
            elif getattr(dst, "is_junction", lambda: False)():
                tier = "NTFS_JUNCTION"
            else:
                tier = "PRESERVED_EXISTING"
            return {"tier": tier, **binding}
        if not overwrite_existing:
            return {"tier": "PRESERVED_EXISTING", **binding}
        _safe_remove_destination(dst)
    elif dst.exists():
        if not is_dir and dst.samefile(src_resolved):
            return {"tier": "HARDLINK", **binding}
        if not overwrite_existing:
            return {"tier": "PRESERVED_EXISTING", **binding}
        _safe_remove_destination(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Tier 1: Native relative symlink
    try:
        rel_src = os.path.relpath(src_resolved, dst.parent.resolve())
        dst.symlink_to(rel_src, target_is_directory=is_dir)
        return {"tier": "SYMLINK", "source": src_resolved.as_posix(), "destination": dst.as_posix()}
    except OSError:
        pass

    # Tier 2: Windows NTFS Junction (directories) or Hardlink (files) without console popup
    if allow_junction and platform.system().lower() == "windows":
        try:
            if is_dir:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.run(
                    ["cmd.exe", "/c", "mklink", "/J", str(dst), str(src_resolved)],
                    check=True,
                    capture_output=True,
                    creationflags=flags,
                )
                return {"tier": "NTFS_JUNCTION", "source": src_resolved.as_posix(), "destination": dst.as_posix()}
            os.link(src_resolved, dst)
            return {"tier": "HARDLINK", "source": src_resolved.as_posix(), "destination": dst.as_posix()}
        except Exception:
            if _is_reparse_or_junction(dst):
                _safe_remove_destination(dst)
            elif dst.exists():
                return {"tier": "PRESERVED_EXISTING", **binding}

    # Tier 3: Deterministic atomic copy fallback
    if is_dir:
        shutil.copytree(src_resolved, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src_resolved, dst)
    return {"tier": "ATOMIC_COPY_FALLBACK", "source": src_resolved.as_posix(), "destination": dst.as_posix()}


def bootstrap_agnostic_hub(
    root: Path,
    *,
    overwrite_existing_root_docs: bool = False,
) -> Dict[str, Any]:
    """Initialize `.agent-hub/` SSoT and project spokes without clobbering existing repository files."""
    root = Path(root).resolve()
    hub = root / ".agent-hub"
    for sub in HUB_SUBDIRS:
        (hub / sub).mkdir(parents=True, exist_ok=True)

    rules_path = hub / "steering" / "core_rules.md"
    if not rules_path.is_file():
        rules_path.write_text(
            "# Patchwork-OS SSoT Steering & Epistemic Contract\n\n"
            "1. Orthogonal Roles: Composer != Criticizer != Validator != Synthesizer != Meta-Evaluator\n"
            "2. Epistemic Classification: KK / KU / UK / UU + No-Tradeoff\n"
            "3. Verification Gate: 3xPR + FRR + Tier-0 Deterministic AST/Lint Gate\n",
            encoding="utf-8",
            newline="\n",
        )

    tech_path = hub / "steering" / "tech.md"
    if not tech_path.is_file():
        tech_path.write_text(
            "# Technology Stack Steering\n\n"
            "- Python 3.12+ with strict type annotations on all functions.\n"
            "- No bare `except:` blocks or hardcoded credentials.\n",
            encoding="utf-8",
            newline="\n",
        )

    structure_path = hub / "steering" / "structure.md"
    if not structure_path.is_file():
        structure_path.write_text(
            "# Directory & Layer Architecture Steering\n\n"
            "- Unidirectional dependency flow: `api/pipelines -> services -> clients -> schemas/core`.\n"
            "- Mirror every module under `src/` with a deterministic test under `tests/`.\n",
            encoding="utf-8",
            newline="\n",
        )

    ledger_path = hub / "memory-graft" / "ledger.jsonl"
    if not ledger_path.is_file():
        init_row = {"event": "HUB_INITIALIZED", "schema_version": "2.0.0"}
        ledger_path.write_text(json.dumps(init_row, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    spokes: Dict[str, Dict[str, str]] = {}
    spokes["kiro_steering"] = safe_bind_spoke(hub / "steering", root / ".kiro" / "steering", is_dir=True)
    spokes["muse_graft"] = safe_bind_spoke(hub / "memory-graft", root / ".muse" / "vault-graft", is_dir=True)

    for doc_name in ("CLAUDE.md", "AGENTS.md"):
        target_doc = root / doc_name
        if target_doc.exists() and not overwrite_existing_root_docs:
            spokes[doc_name] = {
                "tier": "PRESERVED_EXISTING",
                "source": rules_path.as_posix(),
                "destination": target_doc.as_posix(),
            }
        else:
            spokes[doc_name] = safe_bind_spoke(
                rules_path,
                target_doc,
                is_dir=False,
                overwrite_existing=overwrite_existing_root_docs,
            )

    manifest = {
        "schema_version": "patchwork-hub-spoke-manifest-v2",
        "hub_path": hub.as_posix(),
        "rules_sha256": hashlib.sha256(rules_path.read_bytes()).hexdigest(),
        "spokes": spokes,
    }
    (hub / "sync-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def validate_ears_spec_bundle(spec_dir: Path) -> Dict[str, Any]:
    """Validate a 3-document Spec-Driven bundle (`requirements.md`, `design.md`, `tasks.md`)."""
    spec_dir = Path(spec_dir).resolve()
    req_path = spec_dir / "requirements.md"
    des_path = spec_dir / "design.md"
    tsk_path = spec_dir / "tasks.md"

    reasons: List[str] = []
    missing = [p.name for p in (req_path, des_path, tsk_path) if not p.is_file()]
    if missing:
        return {
            "valid": False,
            "reasons": [f"MISSING_SPEC_FILES:{','.join(missing)}"],
            "ears_clause_count": 0,
            "task_count": 0,
        }

    req_text = req_path.read_text(encoding="utf-8")
    des_text = des_path.read_text(encoding="utf-8")
    tsk_text = tsk_path.read_text(encoding="utf-8")

    ears_matches = EARS_REQUIREMENT_RE.findall(req_text)
    if not ears_matches:
        reasons.append("MISSING_EARS_ACCEPTANCE_CRITERIA")

    in_mermaid = False
    for idx, line in enumerate(des_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid and stripped.startswith("```"):
            in_mermaid = False
            continue
        if in_mermaid and len(line) > 79:
            reasons.append(f"DESIGN_MERMAID_LINE_TOO_WIDE:L{idx}:{len(line)}")

    task_items = re.findall(r"^\s*-\s*\[[ xX]\]\s+.+$", tsk_text, re.MULTILINE)
    if not task_items:
        reasons.append("MISSING_DEPENDENCY_ORDERED_TASKS")

    bundle_digest = hashlib.sha256(
        (req_text + "\n" + des_text + "\n" + tsk_text).encode("utf-8")
    ).hexdigest()

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "ears_clause_count": len(ears_matches),
        "task_count": len(task_items),
        "spec_bundle_sha256": bundle_digest,
    }


def extract_python_ast_summary(file_path: Path) -> Dict[str, Any]:
    """Extract function return-annotation coverage, bare except counts, and syntax status at Tier 0."""
    file_path = Path(file_path)
    if not file_path.is_file() or file_path.suffix != ".py":
        return {}
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"file": file_path.as_posix(), "syntax_error": str(exc), "functions": []}

    functions: List[Dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bare_excepts = sum(
                1
                for child in ast.walk(node)
                if isinstance(child, ast.ExceptHandler) and child.type is None
            )
            functions.append(
                {
                    "name": node.name,
                    "lineno": node.lineno,
                    "typed_return": node.returns is not None,
                    "bare_excepts": bare_excepts,
                }
            )
    return {"file": file_path.as_posix(), "functions": functions}


def build_deterministic_payload(
    root: Path,
    *,
    changed_files_override: Optional[Sequence[str]] = None,
    raw_diff_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract compact `<4KB` `{processed_ast_delta, processed_lint_errors, raw_diff_excerpt}` payload."""
    root = Path(root).resolve()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if raw_diff_override is not None:
        raw_diff = raw_diff_override
    else:
        cached = subprocess.run(
            ["git", "diff", "--cached", "--unified=1"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        ).stdout
        raw_diff = cached if cached.strip() else subprocess.run(
            ["git", "diff", "--unified=1"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        ).stdout

    if changed_files_override is not None:
        changed_files = list(changed_files_override)
    else:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        )
        changed_files = [
            line[3:].strip()
            for line in status_proc.stdout.splitlines()
            if len(line) > 3 and line[3:].strip()
        ]

    py_files = [root / rel for rel in changed_files if rel.endswith(".py") and (root / rel).is_file()]
    ast_summaries = [extract_python_ast_summary(p) for p in py_files]

    diff_hash = hashlib.sha256(raw_diff.encode("utf-8")).hexdigest()[:12]
    return {
        "diff_hash": diff_hash,
        "changed_files_count": len(changed_files),
        "changed_files": changed_files[:20],
        "processed_lint_errors": [],
        "processed_ast_delta": ast_summaries,
        "raw_diff_excerpt": raw_diff[:3500],
    }


def evaluate_zero_thinking_gate(
    payload: Dict[str, Any],
    *,
    local_classifier_fn: Optional[Callable[[Dict[str, Any]], GateVerdictResult]] = None,
) -> GateVerdictResult:
    """Run Stage-1 deterministic AST/Lint cutoff -> Stage-2 Zero-Thinking classifier -> Stage-3 Escalation."""
    for item in payload.get("processed_ast_delta", []):
        if "syntax_error" in item:
            return GateVerdictResult(
                verdict="FAIL",
                confidence=1.0,
                violated_invariant=f"SYNTAX_ERROR:{item['file']}:{item['syntax_error']}",
                escalate_to="NONE",
                token_budget_tier="NANO_LOCAL",
            )
        for fn in item.get("functions", []):
            if fn.get("bare_excepts", 0) > 0:
                return GateVerdictResult(
                    verdict="FAIL",
                    confidence=1.0,
                    violated_invariant=f"BARE_EXCEPT_FORBIDDEN:{item['file']}:L{fn['lineno']}:{fn['name']}",
                    escalate_to="NONE",
                    token_budget_tier="NANO_LOCAL",
                )

    lint_errors = payload.get("processed_lint_errors", [])
    if lint_errors:
        first = lint_errors[0]
        return GateVerdictResult(
            verdict="FAIL",
            confidence=1.0,
            violated_invariant=f"LINT_ERROR:{first.get('code', 'LINT')}:L{first.get('line', 0)}:{first.get('msg', '')}",
            escalate_to="NONE",
            token_budget_tier="NANO_LOCAL",
        )

    excerpt = str(payload.get("raw_diff_excerpt", "")).strip()
    if not excerpt and payload.get("changed_files_count", 0) == 0:
        return GateVerdictResult(verdict="PASS", confidence=1.0)

    if local_classifier_fn is not None:
        return local_classifier_fn(payload)

    changed_files = [str(f) for f in payload.get("changed_files", [])]
    changed_count = int(payload.get("changed_files_count", len(changed_files)))

    if any("schema" in f or "spec" in f or "contract" in f for f in changed_files):
        return GateVerdictResult(
            verdict="AMBIGUOUS",
            confidence=0.70,
            escalate_to="PLANNER_VALIDATOR",
            escalation_reason="Schema or formal specification contract delta requires EARS/STDD validator check.",
            token_budget_tier="FLASH_SYNTH",
        )
    if changed_count >= 6:
        return GateVerdictResult(
            verdict="AMBIGUOUS",
            confidence=0.65,
            escalate_to="SYNTHESIZER_HARVESTER",
            escalation_reason=f"Multi-file cross-module change ({changed_count} files) requires parallel context harvest.",
            token_budget_tier="FLASH_SYNTH",
        )
    if changed_count >= 4 or len(excerpt) > 2500:
        return GateVerdictResult(
            verdict="AMBIGUOUS",
            confidence=0.68,
            escalate_to="CRITIC_COUNTERPART",
            escalation_reason=f"High-complexity diff ({changed_count} files, {len(excerpt)} chars) requires counterpart critique.",
            token_budget_tier="HEAVY_DUAL_CORE",
        )
    return GateVerdictResult(verdict="PASS", confidence=0.92)


CANONICAL_THREE_TIER_POLICIES: Dict[str, str] = {
    "cc": "3_TIER_DIRECT",
    "codex": "3_TIER_SLOT_DEDUP",
    "agy": "2_GEN_TO_3_TIER_PROJECTION",
    "muse": "3_TIER_DIRECT",
}


def _parse_version_tuple(ver_str: str) -> tuple[int, int]:
    parts = ver_str.split(".")
    major = int(parts[0]) if parts and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return (major, minor)


def resolve_canonical_three_tier_models(
    live_catalogs: Optional[Dict[str, Sequence[str]]] = None,
    *,
    cognitive_stage: Optional[str] = None,
    registry_path: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    """Resolve the canonical 3-tier deduplicated model vector (4 families x 3 tiers = 12 models).

    Policies:
    - cc (`3_TIER_DIRECT`): 3 distinct lineage slots (`fable`, `opus`, `sonnet`).
      Default and planning/reasoning/synthesizing stages order `["fable-5-1", "opus", "sonnet"]`
      (VLA Artificial Analysis v4.3.2: Fable 5.1 leads Humanity's Last Exam at xhigh 59% > 58%
      and AA-Omniscience Accuracy 67% [#1] > 66%); execution/validation/coding stages order
      `["opus", "fable-5-1", "sonnet"]` (Opus 5.5 leads Intelligence Index 58/56, AA-Briefcase
      1801/1761, GDPval-AA 1866/1829, and Terminal-Bench 4.0 67%/60%).
    - codex (`3_TIER_SLOT_DEDUP`): 3 canonical tier slots (`astra`, `sol`, `luna`), deduplicating
      intra-slot version bumps by selecting the highest `(major, minor)` version per slot
      (e.g., `6.1` supersedes `6.0` in the `sol` slot).
    - agy (`2_GEN_TO_3_TIER_PROJECTION`): Projects the top 2 active Gemini generations `(G1, G2)`
      into the 3-tier vector `[f"{G1}-high", G1, f"{G2}-high"]`, collapsing `-medium`/`-low` bloat.
    - muse (`3_TIER_DIRECT`): 3 distinct lineage slots (`wonder-full`, `wonder`, `spark`) with
      highest version per slot and `contributor` aliases excluded.
    """
    if registry_path is None:
        for anc in Path(__file__).resolve().parents:
            candidate_reg = anc / "config" / "orchestration" / "models.json"
            if candidate_reg.is_file():
                registry_path = candidate_reg
                break

    registry_runtimes: Dict[str, Any] = {}
    if registry_path is not None and registry_path.is_file():
        try:
            registry_runtimes = json.loads(registry_path.read_text(encoding="utf-8")).get("runtimes", {})
        except (OSError, ValueError):
            registry_runtimes = {}

    catalogs: Dict[str, List[str]] = {}
    for runtime in ("cc", "codex", "agy", "muse"):
        if live_catalogs and runtime in live_catalogs and live_catalogs[runtime]:
            catalogs[runtime] = list(live_catalogs[runtime])
        else:
            reg_entry = registry_runtimes.get(runtime, {})
            if isinstance(reg_entry.get("canonical_3tier"), list) and len(reg_entry["canonical_3tier"]) == 3:
                catalogs[runtime] = list(reg_entry["canonical_3tier"])
            else:
                catalogs[runtime] = list(dict.fromkeys(reg_entry.get("tiers", {}).values()))

    resolved: Dict[str, Dict[str, Any]] = {}

    # 1. cc: 3_TIER_DIRECT across ('fable', 'opus', 'sonnet') with dual-axis stage routing
    cc_raw = catalogs.get("cc", [])
    cc_slots: Dict[str, tuple[tuple[int, int], str]] = {}
    for slug in cc_raw:
        s = slug.strip()
        if s == "opus" or s.startswith("opus-"):
            ver = _parse_version_tuple(s.split("-", 1)[1].replace("-", ".")) if "-" in s else (99, 0)
            if "opus" not in cc_slots or ver > cc_slots["opus"][0]:
                cc_slots["opus"] = (ver, s)
        elif s.startswith("fable"):
            ver = _parse_version_tuple(s.split("-", 1)[1].replace("-", ".")) if "-" in s else (1, 0)
            if "fable" not in cc_slots or ver > cc_slots["fable"][0]:
                cc_slots["fable"] = (ver, s)
        elif s == "sonnet" or s.startswith("sonnet-"):
            ver = _parse_version_tuple(s.split("-", 1)[1].replace("-", ".")) if "-" in s else (99, 0)
            if "sonnet" not in cc_slots or ver > cc_slots["sonnet"][0]:
                cc_slots["sonnet"] = (ver, s)

    fable_winner = cc_slots.get("fable", ((0, 0), "fable-5-1"))[1]
    opus_winner = cc_slots.get("opus", ((0, 0), "opus"))[1]
    sonnet_winner = cc_slots.get("sonnet", ((0, 0), "sonnet"))[1]

    planning_order = [fable_winner, opus_winner, sonnet_winner]
    execution_order = [opus_winner, fable_winner, sonnet_winner]
    stage_norm = (cognitive_stage or "").strip().lower()
    if stage_norm in {"adversarial_triage", "meta_evaluating", "coding", "execution", "validation"}:
        cc_selected = execution_order
        cc_tier_slots = ["opus", "fable", "sonnet"]
        active_axis = "execution_validation_coding"
    else:
        cc_selected = planning_order
        cc_tier_slots = ["fable", "opus", "sonnet"]
        active_axis = "planning_reasoning_synthesis"

    resolved["cc"] = {
        "policy": CANONICAL_THREE_TIER_POLICIES["cc"],
        "active_cognitive_axis": active_axis,
        "tier_slots": cc_tier_slots,
        "selected_models": cc_selected,
        "selected_models_by_axis": {
            "planning_reasoning_synthesis": planning_order,
            "execution_validation_coding": execution_order,
        },
        "excluded_models": [m for m in cc_raw if m not in cc_selected],
    }

    # 2. codex: 3_TIER_SLOT_DEDUP across ('astra', 'sol', 'luna')
    codex_raw = catalogs.get("codex", [])
    codex_re = re.compile(r"^gpt-(\d+)(?:\.(\d+))?-(astra|sol|luna)$")
    codex_by_slot: Dict[str, List[tuple[tuple[int, int], str]]] = {"astra": [], "sol": [], "luna": []}
    codex_rejected: List[str] = []
    for slug in codex_raw:
        m = codex_re.match(slug.strip())
        if not m:
            codex_rejected.append(slug)
            continue
        ver = (int(m.group(1)), int(m.group(2) or 0))
        slot = m.group(3)
        codex_by_slot[slot].append((ver, slug.strip()))

    codex_selected: List[str] = []
    codex_superseded: Dict[str, List[str]] = {}
    for slot in ("astra", "sol", "luna"):
        candidates = sorted(codex_by_slot[slot], key=lambda item: item[0], reverse=True)
        if candidates:
            winner = candidates[0][1]
            codex_selected.append(winner)
            if len(candidates) > 1:
                codex_superseded[slot] = [c[1] for c in candidates[1:]]
        else:
            default_codex = [f"gpt-6-{'astra'}", "gpt-6.1-sol", f"gpt-6-{'luna'}"]
            fallback = registry_runtimes.get("codex", {}).get("canonical_3tier", []) or default_codex
            idx = ("astra", "sol", "luna").index(slot)
            codex_selected.append(fallback[idx] if idx < len(fallback) else default_codex[idx])

    resolved["codex"] = {
        "policy": CANONICAL_THREE_TIER_POLICIES["codex"],
        "tier_slots": ["astra", "sol", "luna"],
        "selected_models": codex_selected,
        "superseded_slot_duplicates": codex_superseded,
        "excluded_models": [m for m in codex_raw if m not in codex_selected],
    }

    # 3. agy: 2_GEN_TO_3_TIER_PROJECTION ([gen1-high, gen1-base, gen2-high])
    agy_raw = catalogs.get("agy", [])
    agy_re = re.compile(r"^(gemini-(\d+)(?:\.(\d+))?-([a-z0-9]+?))(?:-(high|medium|low))?$")
    agy_generations: Dict[str, tuple[int, int]] = {}
    for slug in agy_raw:
        m = agy_re.match(slug.strip())
        if not m:
            continue
        base_gen = m.group(1)
        ver = (int(m.group(2)), int(m.group(3) or 0))
        if base_gen not in agy_generations or ver > agy_generations[base_gen]:
            agy_generations[base_gen] = ver

    ranked_gens = [
        gen for gen, _ in sorted(agy_generations.items(), key=lambda item: item[1], reverse=True)
    ]
    if len(ranked_gens) >= 2:
        g1, g2 = ranked_gens[0], ranked_gens[1]
        agy_selected = [f"{g1}-high", g1, f"{g2}-high"]
    else:
        default_agy = ["gemini-4-argon-high", "gemini-4-argon", f"gemini-3.8-{'flash'}-high"]
        agy_selected = list(registry_runtimes.get("agy", {}).get("canonical_3tier", []) or default_agy)
        if not ranked_gens:
            ranked_gens = ["gemini-4-argon", f"gemini-3.8-{'flash'}"]

    resolved["agy"] = {
        "policy": CANONICAL_THREE_TIER_POLICIES["agy"],
        "active_generations": ranked_gens[:2],
        "tier_projection": ["gen1-high", "gen1-base", "gen2-high"],
        "selected_models": agy_selected,
        "excluded_models": [m for m in agy_raw if m not in agy_selected],
    }

    # 4. muse: 3_TIER_DIRECT across ('wonder-full', 'wonder', 'spark')
    muse_raw = catalogs.get("muse", [])
    muse_re = re.compile(r"^muse-(wonder-full|wonder|spark)-(\d+(?:\.\d+)*)$")
    muse_by_slot: Dict[str, List[tuple[tuple[int, int], str]]] = {
        "wonder-full": [],
        "wonder": [],
        "spark": [],
    }
    for slug in muse_raw:
        s = slug.strip()
        if "contributor" in s:
            continue
        m = muse_re.match(s)
        if not m:
            continue
        slot = m.group(1)
        ver = _parse_version_tuple(m.group(2))
        muse_by_slot[slot].append((ver, s))

    muse_selected: List[str] = []
    default_muse = ["muse-wonder-full-1.0", "muse-wonder-1.0", f"muse-{'spark'}-1.3"]
    for slot in ("wonder-full", "wonder", "spark"):
        candidates = sorted(muse_by_slot[slot], key=lambda item: item[0], reverse=True)
        if candidates:
            muse_selected.append(candidates[0][1])
        else:
            fallback = registry_runtimes.get("muse", {}).get("canonical_3tier", []) or default_muse
            idx = ("wonder-full", "wonder", "spark").index(slot)
            muse_selected.append(fallback[idx] if idx < len(fallback) else default_muse[idx])

    resolved["muse"] = {
        "policy": CANONICAL_THREE_TIER_POLICIES["muse"],
        "tier_slots": ["wonder-full", "wonder", "spark"],
        "selected_models": muse_selected,
        "excluded_models": [m for m in muse_raw if m not in muse_selected],
    }

    return resolved


def build_tessellation_plan(task_id: str, scope: str) -> Dict[str, Any]:
    """Build the 5-Phase Serial-Parallel Tessellation execution plan."""
    if not task_id.strip():
        raise ValueError("task_id must be non-empty")
    return {
        "schema_version": "patchwork-tessellation-v1",
        "task_id": task_id.strip(),
        "scope": scope.strip(),
        "canonical_three_tier_models": {
            rt: info["selected_models"]
            for rt, info in resolve_canonical_three_tier_models().items()
        },
        "phases": [
            {
                "phase": 1,
                "mode": "SERIAL",
                "name": "Planning & EARS Contract Lock",
                "tiles": [
                    {
                        "tile_id": "T1-SPEC",
                        "role": "VALIDATOR",
                        "cognitive_phase": "planning",
                        "deliverable": "requirements.md + design.md + tasks.md (PR-1 Lock)",
                    }
                ],
            },
            {
                "phase": 2,
                "mode": "PARALLEL_TESSELLATION",
                "name": "Context Harvesting & AST Baseline",
                "tiles": [
                    {
                        "tile_id": "T2-A-HARVEST",
                        "role": "SYNTHESIZER",
                        "cognitive_phase": "synthesizing",
                        "deliverable": "<2KB synthesized context & UK codemap cruxes",
                    },
                    {
                        "tile_id": "T2-B-MEMORY",
                        "role": "META_EVALUATOR",
                        "cognitive_phase": "meta_evaluating",
                        "deliverable": "Prior ADR lessons & domain invariants",
                    },
                    {
                        "tile_id": "T2-C-AST",
                        "role": "VALIDATOR",
                        "cognitive_phase": "reasoning",
                        "deliverable": "Deterministic Tier-0 AST & test baseline snapshot",
                    },
                ],
            },
            {
                "phase": 3,
                "mode": "SERIAL_PARALLEL_CROSS",
                "name": "Isolated Worktree Compose & Counterpart Critique",
                "tiles": [
                    {
                        "tile_id": "T3-1-COMPOSE",
                        "role": "COMPOSER",
                        "cognitive_phase": "orchestrating",
                        "deliverable": "Worktree implementation + unit tests",
                    },
                    {
                        "tile_id": "T3-2-CRITIQUE",
                        "role": "CRITICIZER",
                        "cognitive_phase": "adversarial_triage",
                        "deliverable": "Cross-family adversarial critique (PR-2 Sign-off)",
                    },
                ],
            },
            {
                "phase": 4,
                "mode": "SERIAL_GATE",
                "name": "Near-Deterministic Pre-Commit Verification",
                "tiles": [
                    {
                        "tile_id": "T4-GATE",
                        "role": "VALIDATOR",
                        "cognitive_phase": "adversarial_triage",
                        "deliverable": "Tier-0 AST/Lint + Tier-1 Zero-Thinking verdict (PR-3 Sign-off)",
                    }
                ],
            },
            {
                "phase": 5,
                "mode": "ASYNC_PARALLEL",
                "name": "Post-Commit Meta-Evaluation & Wiki Sync",
                "tiles": [
                    {
                        "tile_id": "T5-A-GRAFT",
                        "role": "META_EVALUATOR",
                        "cognitive_phase": "meta_evaluating",
                        "deliverable": "FRR & ledger.jsonl absorption",
                    },
                    {
                        "tile_id": "T5-B-DOCSYNC",
                        "role": "SYNTHESIZER",
                        "cognitive_phase": "synthesizing",
                        "deliverable": "Bidirectional EARS spec & CMDS wiki synchronization",
                    },
                ],
            },
        ],
    }


SESSION_TIER_VALUES: tuple[str, ...] = ("main_hub", "main_spoke_sub_hub")
TASK_CATEGORY_VALUES: tuple[str, ...] = (
    "planning_architecture_synthesis",
    "deep_reasoning_and_research",
    "execution_governance_and_audit",
    "agentic_coding_and_tdd",
    "browser_vla_and_automation",
    "adversarial_review_and_reconciliation",
    "fast_curation_and_telemetry",
)


def resolve_orchestrator_session_routing(
    *,
    session_tier: str = "main_hub",
    task_category: str = "planning_architecture_synthesis",
    complexity: str = "high",
    urgency: str = "normal",
    importance: str = "critical",
    registry_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Resolve Rank-1 and Rank-2 `{runtime, model, effort}` for `{Main-Hub, Main-Spoke/Sub-Hub}` x `{Task-Category, Complexity, Urgency, Importance}`.

    Grounded in Artificial Analysis v4.3.2 VLA measurements:
    - `fable-5-1` (`cc`): HLE `xhigh` 59% (#1 vs Opus 5.5 `xhigh` 58%), Omniscience Accuracy 67% (`max` #1) / 66% (`xhigh`).
    - `opus` (`cc`): Intelligence Index 58 (`max`) / 56 (`xhigh`), AA-Briefcase 1801/1761, GDPval-AA 1866/1829, Terminal-Bench 4.0 67%/60%, $3.46/task.
    - `muse-wonder-full-1.0` (`muse`): Intelligence Index 56, GDPval-AA 1857, GDP.pdf 33% (#1), CritPt 33% (#1), AutomationBench 71%.
    - `gpt-6-astra` / `gpt-6.1-sol` (`codex`): Cost/Task $0.39 (#1 Pareto), Non-Hallucination Rate 53% (#1).
    - `gemini-4-argon-high` (`agy`): AutomationBench-AA 78% (#1), Intelligence Index 53, $1.99/task.
    - `muse-wonder-1.0` (`muse`): 144 tok/s (#1 speed), 1049k context (#1).
    """
    s_tier = session_tier.strip().lower()
    if s_tier not in SESSION_TIER_VALUES:
        raise ValueError(f"session_tier must be one of {SESSION_TIER_VALUES}, got {session_tier!r}")
    cat = task_category.strip().lower()
    if cat not in TASK_CATEGORY_VALUES:
        raise ValueError(f"task_category must be one of {TASK_CATEGORY_VALUES}, got {task_category!r}")

    comp = complexity.strip().lower()
    urg = urgency.strip().lower()
    imp = importance.strip().lower()

    plan_models = resolve_canonical_three_tier_models(
        cognitive_stage="planning", registry_path=registry_path
    )
    exec_models = resolve_canonical_three_tier_models(
        cognitive_stage="adversarial_triage", registry_path=registry_path
    )

    cc_fable = plan_models["cc"]["selected_models"][0]
    cc_opus = exec_models["cc"]["selected_models"][0]
    cc_sonnet = plan_models["cc"]["selected_models"][2]

    codex_astra = plan_models["codex"]["selected_models"][0]
    codex_sol = plan_models["codex"]["selected_models"][1]
    codex_luna = plan_models["codex"]["selected_models"][2]

    agy_argon_high = plan_models["agy"]["selected_models"][0]
    agy_argon_base = plan_models["agy"]["selected_models"][1]
    agy_flash_high = plan_models["agy"]["selected_models"][2]

    muse_wonder_full = plan_models["muse"]["selected_models"][0]
    muse_wonder = plan_models["muse"]["selected_models"][1]
    muse_spark = plan_models["muse"]["selected_models"][2]

    high_effort = "max" if (comp == "high" and imp == "critical" and urg != "immediate") else (
        "high" if urg == "immediate" else "xhigh"
    )
    secondary_effort = "high" if urg == "immediate" else "xhigh"

    if s_tier == "main_hub":
        if cat in {"planning_architecture_synthesis", "deep_reasoning_and_research"}:
            if urg == "immediate" and comp == "low":
                rank_1 = {
                    "rank": 1,
                    "runtime": "cc",
                    "model": cc_opus,
                    "effort": "high",
                    "rationale": "Immediate-urgency low-complexity hub triage uses Opus 5.5 (high, 82 tok/s, $3.46/task).",
                }
                rank_2 = {
                    "rank": 2,
                    "runtime": "muse",
                    "model": muse_wonder,
                    "effort": "max",
                    "rationale": "144 tok/s ultra-fast throughput with 1049k context window.",
                }
            else:
                rank_1 = {
                    "rank": 1,
                    "runtime": "cc",
                    "model": cc_fable,
                    "effort": "xhigh" if high_effort != "max" else "xhigh",
                    "max_effort_option": "max",
                    "rationale": "Fable 5.1 leads Humanity's Last Exam at xhigh (59% vs Opus 5.5 xhigh 58%) and AA-Omniscience Raw Knowledge Accuracy (67% max #1 / 66% xhigh).",
                }
                rank_2 = {
                    "rank": 2,
                    "runtime": "muse",
                    "model": muse_wonder_full,
                    "effort": "max",
                    "cli_api_fallback": {"runtime": "cc", "model": cc_opus, "effort": high_effort},
                    "rationale": "Muse Wonder Full (Intelligence Index 56, GDPval-AA 1857, GDP.pdf 33%, CritPt 33%) with Opus 5.5 (Intelligence Index 58 max / 56 xhigh, AA-LCR 85%) as API/CLI fallback.",
                }
        elif cat in {"execution_governance_and_audit", "adversarial_review_and_reconciliation"}:
            rank_1 = {
                "rank": 1,
                "runtime": "cc",
                "model": cc_opus,
                "effort": high_effort,
                "rationale": "Opus 5.5 leads Aggregate Intelligence Index (58 max / 56 xhigh), AA-Briefcase (1801/1761), GDPval-AA (1866/1829), Non-Hallucination (41% vs Fable 27%), and Cost/Task ($3.46).",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "codex",
                "model": codex_astra if comp == "high" else codex_sol,
                "effort": secondary_effort,
                "rationale": "Cross-family adversarial governance (Composer != Validator) with GPT-6.1 Sol achieving 53% Non-Hallucination (#1) and $0.39/task.",
            }
        elif cat == "browser_vla_and_automation":
            rank_1 = {
                "rank": 1,
                "runtime": "agy",
                "model": agy_argon_high,
                "effort": "high",
                "rationale": "Gemini 4 Argon (High) ranks #1 overall on AutomationBench-AA (78%) with $1.99/task and native VLA vision-DOM loop integration.",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "muse",
                "model": muse_wonder_full,
                "effort": "max",
                "rationale": "Muse Wonder Full ranks #2 on AutomationBench-AA (71%) and #1 on GDP.pdf document reasoning (33%).",
            }
        elif cat == "agentic_coding_and_tdd":
            rank_1 = {
                "rank": 1,
                "runtime": "cc",
                "model": cc_opus,
                "effort": high_effort,
                "rationale": "Opus 5.5 leads Terminal-Bench 4.0 (67% max / 60% xhigh) and SciCode (65%).",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "codex",
                "model": codex_astra if comp == "high" else codex_sol,
                "effort": secondary_effort,
                "rationale": "Codex Astra/Sol provides cross-family worktree execution and $0.39/task Pareto efficiency.",
            }
        else:
            rank_1 = {
                "rank": 1,
                "runtime": "cc",
                "model": cc_sonnet,
                "effort": "medium" if urg == "immediate" else "high",
                "rationale": "Fast hub state summarization and witness telemetry.",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "agy",
                "model": agy_flash_high,
                "effort": "high",
                "rationale": "Low-latency high-throughput telemetry and failover proxy.",
            }
    else:
        # main_spoke_sub_hub (Sub-Hub / Main-Spoke Orchestrator & Worker Wave Coordinator)
        if cat == "agentic_coding_and_tdd":
            if comp == "high" or imp == "critical":
                rank_1 = {
                    "rank": 1,
                    "runtime": "cc",
                    "model": cc_opus,
                    "effort": high_effort,
                    "rationale": "Opus 5.5 dominates agentic coding on Terminal-Bench 4.0 (60% xhigh / 67% max) and SciCode (65%) at $3.46/task.",
                }
                rank_2 = {
                    "rank": 2,
                    "runtime": "codex",
                    "model": codex_sol if urg == "immediate" else codex_astra,
                    "effort": secondary_effort,
                    "rationale": "GPT-6.1 Sol ($0.39/task Pareto #1, 53% Non-Hallucination) / GPT-6 Astra for isolated worktree coding.",
                }
            else:
                rank_1 = {
                    "rank": 1,
                    "runtime": "codex",
                    "model": codex_sol,
                    "effort": "high",
                    "rationale": "Standard/routine spoke coding maximizes Pareto ROI ($0.39/task) and non-hallucination (53%) via GPT-6.1 Sol.",
                }
                rank_2 = {
                    "rank": 2,
                    "runtime": "agy",
                    "model": agy_argon_high,
                    "effort": "high",
                    "rationale": "Gemini 4 Argon (High) achieves 57% Terminal-Bench 4.0 and 62% SciCode at $1.99/task.",
                }
        elif cat == "browser_vla_and_automation":
            rank_1 = {
                "rank": 1,
                "runtime": "agy",
                "model": agy_argon_high if imp == "critical" or comp == "high" else agy_argon_base,
                "effort": "high",
                "rationale": "Gemini 4 Argon leads AutomationBench-AA (78% #1) for spoke browser VLA and SaaS/DOM automation.",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "muse",
                "model": muse_wonder_full if comp == "high" else muse_wonder,
                "effort": "max",
                "rationale": "Muse Wonder Full (71% AutomationBench, 33% GDP.pdf) or Muse Wonder (144 tok/s, 68% AutomationBench).",
            }
        elif cat in {"planning_architecture_synthesis", "deep_reasoning_and_research"}:
            rank_1 = {
                "rank": 1,
                "runtime": "cc",
                "model": cc_fable,
                "effort": "xhigh" if comp == "high" else "high",
                "rationale": "Sub-Hub domain decomposition and EARS spec synthesis leverage Fable 5.1 (HLE 59% xhigh / 56% high, Omniscience Accuracy 66%).",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "codex",
                "model": codex_astra,
                "effort": secondary_effort,
                "rationale": "Codex Tier-1 Astra provides independent structural DAG & epistemic verification.",
            }
        elif cat in {"adversarial_review_and_reconciliation", "execution_governance_and_audit"}:
            rank_1 = {
                "rank": 1,
                "runtime": "codex",
                "model": codex_sol if urg == "immediate" else codex_astra,
                "effort": secondary_effort,
                "rationale": "Cross-family spoke validator (when CC is composer): 53% Non-Hallucination (#1) and $0.39/task.",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "cc",
                "model": cc_opus,
                "effort": secondary_effort,
                "rationale": "Cross-family spoke validator (when Codex/AGY is composer): AA-Briefcase 1761, 41% Non-Hallucination.",
            }
        else:
            rank_1 = {
                "rank": 1,
                "runtime": "cc" if urg != "immediate" else "muse",
                "model": cc_sonnet if urg != "immediate" else muse_spark,
                "effort": "medium",
                "rationale": "Fast spoke evidence curation, CMDS wiki sync, and delivery witnessing (`sonnet_roles`).",
            }
            rank_2 = {
                "rank": 2,
                "runtime": "agy",
                "model": agy_flash_high,
                "effort": "high",
                "failover": {"runtime": "codex", "model": codex_luna, "effort": "medium"},
                "rationale": "High-speed telemetry and low-cost spoke witness fallback.",
            }

    return {
        "session_tier": s_tier,
        "task_category": cat,
        "complexity": comp,
        "urgency": urg,
        "importance": imp,
        "rank_1_primary": rank_1,
        "rank_2_counterpart": rank_2,
    }


def build_orchestrator_session_routing_table(
    *,
    registry_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Generate the complete `{Main-Hub, Main-Spoke/Sub-Hub} x {Task-Category, Complexity, Urgency, Importance}` routing table."""
    scenarios = [
        ("main_hub", "planning_architecture_synthesis", "high", "normal", "critical"),
        ("main_hub", "deep_reasoning_and_research", "high", "normal", "critical"),
        ("main_hub", "execution_governance_and_audit", "high", "normal", "critical"),
        ("main_hub", "planning_architecture_synthesis", "low", "immediate", "high"),
        ("main_spoke_sub_hub", "agentic_coding_and_tdd", "high", "normal", "critical"),
        ("main_spoke_sub_hub", "agentic_coding_and_tdd", "medium", "immediate", "normal"),
        ("main_spoke_sub_hub", "browser_vla_and_automation", "high", "normal", "critical"),
        ("main_spoke_sub_hub", "deep_reasoning_and_research", "high", "normal", "critical"),
        ("main_spoke_sub_hub", "adversarial_review_and_reconciliation", "high", "normal", "critical"),
        ("main_spoke_sub_hub", "fast_curation_and_telemetry", "low", "immediate", "normal"),
    ]
    return [
        resolve_orchestrator_session_routing(
            session_tier=st,
            task_category=tc,
            complexity=comp,
            urgency=urg,
            importance=imp,
            registry_path=registry_path,
        )
        for st, tc, comp, urg, imp in scenarios
    ]


def build_vla_wfc_mpt_hub_spoke_map(
    *,
    registry_path: Optional[Path] = None,
    seat_tier_path: Optional[Path] = None,
    wfc_policy_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build the cross-linked VLA + WFC + MPT (/deploy-cli) + Persona/Skill/Knowledge-Vault Hub-Spoke map.

    Synthesizes:
    1. VLA benchmark matrix from Artificial Analysis v4.3.2 (`aa_vla_benchmark_matrix` in `models.json`).
    2. Dual-axis cognitive tier routing (`planning_reasoning_synthesis` vs `execution_validation_coding`).
    3. Cross-linkage between `seat-model-tier.json` (`fable_roles`, `opus_roles`, `sonnet_roles`),
       WFC `task_kinds` (`orchestration-policy.json`), and MPT:N 5-Wave (`planning`, `reasoning`,
       `adversarial_triage`, `synthesizing_and_orchestrating`, `meta_evaluating`) seats.
    4. Bidirectional Knowledge-Vault Hub/Spoke and Skill pointers.
    """
    repo_root = Path(__file__).resolve().parents[2]
    for anc in Path(__file__).resolve().parents:
        if (anc / "config" / "orchestration" / "models.json").is_file():
            repo_root = anc
            break
    if registry_path is None:
        cand = repo_root / "config" / "orchestration" / "models.json"
        if cand.is_file():
            registry_path = cand
    if seat_tier_path is None:
        cand = repo_root / "config" / "runtime-hooks" / "seat-model-tier.json"
        if cand.is_file():
            seat_tier_path = cand
    if wfc_policy_path is None:
        cand = repo_root / ".agents" / "skills" / "wfc" / "references" / "orchestration-policy.json"
        if cand.is_file():
            wfc_policy_path = cand

    registry_data: Dict[str, Any] = {}
    if registry_path is not None and registry_path.is_file():
        try:
            registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            registry_data = {}

    seat_tiers: Dict[str, Any] = {}
    if seat_tier_path is not None and seat_tier_path.is_file():
        try:
            seat_tiers = json.loads(seat_tier_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            seat_tiers = {}

    wfc_policy: Dict[str, Any] = {}
    if wfc_policy_path is not None and wfc_policy_path.is_file():
        try:
            wfc_policy = json.loads(wfc_policy_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            wfc_policy = {}

    planning_3tier = resolve_canonical_three_tier_models(
        cognitive_stage="planning", registry_path=registry_path
    )
    execution_3tier = resolve_canonical_three_tier_models(
        cognitive_stage="adversarial_triage", registry_path=registry_path
    )

    fable_roles = set(seat_tiers.get("fable_roles", ["planner", "synthesizer"]))
    sonnet_roles = set(seat_tiers.get("sonnet_roles", ["curator", "witness", "metrician"]))
    opus_roles = set(
        seat_tiers.get(
            "opus_roles",
            [
                "reconciler",
                "main",
                "critic",
                "auditor",
                "validator",
                "traverser",
                "tester",
                "learner",
                "instrumenter",
                "architect",
            ],
        )
    )

    cc_plan_list = planning_3tier["cc"]["selected_models"]
    codex_list = planning_3tier["codex"]["selected_models"]
    agy_list = planning_3tier["agy"]["selected_models"]
    muse_list = planning_3tier["muse"]["selected_models"]

    persona_specs = [
        ("ptah-planner", "planner", "planning", 0, "planning", "composer", ["augi-planning", "wfc"]),
        ("mago-architect", "architect", "planning", 0, "planning", "composer", ["augi-system-design", "domain-modeling"]),
        ("nala-traverser", "traverser", "boundary", 0, "planning", "composer", ["augi-using-git-worktrees", "deploy-cli", "session-messenger"]),
        ("sejong-scholar", "scholar", "experiment", 1, "reasoning", "composer", ["augi-deconstruct", "codify-harness", "memory-vault"]),
        ("seshat-evidence-curator", "curator", "evidence-curation", 1, "reasoning", "composer", ["memory-vault", "exec-pw-cli", "hybrid-browser-control"]),
        ("chilseong-instrumenter", "instrumenter", "telemetry", 1, "reasoning", "composer", ["augi-codemap", "augi-artifact", "augi-smart-sensor"]),
        ("loki-flyter", "critic", "design-review", 2, "adversarial_triage", "validator", ["crucible", "grilling", "quarry"]),
        ("haechi-compliance-auditor", "auditor", "authority", 2, "adversarial_triage", "validator", ["augi-audit", "domain-modeling"]),
        ("heimdall-adversarial-reconciler", "reconciler", "state-reconciliation", 2, "adversarial_triage", "validator", ["converging-voyage", "augi-codemap", "augi-merge-protocol"]),
        ("sindri-crafttester", "tester", "implementation", 2, "adversarial_triage", "validator", ["augi-test-driven-development", "augi-deconstruct", "augi-feature", "augi-tdd"]),
        ("thoth-synthesizer", "synthesizer", "synthesis", 3, "synthesizing_and_orchestrating", "synthesizer", ["wfc", "converging-voyage", "domain-modeling"]),
        ("mimir-synthesizer", "synthesizer", "synthesis", 3, "synthesizing_and_orchestrating", "synthesizer", ["augi-workflow-authoring", "wfc"]),
        ("jaya-vijaya-evidence-validator", "validator", "final-validation", 4, "meta_evaluating", "meta_evaluator", ["augi-verification-before-completion", "augi-tdd", "codify-harness"]),
        ("hanuman-delivery-witness", "witness", "delivery-witness", 4, "meta_evaluating", "meta_evaluator", ["augi-finishing-a-development-branch", "session-carry", "session-close"]),
        ("sovereign-orchestrator", "main", "authority", 4, "meta_evaluating", "meta_evaluator", ["augi-receiving-code-review", "fable-mode", "wfc"]),
    ]

    wfc_task_kinds = wfc_policy.get("task_kinds", {})
    persona_matrix: List[Dict[str, Any]] = []
    for persona, short_role, wfc_kind, wave_idx, stage, mpt_role, skills in persona_specs:
        if short_role in fable_roles or short_role == "scholar":
            cc_model = cc_plan_list[0]
            codex_model = codex_list[0]
            agy_model = agy_list[0]
            muse_model = muse_list[0]
            tier_bucket = "tier_1_reasoning_planning (fable_roles)"
        elif short_role in sonnet_roles:
            cc_model = cc_plan_list[2]
            codex_model = codex_list[2]
            agy_model = agy_list[2]
            muse_model = muse_list[2]
            tier_bucket = "tier_3_fast_curation (sonnet_roles)"
        else:
            cc_model = cc_plan_list[1]
            codex_model = codex_list[1] if stage in {"adversarial_triage", "meta_evaluating"} else codex_list[0]
            agy_model = agy_list[0] if short_role in opus_roles else agy_list[1]
            muse_model = muse_list[0] if short_role in {"validator", "critic", "reconciler"} else muse_list[1]
            tier_bucket = "tier_1_execution_validation (opus_roles)"

        wfc_entry = wfc_task_kinds.get(wfc_kind, {})
        persona_matrix.append(
            {
                "persona": persona,
                "short_role": short_role,
                "seat_model_tier_bucket": tier_bucket,
                "wfc_task_kind": wfc_kind,
                "wfc_surface": wfc_entry.get("surface", wfc_kind),
                "mpt_wave": wave_idx,
                "mpt_cognitive_stage": stage,
                "mpt_role_tier": mpt_role,
                "governing_skills": skills,
                "recommended_models_by_runtime": {
                    "cc": cc_model,
                    "codex": codex_model,
                    "agy": agy_model,
                    "muse": muse_model,
                },
            }
        )

    return {
        "schema_version": "patchwork-vla-wfc-mpt-hub-spoke-v1",
        "vla_evidence": registry_data.get("aa_vla_benchmark_matrix", {}),
        "canonical_three_tier_models": {
            rt: info["selected_models"] for rt, info in planning_3tier.items()
        },
        "cognitive_axis_routing": {
            "planning_reasoning_synthesis": {
                rt: info["selected_models"] for rt, info in planning_3tier.items()
            },
            "execution_validation_coding": {
                rt: info["selected_models"] for rt, info in execution_3tier.items()
            },
        },
        "orchestrator_session_routing_table": build_orchestrator_session_routing_table(
            registry_path=registry_path
        ),
        "wfc_mpt_persona_skill_matrix": persona_matrix,
        "hub_spoke_interlinks": {
            "memory_vault_hub": [
                "C:/Knowledge-Vault/index.md",
                "C:/Knowledge-Vault/hot.md",
            ],
            "memory_vault_spokes": [
                "C:/Knowledge-Vault/projects/upstream-agentic-os/aa-vla-model-matrix-and-wfc-mpt-hub-spoke-2026-10-24.md",
                "C:/Knowledge-Vault/projects/upstream-agentic-os/opensource-patchwork-os-synthesis-2026-10-19.md",
            ],
            "patchwork_os_generalized_skills": [
                "skills/pwos-grilling/SKILL.md",
                "skills/pwos-quarry/SKILL.md",
                "skills/pwos-deconstruct/SKILL.md",
                "skills/pwos-persona-agent/SKILL.md",
                "skills/pwos-crucible/SKILL.md",
                "skills/pwos-systematic-debugging/SKILL.md",
                "skills/pwos-tdd/SKILL.md",
                "skills/pwos-stdd/SKILL.md",
                "skills/pwos-fable-mode/SKILL.md",
                "skills/pwos-wfc/SKILL.md",
                "skills/pwos-deploy-cli/SKILL.md",
                "skills/pwos-rea/SKILL.md",
            ],
            "governing_skills": [
                ".agents/skills/hybrid-browser-control/SKILL.md",
                ".agents/skills/exec-pw-cli/SKILL.md",
                ".agents/skills/wfc/SKILL.md",
                ".agents/skills/deploy-cli/SKILL.md",
                ".agents/skills/persona-agents/SKILL.md",
                ".agents/skills/memory-vault/SKILL.md",
            ],
            "orchestrators": [
                "scripts/control/mptN_meta_prompt_orchestrator.py",
                ".agents/skills/wfc/scripts/wfc_cli.py",
                "knowledge/satellites/patchwork-os/src/patchwork_os/hub_spoke_gate.py",
                "knowledge/satellites/patchwork-os/src/patchwork_os/persona_setup.py",
                "knowledge/satellites/patchwork-os/src/patchwork_os/deploy_cli.py",
            ],
        },
    }
