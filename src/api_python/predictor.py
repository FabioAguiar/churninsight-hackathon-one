# Predictor module for ChurnInsight FastAPI service
#
# Responsible for:
# - transforming validated input data into model-ready format
# - applying the official preprocessing mapping (contract -> training schema)
# - running model inference
# - returning prediction label and probability
#
# This module contains NO FastAPI code.
# It is pure business logic and can be reused by other services or scripts.

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from src.features.preprocess import preprocess_input
from src.api_python.model_loader import get_model
from src.api_python.schemas import PredictRequest


# -----------------------------
# Internal helpers
# -----------------------------

def _extract_positive_proba(model: Any, X) -> float:
    """
    Extract the probability of the positive class (churn=1) in a robust way.

    - Standard sklearn classifiers return shape (n_samples, n_classes).
    - Some flows may return shape (n_samples,) or even scalar.

    This function normalizes these cases and always returns a float.
    """
    proba = model.predict_proba(X)

    # If it's already a scalar
    if np.isscalar(proba):
        return float(proba)

    proba = np.asarray(proba)

    # Typical sklearn: (n_samples, 2) => take first sample, class=1
    if proba.ndim == 2 and proba.shape[1] >= 2:
        return float(proba[0, 1])

    # Some models/pipelines: (n_samples,) => assume it's positive-class probability
    if proba.ndim == 1 and proba.shape[0] >= 1:
        return float(proba[0])

    raise ValueError(f"Unexpected predict_proba output: ndim={proba.ndim}, shape={proba.shape}")


# -----------------------------
# Public API
# -----------------------------

def predict_churn(payload: PredictRequest) -> Tuple[str, float]:
    """
    Run churn prediction for a single customer.

    Args:
        payload: Validated PredictRequest object.

    Returns:
        Tuple[str, float]:
            - prediction label ("Vai cancelar" | "Vai continuar")
            - probability of churn (positive class) as float (0..1)
              (NOTE: this is returned rounded to 2 decimals for demo friendliness)
    """
    # Convert Pydantic model to plain json (enums -> values, etc.)
    input_dict: Dict = payload.model_dump(mode="json")

    # Apply official preprocessing/mapping (contract -> training schema)
    X = preprocess_input(input_dict)

    # Get loaded model (pipeline)
    model = get_model()

    # Run inference
    proba_raw = _extract_positive_proba(model, X)

    # Business-friendly label based on the raw probability (avoid rounding edge cases)
    prediction_label = "Vai cancelar" if proba_raw >= 0.5 else "Vai continuar"

    # Round only for output (demo/UI)
    churn_probability = round(float(proba_raw), 2)

    return prediction_label, churn_probability


# -----------------------------
# Optional helpers
# -----------------------------

def predict_raw(input_data: Dict) -> Dict:
    """
    Lower-level prediction helper.

    Useful for:
    - quick testing
    - batch prediction experiments
    - internal scripts

    Args:
        input_data: Dictionary with raw input fields (same as API payload keys).

    Returns:
        Dict with prediction and rounded probability.
    """
    X = preprocess_input(input_data)
    model = get_model()

    proba_raw = _extract_positive_proba(model, X)
    label = "Vai cancelar" if proba_raw >= 0.5 else "Vai continuar"

    return {
        "previsao": label,
        "probabilidade": round(float(proba_raw), 2),
    }
