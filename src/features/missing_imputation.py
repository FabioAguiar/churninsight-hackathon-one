"""
ChurnInsight — Seção 4 (N1): Tratamento de Dados Faltantes (Execução)

Esta etapa executa **imputação auditável** como uma transformação **irreversível**
no pipeline de dados, respeitando rigorosamente o escopo semântico definido
pelo contrato (`NormalizationScope`).

Regras fundamentais desta seção
-------------------------------
- Apenas colunas declaradas em `scope.features` podem ser imputadas.
- O `target` **nunca** é imputado automaticamente.
- Nenhuma outra transformação ocorre aqui:
  - ❌ sem encoding
  - ❌ sem scaling
  - ❌ sem feature engineering
- Nenhuma inferência silenciosa é permitida:
  - ❌ sem defaults implícitos
  - ❌ sem heurísticas automáticas
  - ❌ sem correção “inteligente” de decisões incompletas

Filosofia do projeto
-------------------
Esta implementação segue estritamente o princípio:

    diagnóstico → decisão explícita → execução → auditoria

Erros são lançados **cedo e de forma explícita** sempre que a decisão fornecida
pelo notebook não for suficiente para garantir rastreabilidade e segurança
semântica. Esse comportamento é intencional e faz parte do design do pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.data.quality_typing import capture_structural_snapshot, build_before_after_table
from src.features.contract_and_candidates import NormalizationScope


# ---------------------------------------------------------------------
# Contratos auxiliares (internos)
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class ColumnImputationPlan:
    """
    Plano consolidado de imputação para uma única coluna.

    Esta estrutura representa uma **decisão já resolvida**, pronta para execução,
    após a aplicação de:
    - escopo semântico (`scope.features`)
    - filtros de inclusão/exclusão
    - overrides explícitos por coluna

    O plano é **imutável** (`frozen=True`) para garantir que decisões não sejam
    alteradas durante a fase de execução.

    Atributos
    ---------
    column : str
        Nome da coluna a ser imputada.
    dtype : str
        Tipo atual da coluna no pandas (string).
    kind : str
        Classificação semântica da coluna:
        - "numeric"
        - "categorical"
    strategy : str
        Estratégia de imputação já validada:
        - "median"
        - "mean"
        - "most_frequent"
        - "constant"
    fill_value : Any | None
        Valor explícito definido pelo usuário quando `strategy == "constant"`.
        Caso contrário, deve ser None.

    Nota de design
    --------------
    Esta classe separa claramente **decisão** de **execução**,
    reforçando a auditabilidade do pipeline.
    """
    column: str
    dtype: str
    kind: str
    strategy: str
    fill_value: Any | None = None


# ---------------------------------------------------------------------
# API pública (core)
# ---------------------------------------------------------------------
def run_missing_imputation(
    df: pd.DataFrame,
    scope: Optional[NormalizationScope],
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executa imputação de valores ausentes de forma **auditável** (Seção 4).

    Esta função é o **orquestrador central** da Seção 4 do pipeline e é responsável por:

    1. Validar a decisão explícita declarada no notebook
    2. Resolver quais colunas podem ser imputadas com base no escopo semântico
    3. Construir planos de imputação determinísticos por coluna
    4. Executar a imputação (transformação irreversível)
    5. Gerar artefatos completos de auditoria

    Comportamento conservador
    -------------------------
    Caso `scope` seja None, a função **não executa imputação**.
    Isso evita inferência silenciosa sobre quais colunas seriam features.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame no estado atual do pipeline.
    scope : NormalizationScope | None
        Contrato semântico contendo:
        - features : list[str]
        - target : str
    decision : dict
        Decisão explícita declarada no notebook. Nenhum default é aplicado.

    Retorno
    -------
    dict
        Payload consolidado para renderização e auditoria, contendo:
        - df : DataFrame após imputação
        - decision : decisão original
        - impact_df : auditoria estrutural (antes × depois)
        - changes_df : auditoria detalhada por coluna
        - meta : métricas agregadas da execução
        - scope : escopo semântico utilizado
    """
    if scope is None:
        return {
            "df": df,
            "scope": scope,
            "decision": decision,
            "impact_df": pd.DataFrame(),
            "changes_df": pd.DataFrame(),
            "meta": {
                "executed": False,
                "reason": "scope ausente; imputação não executada para evitar inferência silenciosa.",
                "total_imputed_cells": 0,
                "affected_columns": 0,
                "scoped_cols_considered": [],
                "excluded_cols_effective": [],
                "target_preserved": True,
            },
        }

    _validate_decision(decision)

    before = capture_structural_snapshot(df)
    df_after, changes_df, meta = _apply_imputation(df, scope, decision)
    after = capture_structural_snapshot(df_after)

    impact_df = build_before_after_table(before, after)

    return {
        "df": df_after,
        "scope": scope,
        "decision": decision,
        "impact_df": impact_df,
        "changes_df": changes_df,
        "meta": meta,
    }


# ---------------------------------------------------------------------
# Implementação interna
# ---------------------------------------------------------------------
def _validate_decision(decision: Dict[str, Any]) -> None:
    """
    Valida a decisão explícita declarada no notebook.

    Esta função **não corrige**, **não completa** e **não infere** valores.
    Seu papel é garantir que todas as informações necessárias para uma
    imputação auditável estejam presentes.

    Filosofia:
    - Falhar cedo
    - Falhar explicitamente
    - Nunca aplicar defaults ocultos
    """
    if not isinstance(decision, dict):
        raise ValueError("decision deve ser um dict com as estratégias declaradas.")

    required = ["numeric_strategy", "categorical_strategy"]
    missing = [k for k in required if k not in decision]
    if missing:
        raise ValueError(f"decision incompleta. Campos obrigatórios ausentes: {missing}")

    ns = decision.get("numeric_strategy")
    cs = decision.get("categorical_strategy")

    valid_numeric = {"median", "mean", "constant"}
    valid_cat = {"most_frequent", "constant"}

    if ns not in valid_numeric:
        raise ValueError(f"numeric_strategy inválida: {ns}. Use uma de {sorted(valid_numeric)}.")
    if cs not in valid_cat:
        raise ValueError(f"categorical_strategy inválida: {cs}. Use uma de {sorted(valid_cat)}.")

    if ns == "constant" and "numeric_fill_value" not in decision:
        raise ValueError("numeric_strategy == 'constant' exige numeric_fill_value.")
    if cs == "constant" and "categorical_fill_value" not in decision:
        raise ValueError("categorical_strategy == 'constant' exige categorical_fill_value.")

    if "exclude_cols" in decision and not isinstance(decision["exclude_cols"], list):
        raise ValueError("exclude_cols deve ser list[str].")
    if "include_cols" in decision and decision["include_cols"] is not None and not isinstance(decision["include_cols"], list):
        raise ValueError("include_cols deve ser list[str] ou None.")

    per_col = decision.get("per_column")
    if per_col is not None and not isinstance(per_col, dict):
        raise ValueError("per_column deve ser dict[col -> {strategy, fill_value?}].")


def _apply_imputation(
    df: pd.DataFrame,
    scope: NormalizationScope,
    decision: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executa a imputação efetiva respeitando estritamente o escopo semântico.

    Etapas internas:
    1. Resolve o universo de colunas (intenção × escopo × exclusões)
    2. Constrói planos determinísticos por coluna
    3. Executa a imputação
    4. Registra auditoria completa, inclusive para colunas sem faltantes

    Retorna
    -------
    df_after : DataFrame
        DataFrame após imputação.
    changes_df : DataFrame
        Auditoria detalhada por coluna considerada.
    meta : dict
        Métricas agregadas da execução.
    """
    df_after = df.copy(deep=True)

    target = getattr(scope, "target", None)
    features = list(getattr(scope, "features", []) or [])

    include_cols = decision.get("include_cols")
    exclude_cols = set(decision.get("exclude_cols", []) or [])

    intended = set(include_cols) if include_cols is not None else set(features)
    scoped_cols = [c for c in features if c in intended and c not in exclude_cols and c in df_after.columns]

    if target and target in scoped_cols:
        raise ValueError(f"Target '{target}' não pode ser imputado automaticamente.")

    per_col = decision.get("per_column") or {}

    plans: List[ColumnImputationPlan] = []
    for col in scoped_cols:
        dtype_str = str(df_after[col].dtype)
        kind = "numeric" if is_numeric_dtype(df_after[col]) else "categorical"

        if kind == "numeric":
            strategy = decision["numeric_strategy"]
            fill_value = decision.get("numeric_fill_value") if strategy == "constant" else None
        else:
            strategy = decision["categorical_strategy"]
            fill_value = decision.get("categorical_fill_value") if strategy == "constant" else None

        override = per_col.get(col)
        if override:
            strategy = override.get("strategy", strategy)
            if strategy == "constant":
                if "fill_value" not in override:
                    raise ValueError(f"per_column['{col}'] exige fill_value.")
                fill_value = override.get("fill_value")
            else:
                fill_value = None

        plans.append(ColumnImputationPlan(col, dtype_str, kind, strategy, fill_value))

    rows = []
    total_imputed = 0
    affected_cols = 0

    for plan in plans:
        s = df_after[plan.column]
        missing_before = int(s.isna().sum())

        used_value = _resolve_fill_value(s, plan.strategy, plan.fill_value)
        if missing_before > 0:
            df_after[plan.column] = s.fillna(used_value)

        missing_after = int(df_after[plan.column].isna().sum())
        imputed = max(missing_before - missing_after, 0)

        total_imputed += imputed
        if imputed > 0:
            affected_cols += 1

        rows.append(_changes_row(plan, missing_before, missing_after, len(df_after), used_value))

    meta = {
        "executed": True,
        "total_imputed_cells": int(total_imputed),
        "affected_columns": int(affected_cols),
        "scoped_cols_considered": scoped_cols,
        "excluded_cols_effective": sorted([c for c in exclude_cols if c in df.columns]),
        "target_preserved": True,
    }

    return df_after, pd.DataFrame(rows), meta


def _resolve_fill_value(series: pd.Series, strategy: str, fill_value: Any | None) -> Any:
    """
    Resolve o valor de preenchimento conforme a estratégia declarada.

    Estratégias suportadas:
    - median / mean : estatísticas simples da própria coluna
    - most_frequent : moda determinística
    - constant : valor explicitamente declarado

    Erros intencionais
    ------------------
    Se a coluna for 100% nula e a estratégia não for "constant",
    a função falha explicitamente para evitar inferência arbitrária.
    """
    if strategy == "constant":
        return fill_value

    s = series.dropna()
    if s.empty:
        raise ValueError(
            f"Coluna '{series.name}' está 100% nula. Use strategy='constant' com fill_value explícito."
        )

    if strategy == "median":
        return float(s.median()) if is_numeric_dtype(series) else s.median()
    if strategy == "mean":
        return float(s.mean()) if is_numeric_dtype(series) else s.mean()
    if strategy == "most_frequent":
        return s.mode(dropna=True).iloc[0]

    raise ValueError(f"Strategy não suportada: {strategy}")


def _changes_row(
    plan: ColumnImputationPlan,
    missing_before: int,
    missing_after: int,
    n_rows: int,
    used_value: Any,
) -> Dict[str, Any]:
    """
    Constrói uma linha de auditoria para o relatório de imputação.

    Esta função define o **contrato exato** do `changes_df`, que é utilizado
    pela camada de visualização e por inspeções posteriores.

    Observações:
    - O valor preenchido é apresentado de forma simples e determinística.
    - O percentual é calculado sobre o total de linhas do dataset.
    """
    imputed = max(missing_before - missing_after, 0)
    pct = (imputed / max(n_rows, 1)) * 100

    example = round(used_value, 6) if isinstance(used_value, float) else used_value

    return {
        "column": plan.column,
        "dtype": plan.dtype,
        "kind": plan.kind,
        "strategy": plan.strategy,
        "fill_value_used": example,
        "missing_before": missing_before,
        "missing_after": missing_after,
        "imputed": imputed,
        "pct_imputed": round(pct, 2),
    }
