# src/features/contract_and_candidates.py
"""
ChurnInsight — Seção 3 (N1): Conformidade ao Contrato & Padronização Categórica (Fase 0)

Este módulo implementa a **primeira célula conceitual da Seção 3** do notebook principal (N1),
com foco em:

1) **Conformidade ao contrato**:
   - reduzir o DataFrame para manter **apenas** as colunas previstas no contrato
   - registrar impacto estrutural (antes × depois)
   - reportar colunas ausentes do contrato e colunas descartadas

2) **Descoberta de candidatos à padronização categórica** (diagnóstico):
   - identificar colunas prováveis de normalização (strings/categorias e numéricos de baixa cardinalidade)
   - sugerir colunas binárias (Yes/No ou 0/1)
   - detectar presença de frases de serviço (ex.: "no internet service")

Observações importantes
-----------------------
- Este módulo **não aplica padronização** de valores; ele apenas prepara o dataset para
  as próximas células (normalização/encoding).
- A lógica aqui é **auditável, explícita e rastreável**, sem inferência estatística.
- A refatoração introduz `NormalizationScope` para separar explicitamente:
  - `features` (colunas do contrato de entrada do /predict)
  - `target` (variável alvo supervisionada, ex.: Churn)
- Mantém compatibilidade com o modo anterior (`contract_columns=...`) para não quebrar notebooks antigos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import pandas as pd


# ============================================================
# Modelos / Estruturas de suporte
# ============================================================

@dataclass(frozen=True)
class MinimalStructuralSnapshot:
    """
    Snapshot estrutural mínimo (fallback) para uso em UI.

    Este snapshot é utilizado quando o utilitário oficial de snapshot do pipeline
    (Seção 2) não estiver disponível, falhar, ou retornar None.

    Atributos
    ---------
    rows : int
        Número de linhas do DataFrame.
    cols : int
        Número de colunas do DataFrame.
    memory_mb : float
        Memória aproximada do DataFrame em MB (deep=True).
    """
    rows: int
    cols: int
    memory_mb: float


@dataclass(frozen=True)
class NormalizationScope:
    """
    Escopo declarativo de colunas (features vs target).

    Esta estrutura torna explícito o papel semântico das colunas no pipeline:
    - `features`: conjunto de colunas que compõem a entrada do endpoint `/predict`
      (contrato FastAPI ↔ Java).
    - `target`: variável alvo supervisionada (ex.: `Churn`), que **não deve** sofrer
      padronização semântica na Seção 3.

    Atributos
    ---------
    features : list[str]
        Lista de colunas de entrada (contrato).
    target : str
        Nome da coluna alvo (target), ex.: "Churn".

    Observações
    -----------
    - Para conformidade ao contrato na Seção 3 (1ª célula), o recorte final do DataFrame
      deve incluir `features + [target]` (quando `target` existir no DataFrame).
    - O `target` deve ser tratado de forma isolada em etapas posteriores (encoding/modelagem).
    """
    features: List[str]
    target: str

    def keep_columns(self) -> List[str]:
        """
        Retorna a lista de colunas a manter no recorte estrutural (features + target).

        Retorna
        -------
        list[str]
            Lista ordenada com as colunas do escopo, preservando a ordem declarada.
        """
        return list(self.features) + [self.target]


@dataclass(frozen=True)
class ContractConformanceResult:
    """
    Resultado da etapa de conformidade ao contrato.

    Este objeto encapsula o recorte do DataFrame para as colunas previstas no contrato,
    além de metadados essenciais para auditoria e visualização no N1.

    Atributos
    ---------
    df : pandas.DataFrame
        DataFrame recortado (somente colunas presentes no contrato + target, se aplicável).
    contract_columns : list[str]
        Lista final de colunas esperadas para recorte (ordem preservada).
        - No modo novo: `scope.features + [scope.target]`
        - No modo compat: `contract_columns` fornecido pelo chamador
    kept_columns : list[str]
        Colunas esperadas que estavam presentes no DataFrame e foram mantidas.
    missing_contract_columns : list[str]
        Colunas esperadas que não existiam no DataFrame de entrada.
    dropped_columns : list[str]
        Colunas existentes no DataFrame de entrada que foram descartadas por não estarem nas esperadas.
    snapshot_before : object
        Snapshot estrutural antes do recorte.
    snapshot_after : object
        Snapshot estrutural após o recorte.
    scope : NormalizationScope | None
        Escopo (features/target) quando disponível. Em modo compat (antigo), pode ser None.

    Observações
    -----------
    - `snapshot_before` e `snapshot_after` priorizam o tipo retornado por
      `src.data.quality_typing.capture_structural_snapshot` (Seção 2).
    - Quando indisponível, utiliza `MinimalStructuralSnapshot` como fallback,
      garantindo consistência da UI (sem valores "—").
    """
    df: pd.DataFrame
    contract_columns: List[str]
    kept_columns: List[str]
    missing_contract_columns: List[str]
    dropped_columns: List[str]
    snapshot_before: object
    snapshot_after: object
    scope: Optional[NormalizationScope] = None


@dataclass(frozen=True)
class CategoricalCandidatesResult:
    """
    Resultado do diagnóstico de candidatos à padronização categórica.

    Atributos
    ---------
    overview : dict[str, Any]
        Métricas de alto nível (total de colunas, candidatas, binárias, frases de serviço).
    top_candidates : pandas.DataFrame
        Tabela com candidatos priorizados por suspeita e baixa cardinalidade.
    binary_candidates : pandas.DataFrame
        Tabela com colunas sugeridas como binárias (Yes/No ou 0/1).
    service_phrase_candidates : pandas.DataFrame
        Tabela com colunas onde aparecem frases de serviço (ex.: "no internet service").

    Observações
    -----------
    - As tabelas retornadas são apropriadas para renderização no notebook (N1),
      mas este módulo **não** implementa UI.
    """
    overview: Dict[str, Any]
    top_candidates: pd.DataFrame
    binary_candidates: pd.DataFrame
    service_phrase_candidates: pd.DataFrame


# ============================================================
# Funções internas (helpers)
# ============================================================

def _safe_capture_snapshot(df: pd.DataFrame) -> object:
    """
    Captura snapshot estrutural de forma robusta.

    Prioriza o utilitário oficial de snapshot do pipeline (Seção 2):
    `src.data.quality_typing.capture_structural_snapshot`.

    Caso o utilitário não exista, falhe, ou retorne None, utiliza um snapshot
    mínimo local (MinimalStructuralSnapshot) para garantir consistência da UI.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame para captura do snapshot.

    Retorna
    -------
    object
        Objeto de snapshot (ex.: StructuralSnapshot) quando disponível;
        caso contrário retorna MinimalStructuralSnapshot.
    """
    def _fallback(d: pd.DataFrame) -> MinimalStructuralSnapshot:
        """
        Gera um snapshot estrutural mínimo local (fallback) para uso em UI.
        """
        mem_mb = float(d.memory_usage(deep=True).sum() / (1024**2))
        return MinimalStructuralSnapshot(
            rows=int(d.shape[0]),
            cols=int(d.shape[1]),
            memory_mb=mem_mb,
        )

    try:
        from src.data.quality_typing import capture_structural_snapshot  # type: ignore
        snap = capture_structural_snapshot(df)
        if snap is None:
            return _fallback(df)
        return snap
    except Exception:
        return _fallback(df)


def _pct_unique(n_unique: int, n_rows: int) -> float:
    """
    Calcula a razão de valores únicos (n_unique / n_rows) com proteção para n_rows <= 0.
    """
    if n_rows <= 0:
        return 0.0
    return float(n_unique) / float(n_rows)


def _is_textual_dtype(s: pd.Series) -> bool:
    """
    Indica se a série deve ser tratada como textual/categórica no diagnóstico do pipeline.
    """
    dt = str(s.dtype).lower()
    return ("object" in dt) or ("string" in dt) or ("category" in dt)


def _is_numeric_dtype(s: pd.Series) -> bool:
    """
    Indica se a série possui dtype numérico, conforme a tipagem do pandas.
    """
    return pd.api.types.is_numeric_dtype(s.dtype)


def _sample_values(s: pd.Series, max_items: int = 6) -> List[Any]:
    """
    Extrai amostras de valores distintos para inspeção visual.
    """
    try:
        vals = s.dropna().unique().tolist()
    except Exception:
        vals = []
    return vals[:max_items]


def _has_service_phrase(values: Iterable[Any]) -> bool:
    """
    Detecta a presença de frases típicas de serviço em um conjunto de valores.

    Esta função inspeciona valores textuais normalizados (amostras) em busca
    de expressões conhecidas que representam estados de serviço, como
    "no internet service" ou "no phone service".

    O objetivo é identificar colunas que, apesar de categóricas, contêm
    valores compostos que devem ser tratados de forma especial em etapas
    posteriores de padronização (ex.: redução para um rótulo canônico).

    Parâmetros
    ----------
    values : Iterable[Any]
        Conjunto de valores (tipicamente amostras distintas de uma coluna),
        possivelmente contendo strings e valores nulos.

    Retorna
    -------
    bool
        True se ao menos uma frase típica de serviço for detectada;
        False caso contrário.

    Observações
    -----------
    - A detecção é baseada em heurística textual simples (substring, case-insensitive).
    - A função não realiza normalização nem substituição de valores.
    - O resultado é utilizado exclusivamente para diagnóstico e priorização
      visual no pipeline (Seção 3 — N1).
    """
    targets = ("no internet service", "no phone service")
    for v in values:
        if isinstance(v, str):
            low = v.strip().lower()
            if any(t in low for t in targets):
                return True
    return False


def _is_binary_like(values: Iterable[Any]) -> bool:
    """
    Avalia se um conjunto de valores sugere comportamento binário.

    Esta função verifica se os valores distintos observados em uma coluna
    podem ser interpretados como um domínio binário típico, como:
    - Yes / No
    - Y / N
    - 0 / 1

    O objetivo é identificar colunas candidatas a tratamento binário
    específico em etapas posteriores do pipeline (encoding, normalização),
    sem aplicar qualquer transformação neste estágio.

    Parâmetros
    ----------
    values : Iterable[Any]
        Conjunto de valores distintos (tipicamente amostras), possivelmente
        contendo strings, números e valores nulos.

    Retorna
    -------
    bool
        True se o conjunto de valores indicar um domínio binário plausível;
        False caso contrário.

    Observações
    -----------
    - Valores nulos (NaN/None) são ignorados na análise.
    - Strings são normalizadas para minúsculas antes da avaliação.
    - A heurística aceita apenas domínios binários estritos; conjuntos com
      mais de dois valores distintos são descartados.
    - Esta função não infere semântica nem aplica encoding.
    """
    cleaned: List[Any] = []
    for v in values:
        if pd.isna(v):
            continue
        cleaned.append(v)

    if not cleaned:
        return False

    norm: set = set()
    for v in cleaned:
        if isinstance(v, str):
            vv = v.strip().lower()
            if vv in {"0", "1"}:
                norm.add(int(vv))
            else:
                norm.add(vv)
        else:
            try:
                if float(v).is_integer():
                    norm.add(int(v))
                else:
                    norm.add(v)
            except Exception:
                norm.add(v)

    if norm == {"yes", "no"}:
        return True
    if norm == {0, 1}:
        return True
    if norm == {"y", "n"}:
        return True

    return False


def _scope_from_contract_columns(contract_columns: Sequence[str]) -> Optional[NormalizationScope]:
    """
    Tenta derivar um NormalizationScope a partir de uma lista de colunas do contrato (modo compat).

    Esta função existe para manter compatibilidade com o modo legado do pipeline,
    no qual o contrato era fornecido apenas como uma lista de nomes de colunas,
    sem separação explícita entre features e target.

    Regra de inferência
    -------------------
    - Se a coluna "Churn" existir em `contract_columns` e houver ao menos
      uma outra coluna, assume:
        * target = "Churn"
        * features = todas as demais colunas
    - Caso contrário, nenhuma inferência é realizada e a função retorna None.

    Parâmetros
    ----------
    contract_columns : Sequence[str]
        Lista ou sequência de nomes de colunas esperadas pelo contrato.

    Retorna
    -------
    NormalizationScope | None
        Instância de NormalizationScope quando a inferência é possível;
        None quando o target não pode ser determinado com segurança.

    Observações
    -----------
    - A inferência é propositalmente conservadora para evitar erros silenciosos.
    - Esta função não valida a existência real das colunas no DataFrame.
    - Quando `None` é retornado, o pipeline continua operando sem escopo explícito,
      mantendo compatibilidade com notebooks antigos.
    """
    cols = [c for c in contract_columns if isinstance(c, str)]
    if "Churn" in cols and len(cols) >= 2:
        feats = [c for c in cols if c != "Churn"]
        return NormalizationScope(features=feats, target="Churn")
    return None


def _normalize_exclude_columns(exclude_columns: Optional[Sequence[str]]) -> Set[str]:
    """
    Normaliza a lista de colunas a excluir para um conjunto (case-sensitive).

    Parâmetros
    ----------
    exclude_columns : Sequence[str] | None
        Colunas que não devem participar do diagnóstico de candidatos.

    Retorna
    -------
    set[str]
        Conjunto com nomes válidos de colunas a excluir.
    """
    if not exclude_columns:
        return set()
    out: Set[str] = set()
    for c in exclude_columns:
        if isinstance(c, str) and c.strip():
            out.add(c.strip())
    return out


# ============================================================
# API pública (Seção 3 — 1ª célula)
# ============================================================

def enforce_contract_columns(
    df: pd.DataFrame,
    contract_columns: List[str],
    *,
    strict: bool = False,
    scope: Optional[NormalizationScope] = None,
) -> ContractConformanceResult:
    """
    Reduz o DataFrame para conter somente as colunas esperadas (contrato + target).

    Esta função implementa a etapa de conformidade ao contrato na Seção 3 (N1),
    recortando o DataFrame para manter exclusivamente o conjunto de colunas
    declaradas como esperadas. O recorte é auditável e retorna metadados que
    suportam UI e rastreabilidade, incluindo colunas mantidas, colunas ausentes
    no DataFrame de entrada e colunas descartadas.

    Quando `scope` é fornecido, ele representa o escopo semântico (features vs target)
    e é preservado no resultado para consumo da camada de UI e das próximas etapas.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame de entrada no estado atual do pipeline, anterior ao recorte.

    contract_columns : list[str]
        Lista ordenada de colunas esperadas para o recorte. Tipicamente corresponde a:
        - `scope.features + [scope.target]` (modo novo), ou
        - lista explícita em modo compatível (legado).

    strict : bool, opcional
        Se True, exige que todas as colunas esperadas existam no DataFrame de entrada.
        Quando houver colunas ausentes, a função falha com ValueError.
        Padrão: False.

    scope : NormalizationScope | None, opcional
        Escopo semântico associado ao recorte (features/target). Quando fornecido,
        é anexado ao resultado para rastreabilidade. Padrão: None.

    Retorna
    -------
    ContractConformanceResult
        Estrutura contendo:
        - DataFrame recortado (somente colunas mantidas, na ordem do contrato)
        - listas de colunas mantidas/ausentes/descartadas
        - snapshots estruturais antes e depois do recorte
        - escopo (`scope`) quando disponível

    Exceções
    --------
    TypeError
        Se `contract_columns` não for uma lista de strings.

    ValueError
        Se `strict=True` e houver colunas do contrato ausentes no DataFrame de entrada.

    Observações
    -----------
    - Esta função não aplica transformações semânticas nem conversões de tipo:
      seu papel é exclusivamente estrutural (recorte e auditoria).
    - Os snapshots estruturais (`snapshot_before`/`snapshot_after`) priorizam o utilitário
      oficial do pipeline (Seção 2). Caso indisponível, utiliza fallback local para evitar
      valores indefinidos na UI.
    - O DataFrame retornado preserva a ordem declarada em `contract_columns`.
    """
    if not isinstance(contract_columns, list) or not all(isinstance(c, str) for c in contract_columns):
        raise TypeError("contract_columns deve ser uma lista de strings.")

    snapshot_before = _safe_capture_snapshot(df)

    missing = [c for c in contract_columns if c not in df.columns]
    if strict and missing:
        raise ValueError(
            "Conformidade ao contrato falhou (strict=True). "
            f"Colunas ausentes: {missing}"
        )

    kept = [c for c in contract_columns if c in df.columns]
    dropped = sorted([c for c in df.columns if c not in kept])

    df_out = df.loc[:, kept].copy()

    snapshot_after = _safe_capture_snapshot(df_out)

    return ContractConformanceResult(
        df=df_out,
        contract_columns=list(contract_columns),
        kept_columns=kept,
        missing_contract_columns=missing,
        dropped_columns=dropped,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        scope=scope,
    )


def find_categorical_candidates(
    df: pd.DataFrame,
    *,
    max_unique_ratio: float = 0.5,
    max_unique_count: int = 50,
    include_numeric_small: bool = True,
    top_n: int = 30,
    head_bin: int = 20,
    head_service: int = 20,
    exclude_columns: Optional[Sequence[str]] = None,
) -> CategoricalCandidatesResult:
    """
    Detecta colunas candidatas à padronização categórica (diagnóstico, sem alteração).

    Atualização (target fora do diagnóstico)
    ----------------------------------------
    - Permite excluir explicitamente colunas do diagnóstico via `exclude_columns`.
      Caso típico: excluir o `target` (ex.: "Churn") para que ele não apareça
      em "Top candidatos" / "Provavelmente binárias" / "Frases de serviço".

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame de entrada (idealmente já conforme o contrato).
    max_unique_ratio : float, padrão 0.5
        Razão máxima de valores únicos para considerar um campo como candidato.
    max_unique_count : int, padrão 50
        Número máximo absoluto de valores distintos para considerar um campo como candidato.
    include_numeric_small : bool, padrão True
        Se True, inclui colunas numéricas com baixa cardinalidade como possíveis candidatas.
    top_n : int, padrão 30
        Quantidade de linhas na tabela top_candidates.
    head_bin : int, padrão 20
        Quantidade de linhas na tabela binary_candidates.
    head_service : int, padrão 20
        Quantidade de linhas na tabela service_phrase_candidates.
    exclude_columns : Sequence[str] | None, padrão None
        Colunas a excluir do diagnóstico (não entram em registros/tabelas).

    Retorna
    -------
    CategoricalCandidatesResult
        Estrutura com tabelas e métricas de overview.
    """
    exclude_set = _normalize_exclude_columns(exclude_columns)

    n_rows = int(df.shape[0])
    records: List[Dict[str, Any]] = []

    for col in df.columns:
        if col in exclude_set:
            continue

        s = df[col]
        n_unique = int(s.nunique(dropna=True))
        pct = _pct_unique(n_unique, n_rows)
        samples = _sample_values(s, max_items=6)

        textual = _is_textual_dtype(s)
        numeric = _is_numeric_dtype(s)

        reasons: List[str] = []
        suspected = False

        if textual:
            suspected = True
            reasons.append("texto/categoria")
        elif include_numeric_small and numeric:
            if (n_unique <= max_unique_count) and (pct <= max_unique_ratio):
                suspected = True
                reasons.append("numérico baixa cardinalidade")

        binary_like = _is_binary_like(samples if samples else _sample_values(s, max_items=12))
        if binary_like:
            reasons.append("binário (yes/no)")

        service_phrase = _has_service_phrase(samples if samples else _sample_values(s, max_items=12))
        if service_phrase:
            reasons.append("frases de serviço")

        records.append(
            {
                "column": col,
                "dtype": str(s.dtype),
                "n_unique": n_unique,
                "pct_unique": round(pct, 4),
                "sample_values": samples,
                "suspected": suspected,
                "binary_like": binary_like,
                "service_phrase": service_phrase,
                "reasons": ", ".join(reasons) if reasons else "",
            }
        )

    df_all = pd.DataFrame.from_records(records)

    # NOTE:
    # - df_all possui 1 linha por COLUNA analisada.
    # - Portanto, métricas "total analisadas" devem vir de df_all.shape[0],
    #   e NÃO de df.shape[0] (linhas do dataset).
    analyzed_cols = int(df_all.shape[0])

    if df_all.empty:
        overview = {
            "total_columns": 0,
            "suspected_columns": 0,
            "binary_candidates": 0,
            "service_phrase_columns": 0,
            "excluded_columns": sorted(list(exclude_set)) if exclude_set else [],
            "heuristics": {
                "max_unique_ratio": max_unique_ratio,
                "max_unique_count": max_unique_count,
                "include_numeric_small": include_numeric_small,
            },
        }
        empty_cols = ["column", "dtype", "n_unique", "pct_unique", "sample_values", "reasons"]
        empty_df = pd.DataFrame(columns=empty_cols)
        return CategoricalCandidatesResult(
            overview=overview,
            top_candidates=empty_df.copy(),
            binary_candidates=empty_df.copy(),
            service_phrase_candidates=empty_df.copy(),
        )

    df_sus = df_all[df_all["suspected"] == True].copy()  # noqa: E712
    df_sus.sort_values(
        by=["service_phrase", "binary_like", "n_unique", "pct_unique", "column"],
        ascending=[False, False, True, True, True],
        inplace=True,
    )
    top_candidates = df_sus.loc[:, ["column", "dtype", "n_unique", "pct_unique", "sample_values", "reasons"]].head(top_n)

    df_bin = df_all[df_all["binary_like"] == True].copy()  # noqa: E712
    df_bin.sort_values(by=["n_unique", "pct_unique", "column"], ascending=[True, True, True], inplace=True)
    binary_candidates = df_bin.loc[:, ["column", "dtype", "n_unique", "pct_unique", "sample_values", "reasons"]].head(head_bin)

    df_srv = df_all[df_all["service_phrase"] == True].copy()  # noqa: E712
    df_srv.sort_values(by=["n_unique", "pct_unique", "column"], ascending=[True, True, True], inplace=True)
    service_phrase_candidates = df_srv.loc[:, ["column", "dtype", "n_unique", "pct_unique", "sample_values", "reasons"]].head(head_service)

    overview = {
        "total_columns": analyzed_cols,
        "suspected_columns": int(df_sus.shape[0]),
        "binary_candidates": int(df_bin.shape[0]),
        "service_phrase_columns": int(df_srv.shape[0]),
        "excluded_columns": sorted(list(exclude_set)) if exclude_set else [],
        "heuristics": {
            "max_unique_ratio": max_unique_ratio,
            "max_unique_count": max_unique_count,
            "include_numeric_small": include_numeric_small,
        },
    }

    return CategoricalCandidatesResult(
        overview=overview,
        top_candidates=top_candidates.reset_index(drop=True),
        binary_candidates=binary_candidates.reset_index(drop=True),
        service_phrase_candidates=service_phrase_candidates.reset_index(drop=True),
    )


def run_contract_and_candidates(
    df: pd.DataFrame,
    *,
    scope: Optional[NormalizationScope] = None,
    contract_columns: Optional[List[str]] = None,
    strict_contract: bool = False,
    max_unique_ratio: float = 0.5,
    max_unique_count: int = 50,
    include_numeric_small: bool = True,
    top_n: int = 30,
    head_bin: int = 20,
    head_service: int = 20,
) -> Dict[str, Any]:
    """
    Orquestra a 1ª célula da Seção 3 (N1): conformidade ao contrato + diagnóstico categórico.

    Esta função executa, em sequência:
    1) recorte estrutural do DataFrame conforme o contrato (conformidade)
    2) descoberta diagnóstica de colunas candidatas à padronização categórica

    O resultado é um payload consolidado, apropriado para consumo pela camada de UI
    (renderers do notebook) e por etapas posteriores do pipeline.

    Modos suportados
    ---------------
    - Modo novo (recomendado): forneça `scope=NormalizationScope(...)`
    - Modo compatível (legado): forneça `contract_columns=[...]`

    Regras de resolução
    -------------------
    - Se `scope` for fornecido, ele tem prioridade e define as colunas esperadas via
      `scope.keep_columns()`.
    - Se `scope` não for fornecido, utiliza `contract_columns`.
    - Se nenhum for fornecido, a função falha.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame de entrada no estado atual do pipeline.

    scope : NormalizationScope | None, opcional
        Escopo semântico do pipeline (features/target). Quando fornecido, define o contrato
        de entrada e permite excluir o target do diagnóstico categórico. Padrão: None.

    contract_columns : list[str] | None, opcional
        Lista ordenada de colunas esperadas (modo legado/compatível). Padrão: None.

    strict_contract : bool, opcional
        Se True, exige conformidade estrita ao contrato e falha quando houver colunas ausentes.
        É repassado para `enforce_contract_columns(strict=...)`. Padrão: False.

    max_unique_ratio : float, opcional
        Razão máxima de valores únicos para considerar uma coluna como candidata no diagnóstico.
        Padrão: 0.5.

    max_unique_count : int, opcional
        Quantidade máxima absoluta de valores distintos para considerar uma coluna como candidata.
        Padrão: 50.

    include_numeric_small : bool, opcional
        Se True, inclui colunas numéricas de baixa cardinalidade como candidatas. Padrão: True.

    top_n : int, opcional
        Quantidade de linhas no relatório "Top candidatos". Padrão: 30.

    head_bin : int, opcional
        Quantidade de linhas no relatório "Provavelmente binárias". Padrão: 20.

    head_service : int, opcional
        Quantidade de linhas no relatório "Frases de serviço detectadas". Padrão: 20.

    Retorna
    -------
    dict[str, Any]
        Payload consolidado contendo:
        - df: DataFrame recortado conforme contrato
        - contract: ContractConformanceResult
        - candidates: CategoricalCandidatesResult
        - scope: NormalizationScope | None (escopo efetivamente utilizado)

    Exceções
    --------
    TypeError
        Se `scope` não for um NormalizationScope quando fornecido, ou se `contract_columns`
        não for uma lista de strings.

    ValueError
        Se nem `scope` nem `contract_columns` forem fornecidos.

    Observações
    -----------
    - O diagnóstico categórico é heurístico e não determinístico: ele sugere candidatos,
      mas não aplica qualquer padronização/encoding.
    - Regra de design: o target (quando conhecido via `scope`) é explicitamente excluído do
      diagnóstico de candidatos, evitando ruído e preservando integridade semântica.
    - Este orquestrador não executa UI; ele apenas prepara dados e relatórios para renderização.
    """
    if scope is not None:
        if not isinstance(scope, NormalizationScope):
            raise TypeError("scope deve ser uma instância de NormalizationScope.")
        expected = scope.keep_columns()
        scope_used = scope
    else:
        if contract_columns is None:
            raise ValueError("Forneça `scope=NormalizationScope(...)` ou `contract_columns=[...]`.")
        if not isinstance(contract_columns, list) or not all(isinstance(c, str) for c in contract_columns):
            raise TypeError("contract_columns deve ser uma lista de strings.")
        expected = list(contract_columns)
        scope_used = _scope_from_contract_columns(expected)

    contract_result = enforce_contract_columns(
        df,
        expected,
        strict=strict_contract,
        scope=scope_used,
    )

    # Regra: target NÃO entra no diagnóstico de candidatos
    exclude_cols: List[str] = []
    if scope_used is not None and isinstance(scope_used, NormalizationScope):
        if isinstance(scope_used.target, str) and scope_used.target.strip():
            exclude_cols.append(scope_used.target.strip())

    candidates_result = find_categorical_candidates(
        contract_result.df,
        max_unique_ratio=max_unique_ratio,
        max_unique_count=max_unique_count,
        include_numeric_small=include_numeric_small,
        top_n=top_n,
        head_bin=head_bin,
        head_service=head_service,
        exclude_columns=exclude_cols if exclude_cols else None,
    )

    return {
        "df": contract_result.df,
        "contract": contract_result,
        "candidates": candidates_result,
        "scope": scope_used,
    }
