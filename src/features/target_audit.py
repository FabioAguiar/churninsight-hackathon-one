"""
ChurnInsight — Seção 3 (N1): Auditoria do Target (diagnóstico)

Este módulo fornece uma auditoria **somente diagnóstica** da coluna target do dataset,
sem aplicar transformações e sem criar inferências silenciosas.

Objetivo
--------
- Verificar se a coluna target está **presente**, **consistente** e **adequada** para modelagem.
- Exibir sinais de alerta comuns (nulos, variações de casing/espaços, valores inesperados).
- Produzir um artefato simples (dict) para ser consumido pela camada de UI do notebook.

Regras do pipeline (filosofia do projeto)
-----------------------------------------
diagnóstico → decisão explícita → execução → auditoria

Nesta etapa:
- NÃO normaliza valores do target.
- NÃO faz encoding.
- NÃO corrige automaticamente inconsistências.
- Apenas descreve o estado atual do target e aponta possíveis problemas.

Observação
----------
No dataset Telco (churn), o target costuma vir como "Yes"/"No".
Este módulo consegue trabalhar tanto com esse caso quanto com targets numéricos/booleanos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


import pandas as pd


# ---------------------------------------------------------------------
# Contratos auxiliares
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class TargetAuditResult:
    """
    Estrutura de resultado da **auditoria diagnóstica do target**.

    Este contrato representa o **estado observado** da coluna target em um
    determinado ponto do pipeline, sem aplicar qualquer transformação,
    correção ou inferência silenciosa. Ele existe para tornar explícito
    *o que foi encontrado*, não *o que deve ser feito*.

    Papel no pipeline
    -----------------
    - Servir como **artefato auditável e imutável** da Seção 3.3.
    - Encapsular métricas objetivas (nulos, cardinalidade, distribuição).
    - Registrar sinais de alerta detectados durante a auditoria.
    - Fornecer uma estrutura estável para consumo pela camada de UI
      e por wrappers de orquestração.

    Princípios
    ----------
    - Somente leitura / diagnóstico.
    - Nenhuma normalização, encoding ou correção automática.
    - Campos explicitamente nomeados para evitar ambiguidade semântica.
    - Conteúdo suficiente para explicar o status final ("ok", "warning", "error").

    Campos
    ------
    target : str
        Nome da coluna target auditada.
    exists : bool
        Indica se a coluna target existe no DataFrame.
    n_rows : int
        Número total de linhas do DataFrame no momento da auditoria.
    missing_count : int
        Quantidade absoluta de valores ausentes (NaN) no target.
    missing_pct : float
        Percentual de valores ausentes no target (0–100).
    nunique : int
        Número de valores distintos no target (dropna=True).
    unique_values_preview : list[str]
        Prévia limitada dos valores distintos observados, já stringificados
        para fins de auditoria e UI.
    value_counts : list[dict]
        Distribuição de valores do target (inclui NaN), limitada por `top_k`.
        Cada item segue o formato:
        {"value": <str>, "count": <int>, "pct": <float>}.
    anomalies : list[str]
        Lista textual de achados e sinais de alerta detectados durante a auditoria.
        Não implica correção automática.
    status : str
        Status consolidado da auditoria:
        - "ok"      : nenhum sinal relevante detectado,
        - "warning" : inconsistências potenciais,
        - "error"   : condição inválida para prosseguir sem decisão explícita.
    notes : str
        Observação sintética de alto nível sobre a adequação do target.

    Observação
    ----------
    Esta classe **não toma decisões**. Ela apenas descreve o estado atual
    do target de forma estruturada e rastreável.
    """
    target: str
    exists: bool
    n_rows: int
    missing_count: int
    missing_pct: float
    nunique: int
    unique_values_preview: List[str]
    value_counts: List[Dict[str, Any]]
    anomalies: List[str]
    status: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict (pronto para payload/UI)."""
        return {
            "target": self.target,
            "exists": self.exists,
            "n_rows": self.n_rows,
            "missing_count": self.missing_count,
            "missing_pct": self.missing_pct,
            "nunique": self.nunique,
            "unique_values_preview": list(self.unique_values_preview),
            "value_counts": list(self.value_counts),
            "anomalies": list(self.anomalies),
            "status": self.status,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------
def audit_target(
    df: pd.DataFrame,
    target: Optional[str],
    *,
    expected_values: Optional[List[Any]] = None,
    top_k: int = 10,
    preview_unique: int = 12,
) -> Dict[str, Any]:
    """
    Realiza auditoria **estritamente diagnóstica** da coluna target, sem qualquer
    transformação ou inferência silenciosa.

    Esta função é o **núcleo analítico** da Seção 3.3 e responde exclusivamente à
    pergunta: *“o target está presente, consistente e adequado para modelagem?”*.
    Ela não aplica normalizações, encoding ou correções automáticas — apenas
    descreve o estado atual da coluna.

    Papel no pipeline
    -----------------
    - Validar a existência do target no DataFrame.
    - Medir completude (nulos), cardinalidade e distribuição de valores.
    - Detectar sinais comuns de inconsistência sem alterar os dados:
        - valores ausentes,
        - cardinalidade inesperada,
        - strings vazias ou com whitespace,
        - variações de casing (ex.: Yes/YES/yes),
        - valores fora de um domínio esperado (quando fornecido).
    - Produzir um artefato **autoexplicativo e auditável**, consumido pela camada
      de UI e por wrappers de orquestração.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame a ser auditado. Não é modificado pela função.
    target : str | None
        Nome da coluna target. Se None ou vazio, a auditoria é interrompida
        e o status retornado é "error".
    expected_values : list[Any] | None, opcional
        Domínio esperado do target (ex.: ["Yes", "No"]).
        Quando fornecido, a auditoria aponta valores observados fora desse conjunto.
        A comparação é feita por igualdade direta, **sem normalização semântica**.
    top_k : int, padrão=10
        Número máximo de categorias exibidas na distribuição (`value_counts`).
    preview_unique : int, padrão=12
        Número máximo de valores distintos exibidos como prévia
        (`unique_values_preview`).

    Retorna
    -------
    dict
        Estrutura pronta para payload/UI contendo:
        - metadados do target (existência, linhas, nulos, cardinalidade),
        - distribuição de valores (auditável),
        - lista textual de anomalias detectadas,
        - status consolidado ("ok", "warning" ou "error"),
        - nota explicativa de alto nível.

    Garantias
    ---------
    - O DataFrame de entrada não é alterado.
    - Nenhuma conversão de tipo ou limpeza é aplicada.
    - Toda inferência é explícita e reportada como anomalia textual.
    - A saída é determinística e reprodutível para o mesmo input.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df deve ser um pandas.DataFrame válido.")

    n_rows = int(len(df))

    if target is None or str(target).strip() == "":
        res = TargetAuditResult(
            target=str(target),
            exists=False,
            n_rows=n_rows,
            missing_count=0,
            missing_pct=0.0,
            nunique=0,
            unique_values_preview=[],
            value_counts=[],
            anomalies=["Target não informado (None/vazio)."],
            status="error",
            notes="Auditoria não executada: target ausente.",
        )
        return res.to_dict()

    target = str(target)
    exists = target in df.columns
    if not exists:
        res = TargetAuditResult(
            target=target,
            exists=False,
            n_rows=n_rows,
            missing_count=0,
            missing_pct=0.0,
            nunique=0,
            unique_values_preview=[],
            value_counts=[],
            anomalies=[f"Coluna target '{target}' não existe no DataFrame."],
            status="error",
            notes="Auditoria não executada: coluna target ausente no df.",
        )
        return res.to_dict()

    s = df[target]

    missing_count = int(s.isna().sum())
    missing_pct = (missing_count / max(n_rows, 1)) * 100.0

    nunique = int(s.nunique(dropna=True))

    # value_counts incluindo NaN
    vc = s.value_counts(dropna=False)
    value_counts: List[Dict[str, Any]] = []
    for val, cnt in vc.head(max(top_k, 0)).items():
        pct = (int(cnt) / max(n_rows, 1)) * 100.0
        value_counts.append(
            {
                "value": _stringify_value(val),
                "count": int(cnt),
                "pct": round(pct, 2),
            }
        )

    # prévia de valores distintos (dropna)
    uniques = list(pd.unique(s.dropna()))
    unique_values_preview = [_stringify_value(v) for v in uniques[: max(preview_unique, 0)]]

    anomalies: List[str] = []

    # Sinais gerais
    if missing_count > 0:
        anomalies.append(f"Target possui {missing_count} valor(es) ausente(s) ({missing_pct:.2f}%).")

    if nunique == 0:
        anomalies.append("Target não possui valores não-nulos.")
    elif nunique == 1:
        anomalies.append("Target possui apenas 1 valor distinto (risco de classe única).")
    elif nunique > 2:
        anomalies.append(f"Target possui {nunique} valores distintos (esperado binário?).")

    # Sinais específicos para strings: whitespace / casing
    # (sem transformar; apenas detectar)
    if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
        non_null = s.dropna()

        # valores vazios/whitespace
        try:
            stripped = non_null.astype(str).str.strip()
            empty_like = (stripped == "").sum()
            if int(empty_like) > 0:
                anomalies.append(f"Target possui {int(empty_like)} string(s) vazia(s)/somente espaço.")
        except Exception:
            # não bloquear auditoria por problemas de casting
            pass

        # variações por casing: ex.: Yes/YES/yes
        # A ideia é detectar se existem múltiplas variantes quando normalizadas
        try:
            lowered = non_null.astype(str).str.strip().str.lower()
            # mapeia normalizado -> conjunto de originais distintos
            mapping: Dict[str, set] = {}
            for orig, norm in zip(non_null.astype(str).tolist(), lowered.tolist()):
                mapping.setdefault(norm, set()).add(orig)
            casing_variants = {k: v for k, v in mapping.items() if len(v) > 1}
            if casing_variants:
                # limita o texto pra não explodir
                examples = []
                for k, vals in list(casing_variants.items())[:3]:
                    examples.append(f"{k}: {sorted(list(vals))[:4]}")
                anomalies.append("Target possui variações de casing/whitespace: " + " | ".join(examples))
        except Exception:
            pass

    # expected values (sem normalização)
    if expected_values is not None:
        expected_set = set(expected_values)
        observed = set([v for v in uniques])
        unexpected = [v for v in observed if v not in expected_set]
        if unexpected:
            anomalies.append(
                "Valores fora do esperado: " + ", ".join(_stringify_value(v) for v in unexpected[:10])
            )

    # status
    status = "ok"
    if not exists:
        status = "error"
    elif any(msg.startswith("Coluna target") for msg in anomalies):
        status = "error"
    elif anomalies:
        status = "warning"


    notes = "Target consistente para modelagem (sinais básicos ok)." if status == "ok" else "Revisar achados na auditoria do target."

    res = TargetAuditResult(
        target=target,
        exists=True,
        n_rows=n_rows,
        missing_count=missing_count,
        missing_pct=round(missing_pct, 2),
        nunique=nunique,
        unique_values_preview=unique_values_preview,
        value_counts=value_counts,
        anomalies=anomalies,
        status=status,
        notes=notes,
    )
    return res.to_dict()


def run_target_audit(
    df: pd.DataFrame,
    scope: Any,
    *,
    expected_values: Optional[List[Any]] = None,
    top_k: int = 10,
    preview_unique: int = 12,
) -> Dict[str, Any]:
    """
    Executa a auditoria diagnóstica do target (Seção 3.3) e produz um payload
    padronizado para consumo direto pela camada de UI do pipeline.

    Esta função atua como **wrapper de orquestração** sobre `audit_target`,
    garantindo alinhamento com a filosofia do projeto e com o contrato esperado
    pelo renderer do notebook.

    Papel no pipeline
    -----------------
    - Integra a auditoria do target ao fluxo semântico definido pelo `scope`.
    - **Não transforma o target** (sem normalização, encoding ou correções).
    - Consolida métricas e domínios em um formato estável para exibição.
    - Permite rastreabilidade explícita antes do início da modelagem.

    Responsabilidades
    -----------------
    - Resolver o nome do target a partir do `scope` (dict ou objeto).
    - Executar auditoria diagnóstica via `audit_target`.
    - Construir:
        - `audit`: achados completos da auditoria,
        - `audit_df`: tabela auditável (distribuição de valores),
        - `meta`: resumo compacto usado pelos cards da UI
          (linhas, únicos, nulos, inválidos, domínios esperado/observado).
    - Retornar payload tolerante a falhas (target ausente/inexistente),
      sem lançar exceções em fluxo normal do notebook.

    Parâmetros
    ----------
    df : pandas.DataFrame
        DataFrame no estado atual do pipeline.
    scope : Any
        Escopo semântico contendo, preferencialmente, o atributo/chave `target`.
        Pode ser um dict ou um objeto.
    expected_values : list[Any] | None, opcional
        Domínio esperado do target (ex.: ["Yes", "No"]).
        Quando fornecido, permite identificar valores inválidos
        **sem normalização semântica**.
    top_k : int, padrão=10
        Número máximo de categorias retornadas na tabela auditável
        (delegado ao `audit_target`).
    preview_unique : int, padrão=12
        Limite de valores distintos exibidos como prévia
        (delegado ao `audit_target`).

    Retorna
    -------
    dict
        Payload padronizado com chaves estáveis:
        - df : DataFrame original (não modificado)
        - scope : escopo semântico recebido
        - target : nome do target auditado
        - audit : dict com achados completos da auditoria
        - audit_df : pandas.DataFrame com distribuição do target
        - meta : dict resumido para UI (status, contagens e domínios)

    Garantias
    ---------
    - Nenhuma mutação é aplicada ao DataFrame.
    - Nenhuma inferência silenciosa é criada.
    - O payload retornado é compatível com `render_target_audit_report`
      sem necessidade de adaptação adicional.
    """

    """
    Executa auditoria do target (Seção 3.3) e retorna payload padronizado para UI.

    Wrapper do core: NÃO transforma o target. Apenas diagnostica e devolve:
    - audit: dict com achados (compatível com audit_target)
    - audit_df: tabela auditável (value_counts) para exibição
    - meta: resumo completo para o card (linhas, únicos, nulos, inválidos, domínios)

    Retorna
    -------
    dict
        Payload com chaves estáveis:
        - df
        - scope
        - target
        - audit (dict)
        - audit_df (DataFrame)
        - meta (dict)
    """
    # scope tolerante (dict OU objeto)
    if isinstance(scope, dict):
        target = scope.get("target")
    else:
        target = getattr(scope, "target", None)

    if not target:
        return {
            "df": df,
            "scope": scope,
            "target": None,
            "audit": {},
            "audit_df": pd.DataFrame(),
            "meta": {
                "executed": False,
                "reason": "target ausente no scope; auditoria não executada.",
                "n_rows": int(len(df)) if isinstance(df, pd.DataFrame) else "—",
            },
        }

    if target not in df.columns:
        return {
            "df": df,
            "scope": scope,
            "target": target,
            "audit": {},
            "audit_df": pd.DataFrame(),
            "meta": {
                "executed": False,
                "reason": f"target '{target}' não encontrado no DataFrame.",
                "n_rows": int(len(df)) if isinstance(df, pd.DataFrame) else "—",
            },
        }

    audit = audit_target(
        df=df,
        target=target,
        expected_values=expected_values,
        top_k=top_k,
        preview_unique=preview_unique,
    )

    audit_df = pd.DataFrame(audit.get("value_counts", []))

    # --- resumo completo para a UI (sem mudar o renderer) ---
    n_rows = int(audit.get("n_rows", len(df)))
    n_unique = int(audit.get("nunique", 0))
    missing_count = int(audit.get("missing_count", 0))

    expected_list = list(expected_values) if expected_values is not None else None
    expected_set = set(expected_list) if expected_list is not None else None

    # "observed" vem do audit_target (uniques dropna) em formato original
    observed_raw = audit.get("unique_values_preview", [])
    # Para domínio observado completo, preferimos derivar da tabela (quando disponível)
    if not audit_df.empty and "value" in audit_df.columns:
        observed_values = [v for v in audit_df["value"].astype(str).tolist()]
    else:
        observed_values = [str(v) for v in observed_raw]

    invalid_count = 0
    if expected_set is not None:
        # audit_target stringifica na tabela; expected_values pode ser não-string.
        expected_str = set(map(str, expected_set))
        observed_str = set(map(str, observed_values))
        invalid_count = len([v for v in observed_str if v not in expected_str])

    return {
        "df": df,
        "scope": scope,
        "target": target,
        "audit": audit,
        "audit_df": audit_df,
        "meta": {
            "executed": True,
            "status": audit.get("status"),
            # chaves que o renderer já tenta ler:
            "n_rows": n_rows,
            "n_unique": n_unique,
            "missing_count": missing_count,
            "invalid_count": int(invalid_count),
            "expected_values": expected_list,
            "observed_values": observed_values,
            # mantemos também as já existentes (compatibilidade):
            "missing_pct": audit.get("missing_pct"),
            "nunique": n_unique,
        },
    }



def _stringify_value(v: Any) -> str:
    """
    Converte um valor arbitrário em representação textual segura para auditoria e UI.

    Esta função tem finalidade **exclusivamente descritiva**, sendo utilizada para:
    - exibição de valores em relatórios auditáveis,
    - renderização em HTML/UI,
    - comparação visual de categorias observadas.

    Regras e garantias
    ------------------
    - **Não aplica normalização semântica** (não altera casing, não remove espaços, não converte tipos).
    - Preserva o significado original do dado, apenas o torna legível.
    - Trata explicitamente valores especiais comuns em pipelines de dados:
        - `None` → "None"
        - `NaN` (pandas) → "NaN"
    - Para qualquer outro tipo, utiliza `str(v)` como fallback seguro.

    Parâmetros
    ----------
    v : Any
        Valor bruto extraído do DataFrame (categoria, número, None, NaN, etc.).

    Retorna
    -------
    str
        Representação textual do valor, adequada para exibição em UI e logs auditáveis.
    """
    if v is None:
        return "None"
    # pandas NaN
    try:
        if pd.isna(v):
            return "NaN"
    except Exception:
        pass
    return str(v)
