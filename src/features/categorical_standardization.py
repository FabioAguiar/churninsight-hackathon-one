# src/features/categorical_standardization.py
"""
ChurnInsight — Seção 3 (N1): Padronização Categórica (Execução)

Este módulo implementa a **segunda célula conceitual da Seção 3** do notebook principal (N1),
responsável por executar padronização categórica **derivada explicitamente do diagnóstico**.

Regras desta etapa:
- aplica normalização textual mínima (lower/strip/colapso de espaços)
- aplica substituições explícitas (ex.: "no internet service" -> "no")
- NÃO executa encoding
- NÃO altera colunas fora do escopo (features do contrato)
- NÃO toca no target
- gera relatório auditável (o que mudou, por qual regra, em quais colunas)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.data.quality_typing import (
    StructuralSnapshot,
    build_before_after_table,
    capture_structural_snapshot,
)
from src.data.contract_loader import NormalizationScope


def _normalize_text_value(x: Any) -> Any:
    """
    Aplica normalização textual mínima a um valor escalar, preservando valores ausentes.

    Esta função executa apenas transformações **estruturais de forma**, sem qualquer
    inferência semântica, sendo utilizada como etapa preparatória para comparações
    e substituições determinísticas durante a padronização categórica.

    Regras aplicadas:
    - mantém `NaN` / `None` inalterados
    - converte o valor para string
    - remove espaços à esquerda e à direita
    - converte para minúsculas (`lower`)
    - colapsa múltiplos espaços internos em um único espaço

    Parâmetros
    ----------
    x : Any
        Valor escalar original da célula (texto, número ou valor ausente).

    Retorna
    -------
    Any
        Valor normalizado quando aplicável, ou o valor original quando ausente.
    """
    if pd.isna(x):
        return x
    s = str(x)
    s = s.strip().lower()
    s = " ".join(s.split())
    return s


@dataclass(frozen=True)
class StandardizationRule:
    """Regra explícita de substituição (já em lower)."""
    from_value: str
    to_value: str

    def as_tuple(self) -> Tuple[str, str]:
        return (self.from_value, self.to_value)


def apply_service_phrase_standardization(
    df: pd.DataFrame,
    *,
    phrase_map: Dict[str, str],
    cols_scope: List[str],
    features: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Aplica padronização explícita de **frases de serviço** em colunas categóricas.

    Esta função executa a padronização categórica **estritamente baseada em regras declaradas**,
    derivadas do diagnóstico da Seção 3 (N1). Seu objetivo é eliminar variações textuais
    semanticamente equivalentes (ex.: "no internet service" → "no"), preparando os dados
    para etapas posteriores de encoding — sem alterar o significado dos valores.

    Características desta etapa:
    - normalização textual mínima (lowercase, trim, colapso de espaços);
    - substituições **explícitas** definidas em `phrase_map`;
    - **não executa encoding** nem conversão numérica;
    - **não altera o target**;
    - **não modifica colunas fora do escopo** informado;
    - gera artefatos auditáveis que documentam exatamente o que foi alterado.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame no estado pós-aplicação do contrato da API
        (Seção 3 — Parte 1), já validado estruturalmente.
    phrase_map : dict[str, str]
        Mapeamento explícito de substituições textuais, definido a partir
        do diagnóstico categórico (ex.: {"no internet service": "no"}).
        As chaves são normalizadas internamente antes da aplicação.
    cols_scope : list[str]
        Lista de colunas candidatas à padronização, conforme identificado
        no diagnóstico (ex.: colunas com frases compostas ou valores triestado).
    features : list[str] | None, optional
        Lista de features do contrato. Quando fornecida, restringe a execução
        exclusivamente a esse conjunto, garantindo conformidade semântica
        com o contrato da API.

    Retorna
    -------
    dict
        Estrutura consolidada contendo:
        - df : DataFrame resultante após padronização categórica
        - impact_df : comparativo estrutural antes × depois
          (linhas, colunas, memória)
        - changes_df : relatório auditável de alterações por coluna
          (quantidade de células alteradas e exemplos)
        - rules_df : tabela das regras de padronização aplicadas
        - meta : resumo técnico da execução
          (colunas consideradas, total de células alteradas, nº de regras)

    Notas
    -----
    Esta função **não realiza inferência automática** nem heurísticas adicionais.
    Todas as transformações executadas devem estar previamente justificadas
    pelo diagnóstico categórico apresentado na etapa anterior do pipeline.
    """
    df_out = df.copy(deep=True)

    # Resolve escopo final: só colunas existentes + (se houver) apenas features do contrato
    cols = [c for c in cols_scope if c in df_out.columns]
    if features is not None:
        cols = [c for c in cols if c in features]

    before: StructuralSnapshot = capture_structural_snapshot(df_out)

    # regras em formato estável
    rules = [StandardizationRule(k.strip().lower(), v.strip().lower()) for k, v in phrase_map.items()]
    rules_df = pd.DataFrame([{"from": r.from_value, "to": r.to_value} for r in rules])

    audit_rows: List[Dict[str, Any]] = []
    total_cells_changed = 0

    for col in cols:
        original = df_out[col]
        normalized = original.map(_normalize_text_value)

        replaced = normalized.replace(phrase_map)

        changed_mask = (normalized != replaced) & ~(normalized.isna() & replaced.isna())
        changed_count = int(changed_mask.sum())
        total_cells_changed += changed_count

        examples = ""
        if changed_count > 0:
            sample_pairs = (
                pd.DataFrame({"before": normalized[changed_mask], "after": replaced[changed_mask]})
                .drop_duplicates()
                .head(8)
            )
            examples = "; ".join(
                [f"{b}→{a}" for b, a in zip(sample_pairs["before"], sample_pairs["after"])]
            )

        df_out[col] = replaced

        audit_rows.append(
            {
                "column": col,
                "rule_type": "service_phrase_map",
                "cells_changed": changed_count,
                "examples": examples,
            }
        )

    after: StructuralSnapshot = capture_structural_snapshot(df_out)
    impact_df = build_before_after_table(before, after)

    changes_df = (
        pd.DataFrame(audit_rows)
        .sort_values(["cells_changed", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )

    meta = {
        "scoped_cols_considered": cols,
        "total_cells_changed": int(total_cells_changed),
        "rules_count": int(len(rules)),
    }

    return {
        "df": df_out,
        "impact_df": impact_df,
        "changes_df": changes_df,
        "rules_df": rules_df,
        "meta": meta,
    }


def run_categorical_standardization(
    df: pd.DataFrame,
    *,
    scope: Optional[NormalizationScope],
    phrase_map: Dict[str, str],
    cols_scope: List[str],
    render: bool = False,
) -> Dict[str, Any]:
    """
    Orquestra a execução da **padronização categórica** (2ª célula da Seção 3 — N1).

    Esta função aplica regras explícitas de padronização categórica **derivadas do diagnóstico
    realizado anteriormente**, respeitando estritamente o escopo definido pelo contrato da API.

    A execução desta etapa:
    - aplica normalização textual mínima (lowercase, trim, colapso de espaços);
    - aplica substituições explícitas definidas em `phrase_map`
      (ex.: "no internet service" → "no");
    - **não executa encoding** nem transformação numérica;
    - **não altera o target**;
    - **não modifica colunas fora do escopo do contrato**;
    - gera artefatos auditáveis (impacto estrutural, mudanças por coluna, regras aplicadas).

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame no estado pós-aplicação do contrato (Seção 3 — Parte 1),
        contendo apenas as colunas válidas para o pipeline supervisionado.
    scope : NormalizationScope | None
        Escopo derivado do contrato da API. Quando fornecido, restringe a execução
        exclusivamente às `features` declaradas no contrato.
    phrase_map : dict[str, str]
        Mapeamento explícito de substituições textuais, definido a partir do diagnóstico
        categórico (ex.: {"no internet service": "no"}).
        As chaves e valores devem ser semanticamente estáveis.
    cols_scope : list[str]
        Lista de colunas candidatas à padronização, identificadas no diagnóstico
        (ex.: colunas com frases de serviço ou baixa cardinalidade).
    render : bool, default False
        Quando True, aciona a renderização dos artefatos na UI (uso exclusivo em notebooks).
        Em execução de pipeline, deve permanecer False.

    Retorna
    -------
    dict
        Payload consolidado contendo:
        - df : DataFrame padronizado
        - impact_df : comparativo estrutural antes × depois
        - changes_df : relatório auditável de alterações por coluna
        - rules_df : regras de padronização aplicadas
        - meta : resumo técnico da execução
        - scope : escopo do contrato utilizado
        - decision : parâmetros efetivamente aplicados nesta execução

    Notas
    -----
    Esta função representa a **materialização das decisões semânticas**
    estabelecidas no diagnóstico categórico. Nenhuma inferência automática
    é realizada nesta etapa.
    """
    features = None
    if scope is not None and getattr(scope, "features", None):
        features = list(scope.features)

    payload = apply_service_phrase_standardization(
        df,
        phrase_map=phrase_map,
        cols_scope=cols_scope,
        features=features,
    )

    payload["scope"] = scope
    payload["decision"] = {
        "phrase_map": dict(phrase_map),
        "cols_scope": list(cols_scope),
    }

    if render:
        from src.reporting.ui import render_categorical_standardization_report
        render_categorical_standardization_report(payload)

    return payload
