# SPDX-License-Identifier: Apache-2.0
"""Canonical 3-Layer Configuration Precedence Engine for Patchwork-OS CLI Tools.

Enforces the extensible 3-Layer Configuration Contract across every CLI script:
1. ``config.json`` (``--config-json <path>``):
   Organizational, compliance-regime (Commercial, GitHub Enterprise, ITAR/EAR
   AWS GovCloud Bedrock, ITAR/EAR GCP Vertex AI Assured Workloads, Air-Gapped),
   cloud-backend, runtime-harness, and skill-prefix baseline configuration.
2. ``input.json`` (``--input-json <path>``):
   Task, session-tier, brainstorming elicitation, or workload-specific input
   payload that overlays ``config.json``.
3. ``Manual Keyword Arguments`` (``--set key=value`` / explicit CLI flags):
   Targeted manual overrides for 1, 2, or more specific parameters (supporting
   nested dotted paths such as ``--set compliance_regime=itar_ear_aws_govcloud``
   or ``--set routing.urgency=immediate``) that take highest precedence without
   requiring edits to ``config.json`` or ``input.json``.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


def _deep_merge(base: Dict[str, Any], overlay: Mapping[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``overlay`` into a copy of ``base`` without mutating inputs."""
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def parse_scalar_or_json_value(raw: str) -> Any:
    """Parse a manual CLI ``key=value`` value into bool, int, float, JSON list/dict, or str."""
    text = raw.strip()
    if not text:
        return ""
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"null", "none"}:
        return None
    if text[0] in {"[", "{", '"'}:
        try:
            return json.loads(text)
        except ValueError:
            pass
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        pass
    if "," in text and not (" " in text and not text.startswith("[")):
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) > 1:
            return parts
    return text


def apply_dotted_override(target: Dict[str, Any], key_path: str, value: Any) -> None:
    """Apply a dotted key path (e.g. ``compliance.regime``) into ``target`` in-place."""
    parts = [p.strip() for p in key_path.split(".") if p.strip()]
    if not parts:
        raise ValueError("Override key path must be non-empty")
    cursor: Dict[str, Any] = target
    for part in parts[:-1]:
        existing = cursor.get(part)
        if not isinstance(existing, dict):
            existing = {}
            cursor[part] = existing
        cursor = existing
    cursor[parts[-1]] = value


def parse_manual_kv_pairs(pairs: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Parse ``['key=val', 'nested.key=val2']`` into a nested dictionary."""
    result: Dict[str, Any] = {}
    if not pairs:
        return result
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Manual override must be in 'key=value' format, got: {item!r}")
        k, v = item.split("=", 1)
        key_clean = k.strip()
        if not key_clean:
            raise ValueError(f"Manual override key cannot be empty: {item!r}")
        apply_dotted_override(result, key_clean, parse_scalar_or_json_value(v))
    return result


def load_layered_config(
    *,
    defaults: Optional[Mapping[str, Any]] = None,
    config_json: Optional[Path | str | Mapping[str, Any]] = None,
    input_json: Optional[Path | str | Mapping[str, Any]] = None,
    manual_set_pairs: Optional[Sequence[str]] = None,
    manual_kwargs: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Resolve the 3-Layer Configuration Precedence (`defaults < config.json < input.json < manual kwargs`)."""
    resolved: Dict[str, Any] = copy.deepcopy(dict(defaults)) if defaults else {}
    sources_applied: List[str] = ["defaults"] if defaults else []

    def _read_layer(layer: Optional[Path | str | Mapping[str, Any]], label: str) -> Dict[str, Any]:
        if layer is None:
            return {}
        if isinstance(layer, Mapping):
            sources_applied.append(f"{label}:inline_dict")
            return dict(layer)
        p = Path(layer)
        if not p.is_file():
            raise FileNotFoundError(f"{label} file not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{label} root must be a JSON object: {p}")
        sources_applied.append(f"{label}:{p.as_posix()}")
        return data

    cfg_layer = _read_layer(config_json, "config_json")
    if cfg_layer:
        resolved = _deep_merge(resolved, cfg_layer)

    inp_layer = _read_layer(input_json, "input_json")
    if inp_layer:
        resolved = _deep_merge(resolved, inp_layer)

    kv_layer = parse_manual_kv_pairs(manual_set_pairs)
    if kv_layer:
        resolved = _deep_merge(resolved, kv_layer)
        sources_applied.append(f"manual_set:{len(manual_set_pairs or ())}B")

    if manual_kwargs:
        filtered_kwargs: Dict[str, Any] = {}
        for k, v in manual_kwargs.items():
            if v is not None:
                apply_dotted_override(filtered_kwargs, k, v)
        if filtered_kwargs:
            resolved = _deep_merge(resolved, filtered_kwargs)
            sources_applied.append(f"manual_kwargs:{sorted(filtered_kwargs.keys())}")

    resolved["_config_provenance"] = {
        "precedence_order": [
            "defaults",
            "config_json",
            "input_json",
            "manual_set_pairs",
            "manual_kwargs",
        ],
        "sources_applied": sources_applied,
    }
    return resolved


def add_three_layer_cli_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach canonical ``--config-json``, ``--input-json``, and ``--set key=value`` flags to a CLI parser."""
    parser.add_argument(
        "--config-json",
        dest="config_json",
        type=str,
        default=None,
        help="Layer 1 baseline config.json path (organization, compliance regime, cloud & runtime catalog).",
    )
    parser.add_argument(
        "--input-json",
        dest="input_json",
        type=str,
        default=None,
        help="Layer 2 task/session input.json path overlaying config.json.",
    )
    parser.add_argument(
        "--set",
        "--override",
        dest="manual_set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Layer 3 manual keyword override (supports dotted paths e.g. --set compliance_regime=itar_ear_aws_govcloud). Repeatable.",
    )
    return parser
