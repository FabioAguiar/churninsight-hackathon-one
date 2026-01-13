# src/models/model_selection.py
"""
ChurnInsight — Seção 8 (N1)
Seleção de Modelos e Hiperparâmetros — Runner + Leaderboard (core)

Entrada:
- payload_s6 (representation)
- payload_s7 (decision + baselines_results)
- models_selection (lista explícita)
- run_mode: simple_train | grid_search

Saída:
- payload_s8 (model_runs, leaderboard, selection)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator

from .models_registry import build_models_registry, ModelSpec
from .train_model import TrainingDecision, train_simple, train_with_grid_search
from .evaluate import BinaryEvalDecision, compute_binary_metrics, compute_confusion_matrix


SUPPORTED_RUN_MODES = {"simple_train", "grid_search"}


def _extract_representation(payload_s6: Mapping[str, Any]) -> Dict[str, Any]:
    rep = payload_s6.get("representation")
    if not isinstance(rep, dict):
        raise ValueError("payload_s6['representation'] ausente ou inválido")
    required = ["X_train", "X_test", "y_train", "y_test"]
    missing = [k for k in required if k not in rep]
    if missing:
        raise ValueError(f"representation incompleta. Campos ausentes: {missing}")
    return {
        "X_train": rep["X_train"],
        "X_test": rep["X_test"],
        "y_train": rep["y_train"],
        "y_test": rep["y_test"],
    }


def _extract_s7_decision(payload_s7: Mapping[str, Any]) -> Dict[str, Any]:
    decision = payload_s7.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("payload_s7['decision'] ausente ou inválido")
    required = ["positive_label", "primary_metric", "secondary_metrics"]
    missing = [k for k in required if k not in decision]
    if missing:
        raise ValueError(f"decision da S7 incompleta. Campos ausentes: {missing}")
    return decision


def _baseline_threshold(payload_s7: Mapping[str, Any], primary_metric: str) -> Optional[float]:
    baselines = payload_s7.get("baselines_results")
    if not isinstance(baselines, list) or len(baselines) == 0:
        return None

    vals: List[float] = []
    for b in baselines:
        try:
            vals.append(float(b["metrics"][primary_metric]))
        except Exception:
            continue

    if not vals:
        return None

    # Regra: superar ambos => superar o max entre baselines
    return float(max(vals))


def _make_leaderboard(
    model_runs: List[Dict[str, Any]],
    primary_metric: str,
    secondary_metrics: Sequence[str],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for run in model_runs:
        m = run["metrics"]
        row = {
            "model_key": run["model_key"],
            "display_name": run["display_name"],
            "mode": run["mode"],
            "primary_metric": primary_metric,
            "primary_value": float(m.get(primary_metric, float("nan"))),
            "beats_baselines": bool(run.get("beats_baselines")),
            "eligible": bool(run.get("eligible")),
            "params_summary": run.get("params_summary", ""),
        }
        for sm in secondary_metrics:
            row[f"{sm}_value"] = float(m.get(sm, float("nan")))
        rows.append(row)

    df = pd.DataFrame(rows)

    # Ordenação: primary desc, depois secundárias na ordem
    sort_cols = ["primary_value"] + [f"{sm}_value" for sm in secondary_metrics]
    df = df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols), kind="mergesort").reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df


def _params_summary(params: Mapping[str, Any], max_items: int = 6) -> str:
    if not params:
        return "-"
    items = list(params.items())[:max_items]
    return ", ".join([f"{k}={v}" for k, v in items])


def run_section8_model_selection(
    payload_s6: Mapping[str, Any],
    payload_s7: Mapping[str, Any],
    models_selection: Sequence[str],
    run_mode: str = "simple_train",
    order_by: Optional[str] = None,
    allow_optional_models: bool = True,
    random_state: int = 42,
    cv: int = 5,
    n_jobs: int = -1,
    verbose: int = 0,
) -> Dict[str, Any]:
    """
    Executa a Seção 8 em lote.

    Parâmetros importantes:
    - models_selection: lista explícita de model_keys
    - run_mode: simple_train | grid_search
    - order_by: métrica para ordenar (default = primary_metric da S7)
    """
    if run_mode not in SUPPORTED_RUN_MODES:
        raise ValueError(f"run_mode inválido: {run_mode}. Use: {sorted(SUPPORTED_RUN_MODES)}")

    rep = _extract_representation(payload_s6)
    s7_dec = _extract_s7_decision(payload_s7)

    positive_label = int(s7_dec["positive_label"])
    primary_metric = str(s7_dec["primary_metric"])
    secondary_metrics = tuple([str(x) for x in s7_dec.get("secondary_metrics", [])])

    order_metric = str(order_by or primary_metric)
    allowed_metrics = {primary_metric, *secondary_metrics}
    if order_metric not in allowed_metrics:
        raise ValueError(
            f"order_by deve ser uma métrica da S7. Recebido: {order_metric}. Permitidas: {sorted(allowed_metrics)}"
        )

    registry = build_models_registry(random_state=random_state)

    # valida seleção
    if not isinstance(models_selection, (list, tuple)) or len(models_selection) == 0:
        raise ValueError("models_selection deve ser uma lista não vazia")
    unknown = [k for k in models_selection if k not in registry]
    if unknown:
        raise ValueError(f"model_key(s) desconhecido(s) no registry: {unknown}")

    # se o usuário não quer opcionais, limita a obrigatórios
    required_models = {"logreg", "rf", "knn"}
    if not allow_optional_models:
        forbidden = [k for k in models_selection if k not in required_models]
        if forbidden:
            raise ValueError(f"Modelos opcionais não permitidos nesta execução: {forbidden}")

    # baseline guard
    baseline_thr = _baseline_threshold(payload_s7, primary_metric=primary_metric)

    model_runs: List[Dict[str, Any]] = []
    for model_key in models_selection:
        spec: ModelSpec = registry[model_key]
        est = spec.estimator_factory()

        # treino
        timing: Dict[str, Any] = {}
        trained: BaseEstimator
        best_params: Dict[str, Any]

        training_dec = TrainingDecision(
            positive_label=positive_label,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics,
            random_state=random_state,
        )

        if run_mode == "simple_train":
            trained, timing = train_simple(
                estimator=est,
                X_train=rep["X_train"],
                y_train=rep["y_train"],
                params=spec.default_params,
            )
            best_params = dict(spec.default_params)

        else:
            if not spec.search_grid:
                # fallback: sem grid => treino simples
                trained, timing = train_simple(
                    estimator=est,
                    X_train=rep["X_train"],
                    y_train=rep["y_train"],
                    params=spec.default_params,
                )
                best_params = dict(spec.default_params)
                timing["note"] = "search_grid ausente — fallback para simple_train"
            else:
                trained, meta = train_with_grid_search(
                    estimator=est,
                    X_train=rep["X_train"],
                    y_train=rep["y_train"],
                    grid=spec.search_grid,
                    decision=training_dec,
                    cv=cv,
                    n_jobs=n_jobs,
                    verbose=verbose,
                )
                timing = meta
                best_params = dict(meta.get("best_params", {}))

        # avaliação
        y_pred = trained.predict(rep["X_test"])
        eval_dec = BinaryEvalDecision(positive_label=positive_label, average="binary", zero_division=0)
        metrics = compute_binary_metrics(y_true=rep["y_test"], y_pred=y_pred, decision=eval_dec)
        cm, labels = compute_confusion_matrix(y_true=rep["y_test"], y_pred=y_pred)

        primary_value = float(metrics.get(primary_metric, float("nan")))
        beats_baselines = True
        if baseline_thr is not None:
            beats_baselines = bool(primary_value > baseline_thr)

        run = {
            "model_key": spec.model_key,
            "display_name": spec.display_name,
            "mode": run_mode,
            "best_params": best_params,
            "params_summary": _params_summary(best_params),
            "metrics": metrics,
            "confusion_matrix": {"labels": labels, "matrix": cm.tolist()},
            "timing": timing,
            "baseline_guard": {
                "primary_metric": primary_metric,
                "baseline_threshold": baseline_thr,
                "beats_baselines": beats_baselines,
            },
            "beats_baselines": beats_baselines,
            "eligible": beats_baselines,
            "artifacts": {
                "estimator": trained,
            },
        }
        model_runs.append(run)

    leaderboard = _make_leaderboard(model_runs, primary_metric=order_metric, secondary_metrics=secondary_metrics)

    # seleção
    selected_key: Optional[str] = None
    eligible_df = leaderboard[leaderboard["eligible"] == True]
    if len(eligible_df) > 0:
        selected_key = str(eligible_df.iloc[0]["model_key"])

    selection = {
        "selected_model_key": selected_key,
        "order_by": order_metric,
        "primary_metric_guard": primary_metric,
        "reason": (
            "Modelo topo do leaderboard entre elegíveis (supera baselines na métrica principal)."
            if selected_key
            else "Nenhum modelo superou ambos os baselines na métrica principal."
        ),
        "evidence": {
            "top_rows": leaderboard.head(5).to_dict(orient="records"),
            "baseline_threshold": baseline_thr,
        },
    }

    payload_s8 = {
        "scope": "S8",
        "inputs": {
            "models_selection": list(models_selection),
            "run_mode": run_mode,
            "order_by": order_metric,
        },
        "inherited_decision": {
            "positive_label": positive_label,
            "primary_metric": primary_metric,
            "secondary_metrics": list(secondary_metrics),
        },
        "model_runs": model_runs,
        "leaderboard": leaderboard,
        "selection": selection,
        "guards": {
            "no_feature_engineering": True,
            "no_split_change": True,
            "no_metric_redefinition": True,
            "no_threshold_tuning": True,
            "baseline_gate_enabled": True,
        },
    }
    return payload_s8
