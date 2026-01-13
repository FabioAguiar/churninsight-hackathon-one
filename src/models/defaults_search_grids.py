# src/models/defaults_search_grids.py
"""
ChurnInsight — Seção 8 (N1)
Seleção de Modelos e Hiperparâmetros — Grids default (auditáveis)

Escopo estrito:
- ✔️ grids pequenos/moderados para MVP
- ✔️ grids legíveis e fáceis de explicar
- ❌ NÃO tenta “espremer” performance máxima
"""

from __future__ import annotations

from typing import Any, Dict, Mapping


DEFAULT_SEARCH_GRIDS: Dict[str, Mapping[str, Any]] = {
    # Logistic Regression
    "logreg": {
        "C": [0.1, 1.0, 3.0, 10.0],
        "penalty": ["l1", "l2"],
        "solver": ["liblinear"],
    },

    # Random Forest
    "rf": {
        "n_estimators": [200, 400],
        "max_depth": [None, 8, 16],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
    },

    # KNN
    "knn": {
        "n_neighbors": [5, 11, 21, 31],
        "weights": ["uniform", "distance"],
        "p": [1, 2],  # 1 = Manhattan, 2 = Euclidean
    },

    # Decision Tree (opcional)
    "dt": {
        "max_depth": [None, 4, 8, 16],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    },

    # GaussianNB (opcional)
    "gnb": {
        "var_smoothing": [1e-09, 1e-08, 1e-07],
    },
}
