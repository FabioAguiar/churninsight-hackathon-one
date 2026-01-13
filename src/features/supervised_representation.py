# src/features/supervised_representation.py
"""ChurnInsight — Seção 6 (N1)
Representação para Modelagem Supervisionada — Execução Core

Este módulo implementa a **API core da Seção 6** do pipeline ChurnInsight.
Seu objetivo é **materializar a representação final** dos dados para
aprendizado supervisionado, preservando rigorosamente a filosofia do projeto:

    diagnóstico → decisão explícita → execução → auditoria

A Seção 6 atua como ponte formal entre:
- dados estruturalmente prontos (Seção 5)
- e estratégias de avaliação e seleção de modelos (Seções 7 e 8)

Escopo estrito (inegociável)
----------------------------
- ✔️ Decide e executa representação de X (features):
  - encoding de categóricas
  - representação de numéricas (passthrough ou scaling, apenas se explicitado)
- ✔️ Decide e executa representação de y (target), tipicamente encoding binário
- ✔️ Gera diagnósticos pós-representação (shapes, número de features, consistência)

- ❌ NÃO treina modelos
- ❌ NÃO compara algoritmos
- ❌ NÃO define métricas finais
- ❌ NÃO faz GridSearch / tuning
- ❌ NÃO infere defaults de decisão

Princípios de design
--------------------
- Separação clara entre decisão e execução.
- Anti-leakage: qualquer transformador de X é ajustado (fit) **somente no treino**.
- Transformações irreversíveis só ocorrem após decisão declarada.
- Diagnósticos são objetivos e auditáveis.

Contrato esperado
-----------------
Entrada:
- split: dict com X_train, X_test, y_train, y_test (saída canônica da Seção 5)
- scope: NormalizationScope (features/target)
- decision: dict com estratégias explícitas para X e y

Saída:
- payload consolidado com:
  - representation: X_train/X_test transformados + y_train/y_test codificados
  - transformer: objeto treinado apenas no treino (reutilizável em inferência)
  - feature_names: lista ordenada das features resultantes
  - diagnostics: shapes antes/depois e checks de consistência

Observação
----------
Este módulo não depende de UI. Ele produz artefatos que a camada
`src/reporting/ui.py` pode renderizar como cards na narrativa do notebook.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features.contract_and_candidates import NormalizationScope


# ------------------------------------------------------------
# Tipos internos
# ------------------------------------------------------------
DecisionDict = Dict[str, Any]


@dataclass(frozen=True)
class RepresentationDecision:
    """Estrutura interna normalizada (validada) para execução.

    A UI/notebook fornece um dicionário `decision`. Aqui o normalizamos
    para reduzir riscos de chaves ausentes e garantir mensagens de erro
    mais claras.
    """

    x_cat_strategy: str
    x_cat_handle_unknown: str
    x_num_strategy: str
    y_strategy: str
    y_mapping: Optional[Dict[Any, int]]
    y_dtype: str


# ------------------------------------------------------------
# API pública (core)
# ------------------------------------------------------------
def run_supervised_representation(
    split: Mapping[str, Any],
    scope: NormalizationScope,
    decision: DecisionDict,
) -> Dict[str, Any]:
    """Executa a Seção 6 (Representação para Modelagem Supervisionada).

    Parâmetros
    ----------
    split : Mapping[str, Any]
        Saída canônica da Seção 5, contendo:
        - X_train : pd.DataFrame
        - X_test  : pd.DataFrame
        - y_train : pd.Series
        - y_test  : pd.Series

    scope : NormalizationScope
        Escopo semântico (features/target) do pipeline.

    decision : dict
        Decisão explícita declarada no notebook (Seção 6), no formato mínimo:

        decision = {
          "X": {
            "categorical": {"strategy": "onehot", "handle_unknown": "ignore"},
            "numeric": {"strategy": "passthrough"}  # ou "standard_scaler"
          },
          "y": {"strategy": "map_binary", "mapping": {"No": 0, "Yes": 1}, "dtype": "int64"}
        }

    Retorno
    -------
    Dict[str, Any]
        Payload consolidado da Seção 6 contendo:
        - scope
        - decision
        - representation: X_train/X_test transformados + y_train/y_test codificados
        - diagnostics: shapes e checks de consistência
    """

    X_train, X_test, y_train, y_test = _unpack_split(split)

    _validate_scope_against_split(X_train, X_test, y_train, y_test, scope)
    dec = _validate_and_normalize_decision(decision)

    categorical_cols, numeric_cols = _infer_column_roles(X_train, scope)

    transformer = _build_x_transformer(
        categorical_cols=categorical_cols,
        numeric_cols=numeric_cols,
        decision=dec,
    )

    # Fit only on train (anti-leakage)
    transformer.fit(X_train)

    X_train_repr = _transform_to_dataframe(transformer, X_train)
    X_test_repr = _transform_to_dataframe(transformer, X_test)

    feature_names = list(X_train_repr.columns)

    y_train_repr, y_test_repr, target_mapping = _represent_target(
        y_train=y_train,
        y_test=y_test,
        decision=dec,
    )

    diagnostics = _build_diagnostics(
        X_train=X_train,
        X_test=X_test,
        X_train_repr=X_train_repr,
        X_test_repr=X_test_repr,
        y_train=y_train,
        y_test=y_test,
        y_train_repr=y_train_repr,
        y_test_repr=y_test_repr,
        categorical_cols=categorical_cols,
        numeric_cols=numeric_cols,
    )

    payload = {
        "scope": scope,
        "decision": decision,
        "representation": {
            "X_train": X_train_repr,
            "X_test": X_test_repr,
            "y_train": y_train_repr,
            "y_test": y_test_repr,
            "feature_names": feature_names,
            "transformer": transformer,
            "target_mapping": target_mapping,
        },
        "diagnostics": diagnostics,
    }
    return payload


# ------------------------------------------------------------
# Validações e normalização
# ------------------------------------------------------------
def _unpack_split(split: Mapping[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    required = ["X_train", "X_test", "y_train", "y_test"]
    missing = [k for k in required if k not in split]
    if missing:
        raise ValueError(f"split incompleto. Campos ausentes: {missing}")

    X_train = split["X_train"]
    X_test = split["X_test"]
    y_train = split["y_train"]
    y_test = split["y_test"]

    if not isinstance(X_train, pd.DataFrame) or not isinstance(X_test, pd.DataFrame):
        raise TypeError("split['X_train'] e split['X_test'] devem ser pandas.DataFrame")
    if not isinstance(y_train, pd.Series) or not isinstance(y_test, pd.Series):
        raise TypeError("split['y_train'] e split['y_test'] devem ser pandas.Series")

    return X_train.copy(), X_test.copy(), y_train.copy(), y_test.copy()


def _validate_scope_against_split(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    scope: NormalizationScope,
) -> None:
    # A Seção 5 já garantiu isso, mas aqui falhamos cedo caso o contrato se quebre.
    expected_features = list(scope.features)

    train_cols = list(X_train.columns)
    test_cols = list(X_test.columns)

    if train_cols != expected_features:
        raise ValueError(
            "X_train não está alinhado ao scope.features."
            f"Esperado (ordem): {expected_features}"
            f"Recebido: {train_cols}"
        )
    if test_cols != expected_features:
        raise ValueError(
            "X_test não está alinhado ao scope.features."
            f"Esperado (ordem): {expected_features}"
            f"Recebido: {test_cols}"
        )

    if y_train.name is not None and y_train.name != scope.target:
        raise ValueError(f"y_train.name='{y_train.name}' difere do scope.target='{scope.target}'")
    if y_test.name is not None and y_test.name != scope.target:
        raise ValueError(f"y_test.name='{y_test.name}' difere do scope.target='{scope.target}'")

    if len(X_train) != len(y_train):
        raise ValueError("X_train e y_train possuem tamanhos diferentes")
    if len(X_test) != len(y_test):
        raise ValueError("X_test e y_test possuem tamanhos diferentes")


def _validate_and_normalize_decision(decision: DecisionDict) -> RepresentationDecision:
    if not isinstance(decision, dict):
        raise TypeError("decision deve ser um dict")

    if "X" not in decision or "y" not in decision:
        raise ValueError("decision deve conter chaves 'X' e 'y'")

    dx = decision["X"]
    dy = decision["y"]
    if not isinstance(dx, dict) or not isinstance(dy, dict):
        raise TypeError("decision['X'] e decision['y'] devem ser dicts")

    # X.categorical
    cat = dx.get("categorical")
    if not isinstance(cat, dict):
        raise ValueError("decision['X']['categorical'] é obrigatório e deve ser dict")
    x_cat_strategy = cat.get("strategy")
    x_cat_handle_unknown = cat.get("handle_unknown")

    if x_cat_strategy != "onehot":
        raise ValueError("Na v1 da Seção 6, decision['X']['categorical']['strategy'] deve ser 'onehot'")
    if x_cat_handle_unknown not in {"ignore"}:
        raise ValueError("Na v1 da Seção 6, decision['X']['categorical']['handle_unknown'] deve ser 'ignore'")

    # X.numeric
    num = dx.get("numeric")
    if not isinstance(num, dict):
        raise ValueError("decision['X']['numeric'] é obrigatório e deve ser dict")
    x_num_strategy = num.get("strategy")
    if x_num_strategy not in {"passthrough", "standard_scaler"}:
        raise ValueError("decision['X']['numeric']['strategy'] deve ser 'passthrough' ou 'standard_scaler'")

    # y
    y_strategy = dy.get("strategy")
    if y_strategy not in {"map_binary", "passthrough"}:
        raise ValueError("decision['y']['strategy'] deve ser 'map_binary' ou 'passthrough'")

    y_dtype = str(dy.get("dtype", "int64"))

    y_mapping: Optional[Dict[Any, int]] = None
    if y_strategy == "map_binary":
        mapping = dy.get("mapping")
        if not isinstance(mapping, dict) or len(mapping) == 0:
            raise ValueError("decision['y']['mapping'] deve ser um dict não-vazio quando strategy='map_binary'")
        # normaliza valores para int
        y_mapping = {}
        for k, v in mapping.items():
            if not isinstance(v, (int, np.integer)):
                raise ValueError("Valores em decision['y']['mapping'] devem ser inteiros (0/1)")
            y_mapping[k] = int(v)

    return RepresentationDecision(
        x_cat_strategy=str(x_cat_strategy),
        x_cat_handle_unknown=str(x_cat_handle_unknown),
        x_num_strategy=str(x_num_strategy),
        y_strategy=str(y_strategy),
        y_mapping=y_mapping,
        y_dtype=y_dtype,
    )


# ------------------------------------------------------------
# Diagnóstico: papéis de colunas
# ------------------------------------------------------------
def _infer_column_roles(X_train: pd.DataFrame, scope: NormalizationScope) -> Tuple[List[str], List[str]]:
    """Classifica colunas do escopo em categóricas vs numéricas com base em dtype.

    Observação: esta etapa é **diagnóstica** (objetiva), não uma decisão.
    A decisão é feita via `decision` (ex.: onehot vs passthrough/scaler).

    Regras objetivas:
    - Numéricas: is_numeric_dtype e não-bool
    - Categóricas: tudo o que não for numérico (inclui bool)
    """

    categorical_cols: List[str] = []
    numeric_cols: List[str] = []

    for col in scope.features:
        s = X_train[col]
        if is_numeric_dtype(s) and not is_bool_dtype(s):
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)

    return categorical_cols, numeric_cols


# ------------------------------------------------------------
# Construção do transformador de X
# ------------------------------------------------------------
def _build_x_transformer(
    categorical_cols: List[str],
    numeric_cols: List[str],
    decision: RepresentationDecision,
) -> ColumnTransformer:
    transformers: List[Tuple[str, Any, List[str]]] = []

    # Categóricas: OneHot (v1 fixa)
    if categorical_cols:
        ohe = OneHotEncoder(
            handle_unknown=decision.x_cat_handle_unknown,
            sparse_output=False,
        )
        transformers.append(("cat_onehot", ohe, categorical_cols))

    # Numéricas: passthrough ou scaler
    if numeric_cols:
        if decision.x_num_strategy == "passthrough":
            transformers.append(("num", "passthrough", numeric_cols))
        elif decision.x_num_strategy == "standard_scaler":
            transformers.append(("num_scaler", StandardScaler(), numeric_cols))
        else:  # pragma: no cover
            raise ValueError(f"Estratégia numérica não suportada: {decision.x_num_strategy}")

    if not transformers:
        raise ValueError("Nenhuma coluna disponível para representação em X (categorical_cols e numeric_cols vazios)")

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=True,
    )


def _transform_to_dataframe(transformer: ColumnTransformer, X: pd.DataFrame) -> pd.DataFrame:
    arr = transformer.transform(X)

    # Por segurança: converte para ndarray
    if not isinstance(arr, np.ndarray):
        arr = np.asarray(arr)

    feature_names = transformer.get_feature_names_out()
    return pd.DataFrame(arr, columns=feature_names, index=X.index)


# ------------------------------------------------------------
# Representação do target (y)
# ------------------------------------------------------------
def _represent_target(
    y_train: pd.Series,
    y_test: pd.Series,
    decision: RepresentationDecision,
) -> Tuple[pd.Series, pd.Series, Optional[Dict[Any, int]]]:
    if decision.y_strategy == "passthrough":
        return y_train.copy(), y_test.copy(), None

    if decision.y_strategy != "map_binary" or decision.y_mapping is None:
        raise ValueError("Estratégia de y inválida (esperado 'map_binary' com mapping)")

    mapping = decision.y_mapping

    # Valida cobertura total (treino + teste)
    seen = set(pd.concat([y_train, y_test], axis=0).dropna().unique().tolist())
    missing_keys = [v for v in seen if v not in mapping]
    if missing_keys:
        raise ValueError(
            "decision['y']['mapping'] não cobre todos os valores observados no target. "
            f"Ausentes: {missing_keys}"
        )

    y_train_m = y_train.map(mapping).astype(decision.y_dtype)
    y_test_m = y_test.map(mapping).astype(decision.y_dtype)

    return y_train_m, y_test_m, dict(mapping)


# ------------------------------------------------------------
# Diagnósticos/auditorias
# ------------------------------------------------------------
def _build_diagnostics(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    X_train_repr: pd.DataFrame,
    X_test_repr: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    y_train_repr: pd.Series,
    y_test_repr: pd.Series,
    categorical_cols: List[str],
    numeric_cols: List[str],
) -> Dict[str, Any]:
    shapes_before = {
        "X_train": tuple(X_train.shape),
        "X_test": tuple(X_test.shape),
        "y_train": (len(y_train),),
        "y_test": (len(y_test),),
    }
    shapes_after = {
        "X_train": tuple(X_train_repr.shape),
        "X_test": tuple(X_test_repr.shape),
        "y_train": (len(y_train_repr),),
        "y_test": (len(y_test_repr),),
    }

    n_features_before = int(X_train.shape[1])
    n_features_after = int(X_train_repr.shape[1])

    train_test_consistency = {
        "same_feature_count": bool(X_train_repr.shape[1] == X_test_repr.shape[1]),
        "feature_names_match": bool(list(X_train_repr.columns) == list(X_test_repr.columns)),
    }

    x_missing_after = {
        "train_total_nans": int(pd.isna(X_train_repr).sum().sum()),
        "test_total_nans": int(pd.isna(X_test_repr).sum().sum()),
    }

    return {
        "column_roles": {
            "categorical_cols": list(categorical_cols),
            "numeric_cols": list(numeric_cols),
        },
        "shapes_before": shapes_before,
        "shapes_after": shapes_after,
        "n_features_before": n_features_before,
        "n_features_after": n_features_after,
        "fit_on": "train_only",
        "train_test_consistency": train_test_consistency,
        "x_missing_after": x_missing_after,
    }
