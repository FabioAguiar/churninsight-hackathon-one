# src/models/models_registry.py
"""
ChurnInsight — Seção 8 (N1)
Seleção de Modelos e Hiperparâmetros — Model Registry (core)

Filosofia:
- Registry canônico e auditável de modelos suportados
- Nenhuma decisão implícita no notebook
- Sem dependências de UI

Escopo estrito:
- ✔️ define modelos clássicos e seus defaults
- ✔️ define grids default (quando aplicável)
- ❌ NÃO executa treino / busca
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB

from .defaults_search_grids import DEFAULT_SEARCH_GRIDS


EstimatorFactory = Callable[[], Any]


@dataclass(frozen=True)
class ModelSpec:
    model_key: str
    display_name: str
    estimator_factory: EstimatorFactory
    default_params: Mapping[str, Any]
    search_grid: Optional[Mapping[str, Any]] = None


def build_models_registry(random_state: int = 42) -> Dict[str, ModelSpec]:
    """
    Cria o registry canônico de modelos para a Seção 8.

    Regras:
    - model_key é estável e usado em UI/leaderboard
    - default_params e search_grid são auditáveis
    """
    registry: Dict[str, ModelSpec] = {}

    # Logistic Regression
    registry["logreg"] = ModelSpec(
        model_key="logreg",
        display_name="Logistic Regression",
        estimator_factory=lambda: LogisticRegression(),
        default_params={
            "max_iter": 1000,
            "solver": "liblinear",
        },
        search_grid=DEFAULT_SEARCH_GRIDS.get("logreg"),
    )

    # Random Forest
    registry["rf"] = ModelSpec(
        model_key="rf",
        display_name="Random Forest",
        estimator_factory=lambda: RandomForestClassifier(),
        default_params={
            "n_estimators": 300,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": random_state,
            "n_jobs": -1,
        },
        search_grid=DEFAULT_SEARCH_GRIDS.get("rf"),
    )

    # KNN
    registry["knn"] = ModelSpec(
        model_key="knn",
        display_name="K-Nearest Neighbors (KNN)",
        estimator_factory=lambda: KNeighborsClassifier(),
        default_params={
            "n_neighbors": 15,
            "weights": "distance",
        },
        search_grid=DEFAULT_SEARCH_GRIDS.get("knn"),
    )

    # Opcionais (simples)
    registry["dt"] = ModelSpec(
        model_key="dt",
        display_name="Decision Tree",
        estimator_factory=lambda: DecisionTreeClassifier(),
        default_params={
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "random_state": random_state,
        },
        search_grid=DEFAULT_SEARCH_GRIDS.get("dt"),
    )

    registry["gnb"] = ModelSpec(
        model_key="gnb",
        display_name="Gaussian Naive Bayes",
        estimator_factory=lambda: GaussianNB(),
        default_params={},
        search_grid=DEFAULT_SEARCH_GRIDS.get("gnb"),
    )

    return registry
