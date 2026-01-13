# src/models/evaluate.py
"""
ChurnInsight — Métricas utilitárias (S7/S8)

Este módulo existe para evitar duplicação e manter consistência de cálculo.
Não altera decisões da S7: apenas calcula métricas conforme parâmetros fornecidos.

Observação: a Seção 7 já é fechada. Este módulo é usado principalmente pela Seção 8.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


@dataclass(frozen=True)
class BinaryEvalDecision:
    positive_label: int = 1
    average: str = "binary"
    zero_division: int = 0


def compute_binary_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    decision: BinaryEvalDecision,
) -> Dict[str, float]:
    """Computa métricas binárias, de forma consistente e auditável."""
    if decision.average != "binary":
        raise ValueError("compute_binary_metrics suporta apenas average='binary'.")

    pos_label = int(decision.positive_label)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(
                y_true, y_pred, average="binary", pos_label=pos_label, zero_division=decision.zero_division
            )
        ),
        "recall": float(
            recall_score(
                y_true, y_pred, average="binary", pos_label=pos_label, zero_division=decision.zero_division
            )
        ),
        "f1": float(
            f1_score(
                y_true, y_pred, average="binary", pos_label=pos_label, zero_division=decision.zero_division
            )
        ),
    }


def compute_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray) -> Tuple[np.ndarray, List[int]]:
    labels = [0, 1]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return cm, labels
