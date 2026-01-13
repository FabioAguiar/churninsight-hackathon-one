"""
Internal contract loader + payload transformer for ChurnInsight FastAPI.

Context
-------
ChurnInsight uses a stable *external* API contract (8 fields) validated by the
Java Spring Boot layer.

The Python FastAPI service acts as an explicit bridge between:
- the external contract (8 fields), and
- the internal model features declared in `contracts/bank_churn.yaml`.

This module is intentionally:
- explicit (no "magic" mappings)
- audit-friendly (YAML is the single source of truth)
- minimal (MVP / Demo Day oriented)

Public API
---------
- get_internal_contract(): dict
- transform_api_payload_to_model_features(payload: dict, contract: dict) -> pandas.DataFrame
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import yaml

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# Optional env var override (kept simple for MVP)
ENV_INTERNAL_CONTRACT_PATH = "INTERNAL_CONTRACT_PATH"

# Default relative path (resolved against project root)
DEFAULT_INTERNAL_CONTRACT_RELATIVE = Path("contracts/bank_churn.yaml")

# ---------------------------------------------------------------------
# Internal cache (singleton)
# ---------------------------------------------------------------------

_internal_contract: Dict[str, Any] | None = None


def _project_root() -> Path:
    """
    Resolve the project root directory.

    This file lives at: <root>/src/api_python/internal_contract.py
    """
    return Path(__file__).resolve().parents[2]


def _resolve_contract_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p

    # Prefer project-root resolution for robustness in docker / uvicorn cwd differences.
    root = _project_root()
    candidate = root / p
    if candidate.exists():
        return candidate

    # Fallback to current working directory.
    return p.resolve()


def load_internal_contract(path: str | Path | None = None) -> Dict[str, Any]:
    """
    Load the internal contract YAML as a plain dict.

    Notes
    -----
    This function performs only *minimal* validation needed for inference,
    since the main purpose is to keep the bridge pragmatic and explicit.
    """
    if path is None:
        path = os.getenv(ENV_INTERNAL_CONTRACT_PATH) or DEFAULT_INTERNAL_CONTRACT_RELATIVE

    contract_path = _resolve_contract_path(path)

    if not contract_path.exists():
        raise FileNotFoundError(
            f"Internal contract file not found: {contract_path} "
            f"(set {ENV_INTERNAL_CONTRACT_PATH} to override)"
        )

    try:
        data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to read/parse internal contract YAML: {contract_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise TypeError("Internal contract YAML root must be a mapping/dict.")

    # Minimal schema validation
    schema = data.get("schema", {})
    mapping = data.get("mapping", {})
    defaults = data.get("defaults", {})

    if not isinstance(schema, dict) or "model_features" not in schema:
        raise ValueError("Internal contract must define schema.model_features (list).")
    if not isinstance(schema["model_features"], list) or not schema["model_features"]:
        raise ValueError("schema.model_features must be a non-empty list.")
    if not isinstance(mapping, dict) or "api_to_model" not in mapping:
        raise ValueError("Internal contract must define mapping.api_to_model (dict).")
    if not isinstance(mapping["api_to_model"], dict) or not mapping["api_to_model"]:
        raise ValueError("mapping.api_to_model must be a non-empty dict.")
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise ValueError("defaults must be a dict when present.")

    return data


def get_internal_contract() -> Dict[str, Any]:
    """
    Return the cached internal contract (load once).
    """
    global _internal_contract
    if _internal_contract is None:
        _internal_contract = load_internal_contract()
    return _internal_contract


# ---------------------------------------------------------------------
# Transformation (external payload -> internal model features)
# ---------------------------------------------------------------------

_TYPE_CASTS = {
    "tenure": int,
    "active_member": int,
    "credit_card": int,
    "products_number": int,
    "credit_score": int,
    "estimated_salary": float,
}


def _safe_cast(value: Any, cast_fn):
    if value is None:
        return None
    try:
        # Avoid int("89.5") ValueError by passing through float first when needed.
        if cast_fn is int and isinstance(value, str) and value.strip() != "":
            return int(float(value))
        return cast_fn(value)
    except Exception:
        return None


def transform_api_payload_to_model_features(payload: Dict[str, Any], contract: Dict[str, Any]) -> pd.DataFrame:
    """
    Transform the external API payload (8 fields) into a 1-row DataFrame matching the model features.

    The mapping behavior is governed by `contracts/bank_churn.yaml`:

    Supported mapping types
    -----------------------
    - direct: passthrough value
    - yes_no_to_binary: map using a dict like {"Yes": 1, "No": 0}
    - rule: map using rules dict with explicit fallback
    - default: resolve from contract.defaults (kept for compatibility; not fed to the model)

    Important
    ---------
    The internal model may have fewer (or different) features than the external payload.
    Only `schema.model_features` are included in the returned DataFrame, in the declared order.

    Collisions (two external fields -> same internal feature)
    --------------------------------------------------------
    In this project, `online_security` and `tech_support` both map to `active_member`.
    When multiple sources map to the same feature:
    - if both are numeric, the max() is taken (so any "Yes" => 1).
    This is a pragmatic, robust rule for the MVP.
    """
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict")

    schema = contract["schema"]
    model_features = list(schema["model_features"])
    mapping = contract["mapping"]["api_to_model"]
    defaults = contract.get("defaults", {}) or {}

    feature_values: Dict[str, Any] = {}
    _resolved_defaults: Dict[str, Any] = {}

    for api_field, spec in mapping.items():
        if not isinstance(spec, dict):
            continue

        mtype = spec.get("type")
        to_feature = spec.get("to_feature")

        raw_value = payload.get(api_field)

        if mtype == "direct":
            if to_feature:
                feature_values[to_feature] = raw_value

        elif mtype == "yes_no_to_binary":
            if not to_feature:
                continue
            m = spec.get("mapping", {}) or {}
            fallback = spec.get("fallback", m.get("No", 0))
            mapped = m.get(raw_value, fallback)

            # Collision strategy: keep max for numeric/binary values
            if to_feature in feature_values and isinstance(feature_values[to_feature], (int, float)) and isinstance(mapped, (int, float)):
                feature_values[to_feature] = max(feature_values[to_feature], mapped)
            else:
                feature_values[to_feature] = mapped

        elif mtype == "rule":
            if not to_feature:
                continue
            rules = spec.get("rules", {}) or {}
            fallback = spec.get("fallback", None)
            feature_values[to_feature] = rules.get(raw_value, fallback)

        elif mtype == "default":
            # Defaults are kept to satisfy the external interface contract,
            # but they do NOT feed the internal model features.
            key = spec.get("value_from_defaults")
            if key is not None:
                _resolved_defaults[api_field] = defaults.get(key)

        else:
            # Unknown mapping type: ignore (MVP robustness)
            continue

    # Build row in the declared order, coercing types where possible.
    row: Dict[str, Any] = {}
    for feat in model_features:
        val = feature_values.get(feat)

        cast_fn = _TYPE_CASTS.get(feat)
        if cast_fn is not None:
            val = _safe_cast(val, cast_fn)

        # Pragmatic fallback: keep pipeline running even if a feature is missing.
        # If the internal contract doesn't provide a mapping for a required model feature,
        # we default to 0 (or 0.0) after casting.
        if val is None:
            val = 0.0 if cast_fn is float else 0

        row[feat] = val

    df = pd.DataFrame([row], columns=model_features)
    return df
