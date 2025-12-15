# Model loader for ChurnInsight FastAPI service
#
# Responsible for:
# - loading the trained ML model from disk
# - keeping a singleton instance in memory
# - exposing helper methods for health checks
#
# This module is intentionally simple and explicit, to be easily understood
# by beginners and safe to use in production-like scenarios.

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import joblib

# -----------------------------
# Configuration
# -----------------------------

DEFAULT_MODEL_PATH = Path('artifacts/churn_model.joblib')
MODEL_VERSION = os.getenv('MODEL_VERSION', None)

# -----------------------------
# Internal state (singleton)
# -----------------------------

_model: Optional[Any] = None

# -----------------------------
# Public API
# -----------------------------

def load_model(model_path: Path | str = DEFAULT_MODEL_PATH) -> Any:
    global _model
    if _model is not None:
        return _model

    try:
        loaded_obj = joblib.load(model_path)

        # Caso o modelo tenha sido salvo dentro de um dict
        if isinstance(loaded_obj, dict):
            if "model" in loaded_obj:
                _model = loaded_obj["model"]
            else:
                raise RuntimeError(
                    "Loaded object is a dict but does not contain a 'model' key."
                )
        else:
            _model = loaded_obj

    except Exception as exc:
        raise RuntimeError(
            f"Failed to load model from {model_path.resolve()}: {exc}"
        ) from exc


    return _model

def get_model() -> Any:
    if _model is None:
        raise RuntimeError('Model is not loaded. Call load_model() during application startup.')
    return _model

def is_model_loaded() -> bool:
    return _model is not None

def get_model_version() -> Optional[str]:
    return MODEL_VERSION
