"""
ChurnInsight — Seção 2 (N1): Qualidade Estrutural & Tipagem

Avalia impacto estrutural, conversões de tipo e integridade básica do dataset
logo após a ingestão, sem aplicar semântica de negócio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ============================================================
# Snapshots estruturais
# ============================================================

@dataclass(frozen=True)
class StructuralSnapshot:
    """
    Snapshot estrutural imutável do DataFrame em um ponto específico do pipeline.

    Esta estrutura representa um retrato objetivo da forma do dataset,
    capturando métricas essenciais para auditoria e comparação entre
    etapas do pipeline, especialmente na Seção 2 (Qualidade Estrutural & Tipagem).

    Atributos
    ---------
    n_rows : int
        Número total de linhas do DataFrame no momento da captura.
    n_cols : int
        Número total de colunas do DataFrame no momento da captura.
    memory_bytes : int
        Uso total de memória em bytes, calculado com `deep=True`.
    """    
    n_rows: int
    n_cols: int
    memory_bytes: int

    @property
    def memory_mb(self) -> float:
        """
        Retorna o uso de memória do DataFrame em megabytes (MB).

        Este valor é derivado diretamente de `memory_bytes` e existe
        exclusivamente para facilitar visualização e comparação
        em relatórios e tabelas do notebook.

        Retorna
        -------
        float
            Uso de memória em megabytes.
        """        
        return self.memory_bytes / (1024 * 1024)


def capture_structural_snapshot(df: pd.DataFrame) -> StructuralSnapshot:
    """
    Captura um retrato estrutural do DataFrame em um dado momento do pipeline.

    Esta função registra métricas estruturais básicas do dataset, permitindo
    comparações antes e depois de operações que possam impactar sua forma,
    como conversões de tipo, preenchimento de nulos ou outras intervenções
    estruturais.

    O snapshot gerado é utilizado principalmente para:
    - análise de impacto estrutural (antes × depois)
    - auditoria de alterações no pipeline
    - exibição resumida na Seção 2 do notebook principal

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo no ponto atual do pipeline.

    Retorna
    -------
    StructuralSnapshot
        Estrutura imutável contendo:
        - número de linhas
        - número de colunas
        - uso de memória em bytes (considerando `deep=True`)

    Observações
    -----------
    - Nenhuma modificação é aplicada ao DataFrame.
    - O cálculo de memória considera objetos Python internos,
      sendo adequado para comparações relativas, não para
      medições absolutas de consumo em produção.
    - Esta função deve ser chamada sempre que for necessário
      comparar impactos estruturais entre etapas do pipeline.
    """
    memory_bytes = int(df.memory_usage(deep=True).sum())
    return StructuralSnapshot(
        n_rows=int(df.shape[0]),
        n_cols=int(df.shape[1]),
        memory_bytes=memory_bytes,
    )


def build_before_after_table(
    before: StructuralSnapshot,
    after: StructuralSnapshot,
) -> pd.DataFrame:
    """
    Constrói uma tabela comparativa de impacto estrutural (antes × depois).

    Esta função recebe dois snapshots estruturais capturados em momentos
    distintos do pipeline e gera uma representação tabular padronizada,
    evidenciando variações estruturais no dataset.

    A tabela resultante é utilizada principalmente para:
    - exibição visual na Seção 2 do notebook principal
    - auditoria de alterações estruturais
    - comunicação clara de impactos causados por conversões ou ajustes

    Parâmetros
    ----------
    before : StructuralSnapshot
        Snapshot estrutural capturado antes da aplicação de operações
        estruturais no DataFrame.

    after : StructuralSnapshot
        Snapshot estrutural capturado após a aplicação das operações.

    Retorna
    -------
    pandas.DataFrame
        DataFrame com as seguintes métricas comparativas:
        - Linhas (Antes, Depois, Δ)
        - Colunas (Antes, Depois, Δ)
        - Memória em MB (Antes, Depois, Δ)

    Observações
    -----------
    - A coluna Δ representa a diferença aritmética simples entre
      os valores de "Depois" e "Antes".
    - A memória é apresentada em megabytes, arredondada para
      duas casas decimais, com finalidade comparativa.
    - Esta função não valida consistência semântica; assume que
      ambos os snapshots são compatíveis e provenientes do
      mesmo fluxo de dados.
    """
    return pd.DataFrame(
        [
            {
                "Métrica": "Linhas",
                "Antes": before.n_rows,
                "Depois": after.n_rows,
                "Δ": after.n_rows - before.n_rows,
            },
            {
                "Métrica": "Colunas",
                "Antes": before.n_cols,
                "Depois": after.n_cols,
                "Δ": after.n_cols - before.n_cols,
            },
            {
                "Métrica": "Memória (MB)",
                "Antes": round(before.memory_mb, 2),
                "Depois": round(after.memory_mb, 2),
                "Δ": round(after.memory_mb - before.memory_mb, 2),
            },
        ]
    )


# ============================================================
# Conversões de tipo
# ============================================================

def _default_conversion_rules(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Define regras padrão de conversão de tipos com base no schema do DataFrame.

    Esta função inspeciona as colunas presentes no DataFrame e retorna um
    conjunto de regras declarativas que descrevem conversões de tipo
    consideradas seguras, necessárias ou esperadas no contexto do projeto.

    As regras retornadas são utilizadas posteriormente por funções de
    aplicação de conversões, permitindo:
    - separação clara entre definição e execução
    - extensibilidade controlada das conversões
    - rastreabilidade das decisões de tipagem

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo no momento da avaliação das regras de conversão.

    Retorna
    -------
    dict[str, dict[str, Any]]
        Dicionário indexado pelo nome da coluna, onde cada valor descreve
        a regra de conversão a ser aplicada. Cada regra pode conter, por
        exemplo:
        - tipo de destino (`to`)
        - política de erro (`errors`)

    Observações
    -----------
    - Apenas colunas presentes no DataFrame são consideradas.
    - As regras aqui definidas são estruturais, não semânticas.
    - Conversões adicionais devem ser adicionadas de forma explícita
      e criteriosa, evitando inferências implícitas.
    - Esta função não executa conversões; apenas descreve intenções.
    """
    rules: Dict[str, Dict[str, Any]] = {}

    if "TotalCharges" in df.columns:
        rules["TotalCharges"] = {
            "to": "numeric",
            "errors": "coerce",
        }

    return rules


def apply_type_conversions(
    df: pd.DataFrame,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aplica conversões de tipo declaradas ao DataFrame e registra o impacto gerado.

    Esta função executa conversões estruturais de tipo com base em um conjunto
    de regras explícitas, produzindo:
    - um novo DataFrame com os tipos convertidos
    - um relatório tabular contendo apenas as conversões efetivamente aplicadas

    O foco é tornar visíveis e auditáveis:
    - mudanças reais de dtype
    - introdução de valores nulos decorrentes de falhas de parsing
    - volume de dados afetados por cada conversão

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame de entrada sobre o qual as conversões serão avaliadas
        e aplicadas.

    rules : dict[str, dict[str, Any]], opcional
        Regras de conversão por coluna. Caso não fornecidas, regras
        padrão são inferidas via `_default_conversion_rules(df)`.

        Cada regra descreve:
        - o tipo de destino (`to`)
        - a política de erro (`errors`), quando aplicável

    Retorna
    -------
    tuple[pandas.DataFrame, pandas.DataFrame]
        Uma tupla contendo:
        1. DataFrame resultante após a aplicação das conversões
        2. DataFrame de auditoria com as seguintes colunas:
           - column: nome da coluna convertida
           - dtype_after: tipo final após conversão
           - converted_non_null: quantidade de valores não nulos avaliados
           - introduced_nans: quantidade de nulos introduzidos pela conversão

    Observações
    -----------
    - Apenas colunas presentes no DataFrame são consideradas.
    - Conversões que não geram mudança de dtype nem introduzem nulos
      não são registradas no relatório.
    - Valores `introduced_nans` indicam entradas não parseáveis
      (ex.: strings vazias ou inválidas).
    - Esta função não realiza imputação ou limpeza posterior.
    - O DataFrame original não é modificado (opera sobre uma cópia).
    """
    df_after = df.copy()
    rules = rules or _default_conversion_rules(df_after)

    records: List[Dict[str, Any]] = []

    for col, spec in rules.items():
        if col not in df_after.columns:
            continue

        before = df_after[col]
        dtype_before = str(before.dtype)

        n_nulls_before = int(before.isna().sum())
        non_null_before = int(before.notna().sum())

        if spec.get("to") == "numeric":
            after = pd.to_numeric(before, errors=spec.get("errors", "coerce"))
        else:
            after = before

        df_after[col] = after
        dtype_after = str(after.dtype)

        n_nulls_after = int(after.isna().sum())
        introduced_nans = max(0, n_nulls_after - n_nulls_before)

        if dtype_before != dtype_after or introduced_nans > 0:
            records.append(
                {
                    "column": col,
                    "dtype_after": dtype_after,
                    "converted_non_null": non_null_before,
                    "introduced_nans": introduced_nans,
                }
            )

    return df_after, pd.DataFrame(records)


# ============================================================
# Integridade básica
# ============================================================

def check_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verifica a existência de registros duplicados no DataFrame.

    Esta função realiza uma checagem estrutural simples para identificar
    duplicidades completas de linhas, sem assumir semântica de chave
    ou identificador primário.

    O resultado é utilizado como indicador de integridade estrutural
    na Seção 2 do pipeline, sinalizando potenciais problemas que podem
    impactar análises, métricas ou etapas posteriores de modelagem.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame a ser avaliado quanto à presença de linhas duplicadas.

    Retorna
    -------
    dict[str, Any]
        Dicionário contendo:
        - has_duplicates (bool): indica se existem duplicidades
        - duplicate_count (int): número total de linhas marcadas como duplicadas

    Observações
    -----------
    - A checagem considera duplicidade de linhas completas (`keep=False`).
    - Nenhuma coluna é tratada como chave primária nesta etapa.
    - Esta função não remove nem altera registros duplicados.
    - A decisão de deduplicação deve ser tomada em etapas posteriores
      e de forma explícita no pipeline.
    """
    dup_count = int(df.duplicated(keep=False).sum())
    return {
        "has_duplicates": dup_count > 0,
        "duplicate_count": dup_count,
    }


def summarize_introduced_nans(
    conversions_df: pd.DataFrame,
    df_after: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resume os valores nulos introduzidos por conversões de tipo.

    Esta função analisa o relatório de conversões aplicadas e extrai
    apenas os casos em que a conversão de tipo resultou na introdução
    de valores nulos, normalmente decorrentes de falhas de parsing
    (ex.: strings vazias ou valores inválidos).

    O resumo gerado é utilizado como indicador específico de impacto
    estrutural na Seção 2 do pipeline, permitindo:
    - identificação rápida das colunas afetadas
    - quantificação objetiva do impacto relativo no dataset
    - direcionamento de decisões posteriores de imputação ou filtragem

    Parâmetros
    ----------
    conversions_df : pandas.DataFrame
        DataFrame de auditoria gerado por `apply_type_conversions`,
        contendo informações sobre conversões aplicadas e nulos
        introduzidos.

    df_after : pandas.DataFrame
        DataFrame resultante após a aplicação das conversões de tipo,
        utilizado para cálculo do percentual relativo de nulos.

    Retorna
    -------
    pandas.DataFrame
        DataFrame com as seguintes colunas:
        - column: nome da coluna afetada
        - introduced_nans: quantidade absoluta de nulos introduzidos
        - introduced_nans_pct: percentual de linhas afetadas

        Caso nenhuma conversão tenha introduzido nulos, retorna um
        DataFrame vazio com schema definido.

    Observações
    -----------
    - Apenas colunas com `introduced_nans > 0` são incluídas no resumo.
    - O percentual é calculado em relação ao número total de linhas
      do DataFrame pós-conversão.
    - Esta função não realiza imputação ou correção dos valores.
    - Atua exclusivamente como componente de diagnóstico e auditoria.
    """
    if conversions_df.empty:
        return pd.DataFrame(columns=["column", "introduced_nans", "introduced_nans_pct"])

    n_rows = max(1, int(df_after.shape[0]))
    out = conversions_df[["column", "introduced_nans"]].copy()
    out = out[out["introduced_nans"] > 0]

    out["introduced_nans_pct"] = (out["introduced_nans"] / n_rows) * 100

    return out.reset_index(drop=True)


# ============================================================
# Orquestrador da Seção 2
# ============================================================

def run_quality_and_typing_report(
    df: pd.DataFrame,
    *,
    render: bool = True,
) -> pd.DataFrame:
    """
    Executa a Seção 2 do pipeline principal (N1): Qualidade Estrutural & Tipagem.

    Esta função atua como orquestradora da Seção 2 do pipeline, coordenando
    a execução sequencial das etapas de diagnóstico estrutural, conversões
    de tipo e checagens básicas de integridade, a partir de um DataFrame
    já ingerido.

    O fluxo executado inclui:
    - captura do snapshot estrutural inicial
    - aplicação controlada de conversões de tipo
    - captura do snapshot estrutural final
    - construção da tabela de impacto (antes × depois)
    - checagem de duplicidades estruturais
    - sumarização de nulos introduzidos por conversão
    - renderização opcional do painel visual no notebook

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame ativo proveniente da etapa de ingestão (Seção 1),
        sobre o qual a avaliação de qualidade estrutural e tipagem
        será realizada.

    render : bool, opcional
        Indica se o painel visual da Seção 2 deve ser renderizado
        automaticamente no notebook.
        Padrão: True.

    Retorna
    -------
    pandas.DataFrame
        DataFrame resultante após a aplicação das conversões de tipo,
        representando o novo estado dos dados para as próximas etapas
        do pipeline.

    Observações
    -----------
    - Esta função não realiza transformações semânticas nos dados.
    - Todas as operações executadas são de natureza estrutural
      ou diagnóstica.
    - A renderização é opcional e desacoplada da lógica de dados,
      permitindo reutilização desta função em contextos não interativos
      (ex.: FastAPI, pipelines automatizados).
    - O DataFrame original não é modificado; a função opera sobre cópias.
    - Esta função estabelece o contrato formal entre a lógica da Seção 2
      (`src/data/quality_typing.py`) e sua apresentação visual
      (`src/reporting/ui.py`).
    """
    from src.reporting.ui import render_quality_typing_overview

    before = capture_structural_snapshot(df)

    df_after, conversions_df = apply_type_conversions(df)

    after = capture_structural_snapshot(df_after)

    impact_df = build_before_after_table(before, after)
    dup_info = check_duplicates(df_after)
    introduced_nans_df = summarize_introduced_nans(conversions_df, df_after)

    if render:
        render_quality_typing_overview(
            impact_df=impact_df,
            conversions_df=conversions_df,
            dup_info=dup_info,
            introduced_nans_df=introduced_nans_df,
        )

    return df_after
