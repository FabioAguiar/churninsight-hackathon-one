# -*- coding: utf-8 -*-
"""
utils_data_definitivo.py — Utilitários de Data Science (Notebook Individual)

Este módulo concentra rotinas de avaliação pós-dump (Pipeline joblib),
plots (Matriz de Confusão, ROC e PR) e análise de threshold.
Inclui também um helper opcional para montar leaderboard a partir de um diretório
de modelos joblib (caso você persista artefatos intermediários no notebook).

Compatível com o ChurnInsight (banco):
- artifacts/churn_model.joblib (Pipeline completo: preprocess + model)
- matplotlib (sem seaborn)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import joblib

from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    PrecisionRecallDisplay,
    classification_report,
)

# =============================================================================
# Carregamento
# =============================================================================

def load_pipeline_joblib(model_path: Union[str, Path]) -> Pipeline:
    """Carrega um Pipeline salvo via joblib (preprocess + model)."""
    model_path = Path(model_path)
    obj = joblib.load(model_path)
    if not isinstance(obj, Pipeline):
        raise TypeError(f"Esperado sklearn.pipeline.Pipeline em '{model_path}', mas veio: {type(obj)}.")
    return obj

# =============================================================================
# Features esperadas pelo pipeline
# =============================================================================

def expected_features_from_pipeline(pipeline: Pipeline) -> Optional[List[str]]:
    """Tenta inferir as colunas esperadas antes do preprocess."""
    preprocess = pipeline.named_steps.get("preprocess")
    if preprocess is None:
        return None
    names = getattr(preprocess, "feature_names_in_", None)
    if names is not None:
        return list(names)
    names2 = getattr(pipeline, "feature_names_in_", None)
    if names2 is not None:
        return list(names2)
    return None


def check_features(X: pd.DataFrame, expected: Sequence[str]) -> Dict[str, Any]:
    """Retorna faltantes/extras/ordem para depuração rápida."""
    x_cols = list(X.columns)
    exp = list(expected)
    missing = sorted(list(set(exp) - set(x_cols)))
    extra = sorted(list(set(x_cols) - set(exp)))
    return {
        "missing": missing,
        "extra": extra,
        "ordered_ok": (x_cols == exp),
        "expected": exp,
        "got": x_cols,
    }


def align_columns(X: pd.DataFrame, expected: Sequence[str]) -> pd.DataFrame:
    """Reordena e remove extras; falha se faltar coluna esperada."""
    expected = list(expected)
    missing = [c for c in expected if c not in X.columns]
    if missing:
        raise ValueError(f"X está sem colunas esperadas pelo pipeline: {missing}")
    return X.loc[:, expected].copy()

# =============================================================================
# Métricas e plots
# =============================================================================

def _proba_pos(pipeline: Pipeline, X: pd.DataFrame) -> Optional[np.ndarray]:
    """Retorna P(y=1) se houver predict_proba."""
    if hasattr(pipeline, "predict_proba"):
        proba = pipeline.predict_proba(X)
        if isinstance(proba, np.ndarray) and proba.ndim == 2 and proba.shape[1] >= 2:
            return proba[:, 1]
    return None


def compute_metrics_binary(
    y_true: Union[pd.Series, np.ndarray],
    y_pred: Union[pd.Series, np.ndarray],
    y_proba: Optional[np.ndarray] = None,
) -> Dict[str, Optional[float]]:
    """Métricas padrão para churn (binário)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    out: Dict[str, Optional[float]] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": None,
        "avg_precision": None,
    }

    if y_proba is not None:
        try:
            out["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except Exception:
            out["roc_auc"] = None
        try:
            out["avg_precision"] = float(average_precision_score(y_true, y_proba))
        except Exception:
            out["avg_precision"] = None

    return out


def plot_confusion(y_true, y_pred, title: str = "Confusion Matrix") -> np.ndarray:
    """Plota matriz de confusão."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots()
    ConfusionMatrixDisplay(confusion_matrix=cm).plot(ax=ax)
    ax.set_title(title)
    plt.show()
    return cm


def plot_roc_pr(y_true, y_proba, title_prefix: str = "") -> None:
    """Plota ROC e Precision-Recall."""
    fig1, ax1 = plt.subplots()
    RocCurveDisplay.from_predictions(y_true, y_proba, ax=ax1)
    ax1.set_title((title_prefix + "ROC Curve").strip())
    plt.show()

    fig2, ax2 = plt.subplots()
    PrecisionRecallDisplay.from_predictions(y_true, y_proba, ax=ax2)
    ax2.set_title((title_prefix + "Precision-Recall Curve").strip())
    plt.show()

# =============================================================================
# Pós-dump (pipeline final)
# =============================================================================

def post_dump_evaluate_pipeline(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: Union[pd.Series, np.ndarray],
    threshold: float = 0.5,
    title: str = "Pós-dump — Avaliação do Pipeline (joblib)",
    verbose: bool = True,
    enforce_expected_columns: bool = True,
) -> Dict[str, Any]:
    """Avalia o Pipeline final salvo em joblib e gera plots essenciais."""
    X_eval = X_test

    expected = expected_features_from_pipeline(pipeline)
    feature_check = None
    if enforce_expected_columns and expected is not None:
        feature_check = check_features(X_eval, expected)
        X_eval = align_columns(X_eval, expected)

    y_proba = _proba_pos(pipeline, X_eval)
    if y_proba is not None:
        y_pred = (y_proba >= threshold).astype(int)
    else:
        y_pred = pipeline.predict(X_eval)

    metrics = compute_metrics_binary(y_test, y_pred, y_proba=y_proba)

    if verbose:
        print(f"\n=== {title} ===")
        if expected is not None:
            print(f"[Features esperadas] {expected}")
        if feature_check is not None and (feature_check["missing"] or feature_check["extra"]):
            print("[Atenção] Mismatch de colunas:")
            print(f"- Faltando: {feature_check['missing']}")
            print(f"- Extras: {feature_check['extra']}")
        print(f"Threshold: {threshold}")
        print("\n[Classification Report]")
        print(classification_report(y_test, y_pred, zero_division=0))
        print("[Metrics]")
        for k, v in metrics.items():
            print(f"- {k}: {v}")

    cm = plot_confusion(y_test, y_pred, title="Confusion Matrix — Modelo Final")

    if y_proba is not None:
        plot_roc_pr(y_test, y_proba, title_prefix="Modelo Final — ")

    return {
        "metrics_test": metrics,
        "confusion_matrix": cm,
        "feature_check": feature_check,
    }


def threshold_sweep_pipeline(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: Union[pd.Series, np.ndarray],
    thresholds: Optional[Sequence[float]] = None,
    enforce_expected_columns: bool = True,
) -> pd.DataFrame:
    """Gera tabela de Precision/Recall/F1 por threshold (requer predict_proba)."""
    if thresholds is None:
        thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    X_eval = X_test
    expected = expected_features_from_pipeline(pipeline)
    if enforce_expected_columns and expected is not None:
        X_eval = align_columns(X_eval, expected)

    y_proba = _proba_pos(pipeline, X_eval)
    if y_proba is None:
        raise ValueError("O pipeline não expõe predict_proba. Threshold sweep requer probabilidades.")

    y_true = np.asarray(y_test)
    rows = []
    for t in thresholds:
        y_pred = (y_proba >= float(t)).astype(int)
        rows.append(
            {
                "threshold": float(t),
                "precision": float(precision_score(y_true, y_pred, zero_division=0)),
                "recall": float(recall_score(y_true, y_pred, zero_division=0)),
                "f1": float(f1_score(y_true, y_pred, zero_division=0)),
                "churn_rate_pred": float(np.mean(y_pred)),
            }
        )

    return pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)

# =============================================================================
# (Opcional) Leaderboard de modelos salvos (caso exista pasta artifacts/models)
# =============================================================================

def build_models_leaderboard(
    models_dir: Union[str, Path],
    order_by: str = "f1",
    descending: bool = True,
) -> pd.DataFrame:
    """Monta leaderboard a partir de joblibs (quando você salva múltiplos best_*)."""
    models_dir = Path(models_dir)
    if not models_dir.exists():
        return pd.DataFrame()

    files = sorted([p for p in models_dir.glob("*.joblib") if p.is_file()])
    if not files:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for p in files:
        try:
            obj = joblib.load(p)
        except Exception:
            continue

        row: Dict[str, Any] = {"file": p.name}

        if isinstance(obj, dict):
            row["model_key"] = obj.get("model_key")
            row["model_name"] = obj.get("model_name")
            row["run_type"] = obj.get("run_type") or obj.get("search_type")

            tm = obj.get("test_metrics") or {}
            for k in ["accuracy", "precision", "recall", "f1", "roc_auc", "avg_precision"]:
                row[k] = tm.get(k, obj.get(k))

            row["n_train"] = obj.get("n_train")
            row["n_test"] = obj.get("n_test")

        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for col in ["accuracy", "precision", "recall", "f1", "roc_auc", "avg_precision", "n_train", "n_test"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if order_by in df.columns:
        df = df.sort_values(order_by, ascending=not descending)

    if order_by in df.columns:
        df["rank_" + order_by] = df[order_by].rank(method="dense", ascending=not descending).astype("Int64")

    return df.reset_index(drop=True)
