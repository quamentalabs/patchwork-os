# SPDX-License-Identifier: MIT
"""Dispatch-plan and completion-contract utilities for Patchwork-OS.

Plans describe runtime and child-result lease paths; they do not launch seats,
acquire leases or locks, or authenticate results. There is no runnable dispatcher
CLI in this module. Hashes describe bytes rather than signatures or approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
import uuid

from .hub_spoke_gate import resolve_canonical_three_tier_models

SUPPORTED_DEPLOY_RUNTIMES: tuple[str, ...] = ("cc", "codex", "agy", "muse")
SUPPORTED_DEPLOY_SURFACES: tuple[str, ...] = ("cli", "ide", "desktop_app")
SUPPORTED_EFFORT_LEVELS: tuple[str, ...] = ("max", "xhigh", "high", "medium", "low")


def verify_parent_child_lease_isolation(
    *,
    owner_session: str,
    parent_claimed_paths: Sequence[str],
) -> Dict[str, Any]:
    """Verify that the parent `owner_session` does not claim child result lease prefixes.

    In `--inter-cli`, each child seat claims `.scratch/session-state/<owner_session>/tasks/<run_id>/...`.
    If the parent claims `.scratch/session-state/<owner_session>` or `.../tasks`, child acquisition
    fails with `RESULT_LEASE_REFUSED`.
    """
    owner = owner_session.strip()
    if not owner:
        raise ValueError("owner_session must be non-empty")

    forbidden_exact_or_prefix = (
        f".scratch/session-state/{owner}",
        f".scratch/session-state/{owner}/tasks",
    )
    violations: List[str] = []
    for raw_path in parent_claimed_paths:
        norm = str(raw_path).replace("\\", "/").rstrip("/")
        for forbidden in forbidden_exact_or_prefix:
            if norm.endswith(forbidden) or f"{forbidden}/" in norm:
                violations.append(raw_path)
                break

    return {
        "valid": len(violations) == 0,
        "owner_session": owner,
        "violations": violations,
        "reason": "OK" if not violations else "RESULT_LEASE_REFUSED:ParentClaimedChildTasksPrefix",
    }


def plan_inter_cli_dispatch(
    *,
    owner_session: str,
    run_id: str,
    target_runtime: str,
    task_path: Path,
    workspace_root: Path,
    persona_path: Optional[Path] = None,
    skill_name: Optional[str] = None,
    model_override: Optional[str] = None,
    cognitive_stage: Optional[str] = None,
    tier_index: int = 0,
    effort: str = "xhigh",
    surface: str = "cli",
    host: str = "agnostic",
    dry_run: bool = True,
    registry_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Describe a dispatch plan; only dry_run=True is supported.

    launch_argv is a descriptive compatibility template, not an executable CLI.
    No process, lease, lock, run directory or result directory is created.
    """
    if dry_run is not True:
        raise NotImplementedError(
            "plan_inter_cli_dispatch supports dry_run=True only; "
            "live execution is not implemented"
        )
    runtime = target_runtime.strip().lower()
    if runtime not in SUPPORTED_DEPLOY_RUNTIMES:
        raise ValueError(f"Unsupported target_runtime: {target_runtime!r}")
    if surface not in SUPPORTED_DEPLOY_SURFACES:
        raise ValueError(f"Unsupported surface: {surface!r}")
    if effort not in SUPPORTED_EFFORT_LEVELS:
        raise ValueError(f"Unsupported effort level: {effort!r}")
    if not owner_session.strip() or not run_id.strip():
        raise ValueError("owner_session and run_id must be non-empty")

    ws_root = Path(workspace_root).resolve()
    t_path = Path(task_path).resolve()
    if not t_path.exists():
        raise FileNotFoundError(f"task_path does not exist: {t_path}")
    if not t_path.is_file():
        raise ValueError(f"task_path must be a regular file: {t_path}")
    task_bytes = t_path.read_bytes()
    task_sha256 = hashlib.sha256(task_bytes).hexdigest()

    models_3tier = resolve_canonical_three_tier_models(
        cognitive_stage=cognitive_stage,
        registry_path=registry_path,
    )
    selected_list = models_3tier[runtime]["selected_models"]
    clamped_idx = max(0, min(tier_index, len(selected_list) - 1))
    resolved_model = (
        model_override.strip()
        if model_override and model_override.strip() and model_override.strip() != "default"
        else selected_list[clamped_idx]
    )

    child_session = f"child-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{owner_session}:{run_id}')}"
    result_dir = ws_root / ".scratch" / "session-state" / owner_session / "tasks" / run_id
    run_dir = ws_root / ".scratch" / "deploy2" / owner_session / "runs" / run_id

    notes: List[str] = []
    if skill_name and skill_name.strip():
        notes.append(f"SKILL_BY_POINTER:{skill_name.strip()}")

    prompt_payload = json.dumps(
        {
            "run_id": run_id,
            "target": runtime,
            "model": resolved_model,
            "effort": effort,
            "surface": surface,
            "task_sha256": task_sha256,
            "persona_path": persona_path.as_posix() if persona_path else None,
            "skill": skill_name,
        },
        sort_keys=True,
    )
    first_prompt_sha256 = hashlib.sha256(prompt_payload.encode("utf-8")).hexdigest()

    argv: List[str] = [
        "python",
        "-X",
        "utf8",
        "-B",
        "-m",
        "patchwork_os.deploy_cli",
        "run",
        "--inter-cli",
        "--owner-session",
        owner_session,
        "--repo-root",
        ws_root.as_posix(),
        "--target",
        runtime,
        "--model",
        resolved_model,
        "--effort",
        effort,
        "--surface",
        surface,
        "--task",
        t_path.as_posix(),
        "--workspace",
        ws_root.as_posix(),
        "--run-id",
        run_id,
    ]
    if persona_path is not None:
        argv.extend(["--persona", Path(persona_path).resolve().as_posix()])
    if skill_name:
        argv.extend(["--skill", skill_name])
    if dry_run:
        argv.append("--dry-run")

    return {
        "kind": "deploy2-cli-plan",
        "execution_supported": False,
        "command": "run",
        "dry_run": dry_run,
        "host": host,
        "surface": surface,
        "run_id": run_id,
        "owner_session": owner_session,
        "child_session": child_session,
        "target": runtime,
        "model": resolved_model,
        "effort": effort,
        "persona_path": Path(persona_path).resolve().as_posix() if persona_path else None,
        "skill": skill_name,
        "notes": notes,
        "task": {
            "path": t_path.as_posix(),
            "sha256": task_sha256,
        },
        "first_prompt": {
            "sha256": first_prompt_sha256,
        },
        "first_prompt_sha256": first_prompt_sha256,
        "run_dir": run_dir.as_posix(),
        "result_dir": result_dir.as_posix(),
        "result_lease": {
            "child_session": child_session,
            "claimed_paths": [
                (result_dir / "task_result.md").as_posix(),
                (result_dir / "done.json").as_posix(),
            ],
        },
        "answer_contract_required": True,
        "launch_argv": argv,
        "runtime_acceptance": "not_run",
    }


def verify_inter_cli_completion_contract(
    *,
    result_dir: Path,
    preimage_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """Check recorded SHA-256 consistency, status and optional preimage change.

    A valid result is not a signature, sender authentication, native execution
    observation, authority grant or independent approval.
    """
    r_dir = Path(result_dir).resolve()
    done_path = r_dir / "done.json"
    answer_path = r_dir / "task_result.md"

    if not done_path.is_file():
        return {"valid": False, "reason": "DONE_ABSENT"}
    if not answer_path.is_file():
        return {"valid": False, "reason": "TASK_RESULT_ABSENT"}

    try:
        done_data = json.loads(done_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"valid": False, "reason": "DONE_MALFORMED"}

    if done_data.get("status") != "completed":
        return {"valid": False, "reason": "STATUS_NOT_COMPLETED"}

    answer_bytes = answer_path.read_bytes()
    actual_sha = f"sha256:{hashlib.sha256(answer_bytes).hexdigest()}"
    if preimage_sha256 and actual_sha == preimage_sha256:
        return {"valid": False, "reason": "ANSWER_UNEDITED_PREIMAGE"}

    artifacts = done_data.get("artifacts", [])
    matched_artifact = any(
        isinstance(a, Mapping)
        and str(a.get("path", "")).endswith("task_result.md")
        and a.get("sha256") in {actual_sha, actual_sha.removeprefix("sha256:")}
        for a in artifacts
    )
    if not matched_artifact:
        return {"valid": False, "reason": "ARTIFACT_SHA256_MISMATCH"}

    return {
        "valid": True,
        "reason": "VERIFIED",
        "answer_path": answer_path.as_posix(),
        "answer_sha256": actual_sha,
        "size_bytes": len(answer_bytes),
    }
