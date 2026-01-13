# src/models/evaluation_baselines.py
"""
ChurnInsight — Seção 7 (N1)
Estratégia de Avaliação e Baselines — Execução Core

Escopo estrito:
- ✔️ define e executa baselines (DummyClassifier)
- ✔️ calcula métricas e matriz de confusão
- ✔️ registra distribuição de classes (train/test)
- ❌ NÃO treina modelos reais
- ❌ NÃO compara algoritmos reais
- ❌ NÃO faz tuning / threshold / calibration
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

DecisionDict = Dict[str, Any]


@dataclass(frozen=True)
class Section7Decision:
    positive_label: int
    primary_metric: str
    secondary_metrics: List[str]
    baselines: List[Dict[str, Any]]  # ex: [{"name":"most_frequent","strategy":"most_frequent"}, ...]
    average: str                    # "binary"
    zero_division: int              # 0 ou 1
    random_state: int


def run_section7_evaluation_and_baselines(
    s6_payload: Mapping[str, Any],
    decision: DecisionDict,
) -> Dict[str, Any]:
    """
    Executa a Seção 7 a partir do payload da Seção 6.

    Entrada:
    - s6_payload: saída de run_supervised_representation(...)
    - decision: decisão explícita da seção 7

    Saída:
    - payload consolidado com:
      - decision
      - class_distribution
      - baselines_results (métricas + confusion matrix)
      - notes/guards (auditoria)
    """
    rep = _extract_representation(s6_payload)
    X_train = rep["X_train"]
    X_test = rep["X_test"]
    y_train = rep["y_train"]
    y_test = rep["y_test"]

    dec = _validate_and_normalize_decision(decision)

    _validate_binary_target(y_train, y_test, positive_label=dec.positive_label)

    class_dist = _class_distribution(y_train, y_test)

    baselines_results = []
    for b in dec.baselines:
        result = _run_single_baseline(
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            baseline=b,
            dec=dec,
        )
        baselines_results.append(result)

    payload = {
        "decision": decision,  # decisão original, sem “inferências”
        "class_distribution": class_dist,
        "baselines_results": baselines_results,
        "guards": {
            "scope": "S7",
            "no_real_models": True,
            "no_tuning": True,
            "no_threshold_adjustment": True,
        },
    }
    return payload


# -----------------------------
# Helpers / validações
# -----------------------------
def _extract_representation(s6_payload: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(s6_payload, Mapping):
        raise TypeError("s6_payload deve ser um mapping/dict")

    rep = s6_payload.get("representation")
    if not isinstance(rep, dict):
        raise ValueError("s6_payload['representation'] ausente ou inválido")

    required = ["X_train", "X_test", "y_train", "y_test"]
    missing = [k for k in required if k not in rep]
    if missing:
        raise ValueError(f"representation incompleta. Campos ausentes: {missing}")

    X_train = rep["X_train"]
    X_test = rep["X_test"]
    y_train = rep["y_train"]
    y_test = rep["y_test"]

    if not isinstance(X_train, pd.DataFrame) or not isinstance(X_test, pd.DataFrame):
        raise TypeError("X_train/X_test devem ser pandas.DataFrame")
    if not isinstance(y_train, pd.Series) or not isinstance(y_test, pd.Series):
        raise TypeError("y_train/y_test devem ser pandas.Series")

    return {
        "X_train": X_train.copy(),
        "X_test": X_test.copy(),
        "y_train": y_train.copy(),
        "y_test": y_test.copy(),
    }


def _validate_and_normalize_decision(decision: DecisionDict) -> Section7Decision:
    if not isinstance(decision, dict):
        raise TypeError("decision deve ser um dict")

    required = ["positive_label", "primary_metric", "secondary_metrics", "baselines"]
    missing = [k for k in required if k not in decision]
    if missing:
        raise ValueError(f"decision incompleta. Campos ausentes: {missing}")

    positive_label = int(decision["positive_label"])
    primary_metric = str(decision["primary_metric"]).strip().lower()
    secondary_metrics = [str(m).strip().lower() for m in (decision["secondary_metrics"] or [])]
    baselines = decision["baselines"]

    if primary_metric not in {"recall", "precision", "f1", "accuracy"}:
        raise ValueError("primary_metric inválida. Use: recall|precision|f1|accuracy")

    allowed_secondary = {"recall", "precision", "f1", "accuracy"}
    for m in secondary_metrics:
        if m not in allowed_secondary:
            raise ValueError(f"secondary_metric inválida: {m}")

    if not isinstance(baselines, list) or len(baselines) == 0:
        raise ValueError("baselines deve ser uma lista não vazia")

    for b in baselines:
        if not isinstance(b, dict):
            raise TypeError("cada baseline deve ser um dict")
        if "name" not in b or "strategy" not in b:
            raise ValueError("baseline exige chaves: name, strategy")
        if b["strategy"] not in {"most_frequent", "stratified"}:
            raise ValueError("strategy inválida para S7. Use: most_frequent|stratified")

    average = str(decision.get("average", "binary"))
    if average != "binary":
        raise ValueError("S7 suporta apenas average='binary' (escopo estrito).")

    zero_division = int(decision.get("zero_division", 0))
    if zero_division not in (0, 1):
        raise ValueError("zero_division deve ser 0 ou 1")

    random_state = int(decision.get("random_state", 42))

    return Section7Decision(
        positive_label=positive_label,
        primary_metric=primary_metric,
        secondary_metrics=secondary_metrics,
        baselines=baselines,
        average=average,
        zero_division=zero_division,
        random_state=random_state,
    )


def _validate_binary_target(y_train: pd.Series, y_test: pd.Series, positive_label: int) -> None:
    values = set(pd.concat([y_train, y_test]).dropna().unique().tolist())
    if values != {0, 1}:
        raise ValueError(f"S7 exige target binário {{0,1}}. Observado: {sorted(values)}")
    if positive_label not in (0, 1):
        raise ValueError("positive_label deve ser 0 ou 1")


def _class_distribution(y_train: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
    def _dist(y: pd.Series) -> Dict[str, Any]:
        vc = y.value_counts(dropna=False).sort_index()
        total = int(vc.sum())
        pct = (vc / total).round(6) if total > 0 else vc * 0.0
        return {
            "counts": vc.to_dict(),
            "pct": pct.to_dict(),
            "total": total,
        }

    return {"train": _dist(y_train), "test": _dist(y_test)}


def _run_single_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    baseline: Dict[str, Any],
    dec: Section7Decision,
) -> Dict[str, Any]:
    name = str(baseline["name"])
    strategy = str(baseline["strategy"])

    clf = DummyClassifier(strategy=strategy, random_state=dec.random_state)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    metrics = _compute_metrics(y_true=y_test, y_pred=y_pred, dec=dec)
    cm, cm_labels = _confusion(y_true=y_test, y_pred=y_pred)

    return {
        "baseline": {"name": name, "strategy": strategy},
        "metrics": metrics,
        "confusion_matrix": {
            "labels": cm_labels,      # [0, 1]
            "matrix": cm.tolist(),    # [[tn, fp],[fn,tp]]
        },
    }


def _compute_metrics(y_true: pd.Series, y_pred: np.ndarray, dec: Section7Decision) -> Dict[str, float]:
    # Sempre calculamos esse conjunto fixo (auditável)
    # Sem ROC-AUC aqui por escopo mínimo (e porque depende de proba/score)
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(
                y_true, y_pred,
                pos_label=dec.positive_label,
                average=dec.average,
                zero_division=dec.zero_division,
            )
        ),
        "recall": float(
            recall_score(
                y_true, y_pred,
                pos_label=dec.positive_label,
                average=dec.average,
                zero_division=dec.zero_division,
            )
        ),
        "f1": float(
            f1_score(
                y_true, y_pred,
                pos_label=dec.positive_label,
                average=dec.average,
                zero_division=dec.zero_division,
            )
        ),
    }
    # metadado de decisão: qual é “principal”
    out["_primary_metric"] = dec.primary_metric
    out["_secondary_metrics"] = list(dec.secondary_metrics)
    return out


def _confusion(y_true: pd.Series, y_pred: np.ndarray) -> Tuple[np.ndarray, List[int]]:
    labels = [0, 1]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return cm, labels
