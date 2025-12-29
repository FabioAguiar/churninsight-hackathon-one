# src/data/contract_loader.py
"""
ChurnInsight — Seção 3 (N1): Conformidade ao Contrato de Entrada (API),
Diagnóstico de Features & Padronização Categórica

Este módulo implementa o carregamento e validação leve do contrato de entrada
definido em YAML (ex.: `contract.yaml`), estabelecendo o elo formal entre:

- o contrato de entrada do endpoint `/predict` (FastAPI ↔ Java), e
- o pipeline de preparação de dados (Seção 3 — N1), que depende de:
  - `features` (colunas de entrada)
  - `target` (variável supervisionada)
  - `id_columns` (colunas identificadoras, opcionais)
  - `drop_columns` (colunas a remover, opcionais)

Objetivo
--------
- Garantir que o contrato seja carregado de forma robusta (resolução de caminho).
- Validar o mínimo necessário para evitar erros silenciosos no pipeline.
- Preservar rastreabilidade: o que foi declarado no YAML é mantido (ordem),
  com saneamento mínimo (dedupe) e checks de consistência.

Observações importantes
-----------------------
- A validação é propositalmente **leve** (mínimo viável), para não engessar
  evoluções do contrato durante iterações de produto.
- Este módulo **não** valida a existência das colunas no DataFrame; ele valida
  apenas o **contrato declarativo**. A conformidade estrutural (colunas presentes,
  ausentes e descartadas) é tratada por `src/features/contract_and_candidates.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml

from src.features.contract_and_candidates import NormalizationScope


# ============================================================
# Modelos / Estruturas de suporte
# ============================================================

@dataclass(frozen=True)
class ContractConfig:
    """
    Representa um contrato de entrada carregado de um arquivo YAML.

    Esta estrutura consolida o schema declarado em YAML e fornece um
    formato tipado e imutável para consumo no pipeline (Seção 3 — N1).

    Atributos
    ---------
    name : str
        Nome lógico do contrato (ex.: "telco-churn").
    version : int
        Versão do contrato. Útil para rastreabilidade e evolução controlada.
    features : list[str]
        Lista ordenada de colunas de entrada do endpoint `/predict`.
    target : str
        Nome da variável alvo supervisionada (ex.: "Churn").
    id_columns : list[str]
        Colunas identificadoras (opcional), úteis para rastreabilidade e joins.
    drop_columns : list[str]
        Colunas declaradas para remoção (opcional), fora do escopo do modelo.

    Observações
    -----------
    - A ordem declarada em `features` é preservada (após dedupe).
    - Este objeto não valida a existência das colunas em um DataFrame;
      validação de conformidade ocorre em etapa posterior do pipeline.
    """

    name: str
    version: int
    features: List[str]
    target: str
    id_columns: List[str]
    drop_columns: List[str]

    def to_scope(self) -> NormalizationScope:
        """
        Converte o contrato carregado para `NormalizationScope` (features/target).

        Esta conversão é utilizada para integrar o contrato YAML com a lógica
        de conformidade ao contrato e diagnóstico categórico implementada em
        `src/features/contract_and_candidates.py`.

        Retorna
        -------
        NormalizationScope
            Instância contendo `features` e `target` conforme definidos no contrato.
        """
        return NormalizationScope(features=list(self.features), target=str(self.target))


# ============================================================
# API pública
# ============================================================

def load_contract_yaml(path: str | Path) -> ContractConfig:
    """
    Carrega um contrato YAML e retorna um `ContractConfig` validado (mínimo viável).

    Esta função realiza:
    1) Resolução robusta de caminho (absoluto vs relativo, com fallback para root do projeto).
    2) Leitura do YAML (safe_load).
    3) Validação leve dos campos essenciais do contrato.
    4) Saneamento mínimo (dedupe preservando ordem).
    5) Checks de consistência básicos (ex.: target não pode estar em features).

    Regras mínimas de validação
    ---------------------------
    - `schema.target`: obrigatório (string não vazia)
    - `schema.features`: obrigatório (lista de strings não vazia)
    - `schema.id_columns`: opcional (lista de strings)
    - `schema.drop_columns`: opcional (lista de strings)
    - `name`: opcional (fallback para o stem do arquivo)
    - `version`: opcional (default = 1)

    Resolução de caminho (robusta)
    ------------------------------
    - Se `path` for absoluto: usa diretamente.
    - Se `path` for relativo:
      1) tenta resolver relativo ao diretório atual (cwd)
      2) se não existir, tenta resolver relativo ao root do projeto (detectado
         subindo diretórios até encontrar uma pasta `src/`).

    Parâmetros
    ----------
    path : str | pathlib.Path
        Caminho para o arquivo YAML de contrato (ex.: "contract.yaml").

    Retorna
    -------
    ContractConfig
        Contrato carregado e validado (mínimo viável), pronto para consumo no pipeline.

    Exceções
    --------
    FileNotFoundError
        Se o arquivo de contrato não existir após resolução robusta.
    TypeError
        Se o YAML não possuir objeto raiz dict, ou se campos tiverem tipos inválidos.
    ValueError
        Se campos obrigatórios estiverem ausentes/vazios, ou se houver inconsistências
        básicas (ex.: target dentro de features).

    Observações
    -----------
    - A validação é propositalmente leve para permitir evolução do contrato.
    - Este carregador não valida conformidade com um DataFrame; ele valida apenas
      a estrutura declarativa do YAML.
    """
    p = _resolve_contract_path(path)
    if not p.exists():
        raise FileNotFoundError(f"Contract YAML não encontrado: {p}")

    data = _read_yaml(p)

    version = _as_int(data.get("version", 1), default=1)
    name = _as_str(data.get("name", p.stem), field="name")

    schema = data.get("schema", {})
    if not isinstance(schema, dict):
        raise TypeError("Campo 'schema' deve ser um objeto/dict no YAML.")

    target = _as_str(schema.get("target"), field="schema.target")
    features = _as_list_str(schema.get("features"), field="schema.features", allow_empty=False)

    id_columns = _as_list_str(schema.get("id_columns", []), field="schema.id_columns", allow_empty=True)
    drop_columns = _as_list_str(schema.get("drop_columns", []), field="schema.drop_columns", allow_empty=True)

    # Saneamento: dedupe preservando ordem (sem alterar muito o que foi declarado)
    features = _dedupe_preserve_order(features)
    id_columns = _dedupe_preserve_order(id_columns)
    drop_columns = _dedupe_preserve_order(drop_columns)

    # Sanity checks úteis (conservadores)
    if target in features:
        raise ValueError(
            "Contrato inválido: o target não deve estar dentro de schema.features. "
            f"target='{target}' apareceu em features."
        )

    return ContractConfig(
        name=name,
        version=version,
        features=features,
        target=target,
        id_columns=id_columns,
        drop_columns=drop_columns,
    )


# ============================================================
# Funções internas (helpers)
# ============================================================

def _detect_project_root(start: Path | None = None) -> Path:
    """
    Detecta o root do projeto subindo diretórios até encontrar uma pasta `src/`.

    Esta função implementa uma heurística simples e robusta para encontrar
    o diretório raiz do projeto sem depender de ajustes manuais de `sys.path`,
    funcionando bem em contextos como:
    - execução via notebook dentro de subpastas (ex.: `notebooks/`)
    - execução via scripts dentro de `src/`
    - execução via CLI com cwd variando

    Parâmetros
    ----------
    start : pathlib.Path | None, opcional
        Diretório inicial para a busca. Se None, utiliza `Path.cwd()`.

    Retorna
    -------
    pathlib.Path
        Caminho absoluto (resolve) para o root do projeto detectado.

    Observações
    -----------
    - A heurística considera que a presença de uma pasta `src/` indica o root.
    - Se nenhuma pasta `src/` for encontrada até a raiz do filesystem, retorna
      o diretório superior mais alto alcançado (comportamento conservador).
    """
    root = (start or Path.cwd()).resolve()
    while not (root / "src").exists() and root.parent != root:
        root = root.parent
    return root


def _resolve_contract_path(path: str | Path) -> Path:
    """
    Resolve o caminho do contrato de forma robusta.

    Estratégia
    ----------
    - Se `path` for absoluto: retorna `resolve()` do próprio caminho.
    - Se `path` for relativo:
      1) tenta resolver relativo ao cwd atual
      2) se não existir, tenta resolver relativo ao root do projeto (via `src/`)

    Parâmetros
    ----------
    path : str | pathlib.Path
        Caminho fornecido pelo chamador.

    Retorna
    -------
    pathlib.Path
        Caminho absoluto (resolve) para o arquivo de contrato.
    """
    p = Path(path)

    if p.is_absolute():
        return p.resolve()

    # 1) relativo ao cwd atual
    p1 = (Path.cwd() / p).resolve()
    if p1.exists():
        return p1

    # 2) relativo ao root do projeto
    project_root = _detect_project_root()
    p2 = (project_root / p).resolve()
    return p2


def _read_yaml(path: Path) -> Dict[str, Any]:
    """
    Lê um arquivo YAML e retorna o objeto raiz como dict.

    Parâmetros
    ----------
    path : pathlib.Path
        Caminho do arquivo YAML.

    Retorna
    -------
    dict[str, Any]
        Objeto raiz do YAML. Se o YAML estiver vazio, retorna `{}`.

    Exceções
    --------
    TypeError
        Se o YAML não contiver um objeto raiz do tipo dict.

    Observações
    -----------
    - A leitura utiliza `yaml.safe_load` por segurança.
    - Este helper não valida schema; apenas garante o formato raiz esperado.
    """
    with path.open("r", encoding="utf-8") as f:
        obj = yaml.safe_load(f)

    if obj is None:
        return {}

    if not isinstance(obj, dict):
        raise TypeError("O YAML deve ter um objeto raiz (dict).")

    return obj


def _as_str(value: Any, *, field: str) -> str:
    """
    Valida e normaliza um campo obrigatório do tipo string.

    Parâmetros
    ----------
    value : Any
        Valor de entrada (possivelmente None).
    field : str
        Nome lógico do campo para mensagens de erro (ex.: "schema.target").

    Retorna
    -------
    str
        String normalizada (`strip()`), garantidamente não vazia.

    Exceções
    --------
    ValueError
        Se `value` for None (campo obrigatório ausente).
    TypeError
        Se `value` não for string ou for string vazia/apenas espaços.
    """
    if value is None:
        raise ValueError(f"Campo obrigatório ausente: '{field}'.")

    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"Campo '{field}' deve ser uma string não vazia.")

    return value.strip()


def _as_int(value: Any, *, default: int) -> int:
    """
    Converte um valor para inteiro com fallback explícito.

    Parâmetros
    ----------
    value : Any
        Valor a ser convertido para int. Se None, retorna `default`.
    default : int
        Valor padrão quando `value` for None.

    Retorna
    -------
    int
        Valor convertido para inteiro.

    Exceções
    --------
    TypeError
        Se `value` não puder ser convertido para int.
    """
    if value is None:
        return int(default)

    try:
        return int(value)
    except Exception as e:
        raise TypeError(f"Campo 'version' deve ser inteiro. Recebido: {value!r}") from e


def _as_list_str(value: Any, *, field: str, allow_empty: bool) -> List[str]:
    """
    Valida e normaliza um campo do tipo lista de strings.

    Parâmetros
    ----------
    value : Any
        Valor a ser validado. Espera-se `list[str]` (ou None, dependendo de `allow_empty`).
    field : str
        Nome lógico do campo para mensagens de erro (ex.: "schema.features").
    allow_empty : bool
        Se False, a lista não pode ser vazia (ex.: `schema.features`).
        Se True, lista vazia é permitida (ex.: `schema.drop_columns`).

    Retorna
    -------
    list[str]
        Lista de strings normalizadas (`strip()`), garantidamente não vazias.

    Exceções
    --------
    ValueError
        Se `value` for None e `allow_empty=False`, ou se a lista resultar vazia quando
        `allow_empty=False`.
    TypeError
        Se `value` não for list, ou se algum item não for string não vazia.
    """
    if value is None:
        if allow_empty:
            return []
        raise ValueError(f"Campo obrigatório ausente: '{field}'.")

    if not isinstance(value, list):
        raise TypeError(f"Campo '{field}' deve ser uma lista.")

    out: List[str] = []
    for i, v in enumerate(value):
        if not isinstance(v, str) or not v.strip():
            raise TypeError(f"Campo '{field}[{i}]' deve ser string não vazia.")
        out.append(v.strip())

    if not allow_empty and len(out) == 0:
        raise ValueError(f"Campo '{field}' não pode ser vazio.")

    return out


def _dedupe_preserve_order(items: Sequence[str]) -> List[str]:
    """
    Remove duplicatas preservando a ordem original dos itens.

    Este helper é utilizado para saneamento mínimo do contrato, evitando:
    - duplicações acidentais em `features`, `id_columns` ou `drop_columns`
    - reordenação silenciosa das listas declaradas no YAML

    Parâmetros
    ----------
    items : Sequence[str]
        Sequência de strings a ser deduplicada.

    Retorna
    -------
    list[str]
        Lista deduplicada, preservando a ordem do primeiro aparecimento.

    Observações
    -----------
    - A deduplicação é case-sensitive e não altera valores (apenas remove repetições).
    """
    seen = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out
