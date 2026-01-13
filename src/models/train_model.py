# src/models/train_model.py
"""
ChurnInsight — Seção 8 (N1)
Treino e busca de hiperparâmetros (core)

Escopo:
- ✔️ treino simples
- ✔️ GridSearchCV (grids default)
- ❌ sem calibração, sem threshold tuning, sem ensembles
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, recall_score, f1_score, precision_score, accuracy_score


@dataclass(frozen=True)
class TrainingDecision:
    positive_label: int
    primary_metric: str
    secondary_metrics: Tuple[str, ...]
    random_state: int = 42


def _build_scorers(dec: TrainingDecision) -> Dict[str, Any]:
    pos_label = int(dec.positive_label)

    scorers: Dict[str, Any] = {
        "accuracy": make_scorer(accuracy_score),
        "precision": make_scorer(precision_score, average="binary", pos_label=pos_label, zero_division=0),
        "recall": make_scorer(recall_score, average="binary", pos_label=pos_label, zero_division=0),
        "f1": make_scorer(f1_score, average="binary", pos_label=pos_label, zero_division=0),
    }
    return scorers


def train_simple(
    estimator: BaseEstimator,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Mapping[str, Any],
) -> Tuple[BaseEstimator, Dict[str, Any]]:
    t0 = time.perf_counter()
    model = estimator.set_params(**dict(params))
    model.fit(X_train, y_train)
    t1 = time.perf_counter()
    return model, {"fit_time_s": float(t1 - t0)}


def train_with_grid_search(
    estimator: BaseEstimator,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    grid: Mapping[str, Any],
    decision: TrainingDecision,
    cv: int = 5,
    n_jobs: int = -1,
    verbose: int = 0,
) -> Tuple[BaseEstimator, Dict[str, Any]]:
    scorers = _build_scorers(decision)

    if decision.primary_metric not in scorers:
        raise ValueError(f"primary_metric inválida para S8: {decision.primary_metric}")

    t0 = time.perf_counter()
    gs = GridSearchCV(
        estimator=estimator,
        param_grid=dict(grid),
        scoring=scorers,
        refit=decision.primary_metric,
        cv=cv,
        n_jobs=n_jobs,
        verbose=verbose,
        return_train_score=False,
    )
    gs.fit(X_train, y_train)
    t1 = time.perf_counter()

    best_model = gs.best_estimator_
    meta = {
        "search_time_s": float(t1 - t0),
        "best_params": dict(gs.best_params_),
        "best_score_primary": float(gs.best_score_),
        "cv_results_summary": {
            "n_splits": int(cv),
            "n_candidates": int(len(gs.cv_results_.get("params", []))),
        },
    }
    return best_model, meta
