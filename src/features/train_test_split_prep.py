# src/features/train_test_split_prep.py
"""
ChurnInsight — Seção 5 (N1)
Preparação para Modelagem Supervisionada — Execução Core

Este módulo implementa a **API core da Seção 5** do pipeline ChurnInsight,
responsável por materializar decisões explícitas de preparação estrutural
para modelagem supervisionada.

Seu escopo é estritamente delimitado à execução **irreversível e auditável**
das seguintes operações:

- separação explícita entre features (X) e target (y), conforme o
  contrato semântico definido em `NormalizationScope`
- aplicação do split treino/teste, com parâmetros **integralmente
  declarados no notebook**, sem defaults implícitos
- geração de diagnósticos estruturais pós-split, utilizados
  exclusivamente para auditoria e visualização

Nenhuma decisão de modelagem é tomada neste módulo.

Regras inegociáveis
-------------------
- ❌ Não realiza encoding de features
- ❌ Não realiza scaling ou normalização
- ❌ Não treina modelos
- ❌ Não transforma ou codifica a variável alvo (target)
- ❌ Não infere parâmetros de split (ex.: estratificação nunca é assumida)
- ✔️ Falha de forma explícita e antecipada se a decisão fornecida
  estiver incompleta ou inconsistente

Princípios de design
--------------------
- Separação clara entre decisão e execução
- Ausência total de transformações silenciosas
- Produção de artefatos diagnósticos objetivos
- Reprodutibilidade e rastreabilidade do split

Filosofia do pipeline
---------------------
diagnóstico → decisão explícita → execução → auditoria

Este módulo atua como **checkpoint formal** do pipeline, garantindo que
a transição entre dados auditados (Seções 1–4) e dados modeláveis
(Seção 6 em diante) ocorra apenas quando a integridade estrutural
estiver explicitamente documentada.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import pandas as pd

from src.features.contract_and_candidates import NormalizationScope


# ------------------------------------------------------------
# API pública (core)
# ------------------------------------------------------------
def run_train_test_split(
    df: pd.DataFrame,
    scope: NormalizationScope,
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executa a separação estrutural X/y e o split treino/teste
    de forma explícita, auditável e semanticamente controlada.

    Esta é a **API pública (core)** da Seção 5 do pipeline
    (Preparação para Modelagem). Sua responsabilidade é
    **materializar decisões declaradas no notebook**, sem
    inferências automáticas ou defaults ocultos, e produzir
    um payload completo para auditoria e visualização.

    A função consolida, em um único ponto:
    - a separação explícita entre features e target
    - a aplicação irreversível do split treino/teste
    - a geração de diagnósticos estruturais auditáveis

    Nenhuma decisão de modelagem é tomada nesta etapa.

    IMPORTANTE
    ----------
    - O DataFrame de entrada **não é modificado**.
    - Nenhuma transformação de valores é aplicada.
    - Nenhuma inferência sobre encoding, scaling ou balanceamento é realizada.
    - Todos os parâmetros de split devem ser explicitamente fornecidos em `decision`.

    Pré-requisitos invariáveis
    --------------------------
    - O `df` deve estar no estado final da Seção 4.
    - O `scope` deve refletir exatamente o contrato de entrada da API.
    - O `decision` deve ter sido declarado explicitamente no notebook.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame no estado final da Seção 4 (pré-requisito invariável),
        já validado estruturalmente e semanticamente.

    scope : NormalizationScope
        Escopo semântico que define explicitamente:
        - `features`: lista ordenada de colunas de entrada
        - `target`: nome da variável alvo

    decision : Dict[str, Any]
        Decisão explícita do split treino/teste.
        Nenhum default implícito é aplicado.

        Campos obrigatórios:
        - test_size : float (entre 0 e 1) ou int (>= 1)
        - random_state : int
        - shuffle : bool
        - stratify : bool

        Campos condicionais:
        - stratify_col : str
          Obrigatório apenas se `stratify=True`

        Campo opcional:
        - audit_categorical_cardinality : bool
          Ativa a geração do diagnóstico [S5.5] se True

    Retorno
    -------
    Dict[str, Any]
        Payload consolidado conforme o contrato canônico da Seção 5 ([S5.0]),
        contendo:

        - df :
            DataFrame original de entrada da Seção 5 (não modificado)

        - scope :
            Escopo semântico utilizado na execução

        - decision :
            Decisão explícita aplicada ao split

        - split :
            Dicionário contendo:
            - X_train : DataFrame de features de treino
            - X_test : DataFrame de features de teste
            - y_train : Série do target de treino
            - y_test : Série do target de teste

        - diagnostics :
            Dicionário de artefatos auditáveis contendo:
            - shapes : relatório estrutural dos subconjuntos
            - target_distribution : distribuição do target (pré vs pós-split)
            - risk_checks : diagnósticos objetivos de integridade estrutural
            - categorical_cardinality : relatório opcional de cardinalidade categórica

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - API core invocada pelo notebook principal
    - Base para renderização dos Cards [S5.1] a [S5.5]

    Este payload garante que o pipeline só avance para
    etapas de representação e modelagem quando a separação
    estrutural estiver **explicitamente documentada e auditada**.
    """
    # Validações (fail fast)
    _validate_scope(df, scope)
    _validate_decision(decision, scope)

    # Separação explícita X / y (sem transformar valores)
    X, y = _split_X_y(df, scope)

    # Estratificação: somente se decidida explicitamente
    stratify_series = None
    if decision.get("stratify") is True:
        # Mantém compatível com o contrato: stratify_col deve ser declarado
        stratify_col = decision.get("stratify_col", scope.target)
        # Por design, no ChurnInsight a estratificação deve ser pelo target
        # (a validação garante coerência com scope.target)
        stratify_series = df.loc[:, stratify_col].copy()

    # Split supervisionado (irreversível, sem defaults ocultos)
    X_train, X_test, y_train, y_test = _apply_train_test_split(
        X=X,
        y=y,
        decision=decision,
        stratify_series=stratify_series,
    )

    # Diagnósticos auditáveis (sem interpretação)
    shapes = _build_shapes(X_train, X_test, y_train, y_test, scope)

    target_distribution = _build_target_distribution(
        y_all=y,
        y_train=y_train,
        y_test=y_test,
        target_name=scope.target,
    )

    risk_checks = _build_risk_checks(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        scope=scope,
    )

    # Diagnóstico opcional (explicitamente ligado à decision)
    audit_cat = bool(decision.get("audit_categorical_cardinality", False))
    categorical_cardinality = _build_categorical_cardinality(X_train, X_test) if audit_cat else None

    diagnostics: Dict[str, Any] = {
        "shapes": shapes,
        "target_distribution": target_distribution,
        "risk_checks": risk_checks,
    }
    if audit_cat:
        diagnostics["categorical_cardinality"] = categorical_cardinality

    # Payload canônico [S5.0]
    return {
        "df": df,  # dataset de entrada da Seção 5 (não modificado)
        "scope": scope,
        "decision": decision,
        "split": {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
        },
        "diagnostics": diagnostics,
    }



# ------------------------------------------------------------
# Validações (conservadoras)
# ------------------------------------------------------------
def _split_X_y(
    df: pd.DataFrame,
    scope: NormalizationScope,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Realiza a separação explícita entre features (X) e target (y)
    com base no escopo definido no contrato.

    Esta função executa uma **separação estrutural e determinística**
    do dataset, utilizada na Seção 5 do pipeline (Preparação para Modelagem),
    com o objetivo de materializar a distinção entre variáveis de entrada
    e variável alvo antes da aplicação do split treino/teste.

    Nenhuma transformação é aplicada aos dados.
    A função apenas **seleciona e isola** colunas conforme o contrato.

    IMPORTANTE
    ----------
    - Esta função **não valida tipos**.
    - Esta função **não altera valores**.
    - Esta função **não decide** quais colunas são features ou target.
    - Toda a definição semântica provém exclusivamente do `scope`.

    A separação realizada aqui é um **pré-requisito estrutural**
    para qualquer etapa supervisionada subsequente.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame completo no estado atual do pipeline,
        já validado estruturalmente nas seções anteriores.

    scope : NormalizationScope
        Objeto de contrato que define explicitamente:
        - `features`: conjunto ordenado de colunas de entrada
        - `target`: coluna correspondente à variável alvo

    Retorno
    -------
    Tuple[pd.DataFrame, pd.Series]
        Tupla contendo:
        - X : DataFrame com as features, na ordem definida pelo escopo
        - y : Série correspondente ao target

        Ambos os objetos são retornados como cópias independentes
        do DataFrame original, evitando efeitos colaterais.

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Etapa de separação estrutural X / y

    Esta função garante que a distinção entre dados de entrada
    e variável supervisionada seja **explícita, rastreável
    e alinhada ao contrato**, antes de qualquer decisão irreversível.
    """
    if scope is None or not isinstance(scope, NormalizationScope):
        raise TypeError("scope deve ser uma instância de NormalizationScope (obrigatório na Seção 5).")

    if not isinstance(scope.features, list) or not all(isinstance(c, str) for c in scope.features):
        raise ValueError("scope.features deve ser list[str].")

    if not isinstance(scope.target, str) or not scope.target.strip():
        raise ValueError("scope.target deve ser uma string não vazia.")

    missing_feats = [c for c in scope.features if c not in df.columns]
    if missing_feats:
        raise ValueError(f"scope.features contém colunas ausentes no df: {missing_feats}")

    if scope.target not in df.columns:
        raise ValueError(f"Target '{scope.target}' não existe no df.")

    # Garantia adicional: target não pode estar dentro de features
    if scope.target in scope.features:
        raise ValueError(f"Target '{scope.target}' não pode constar em scope.features.")


def _validate_scope(df: pd.DataFrame, scope: NormalizationScope) -> None:
    """
    Valida o escopo semântico (`NormalizationScope`) contra o DataFrame de entrada.

    Esta validação é **estrutural e conservadora**: ela não interpreta dados,
    não corrige inconsistências e não aplica defaults. Ela apenas garante que
    o contrato mínimo para a Seção 5 está presente antes de executar qualquer
    decisão irreversível (split).

    Regras canônicas
    ---------------
    - `scope` deve ser instância de `NormalizationScope`
    - `scope.features` deve ser `list[str]` (ordem é relevante)
    - `scope.target` deve ser `str` não vazia
    - Todas as colunas de `scope.features` devem existir em `df`
    - `scope.target` deve existir em `df`
    - `scope.target` **não pode** estar contido em `scope.features`

    Falha cedo (fail fast)
    ----------------------
    Se qualquer condição falhar, lança exceção explícita, pois o pipeline
    não deve avançar para split em estado inconsistente.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame.")

    if scope is None or not isinstance(scope, NormalizationScope):
        raise TypeError("scope deve ser uma instância de NormalizationScope (obrigatório na Seção 5).")

    if not isinstance(scope.features, list) or not all(isinstance(c, str) for c in scope.features):
        raise ValueError("scope.features deve ser list[str].")

    if not isinstance(scope.target, str) or not scope.target.strip():
        raise ValueError("scope.target deve ser uma string não vazia.")

    missing_feats = [c for c in scope.features if c not in df.columns]
    if missing_feats:
        raise ValueError(f"scope.features contém colunas ausentes no df: {missing_feats}")

    if scope.target not in df.columns:
        raise ValueError(f"Target '{scope.target}' não existe no df.")

    if scope.target in scope.features:
        raise ValueError(f"Target '{scope.target}' não pode constar em scope.features.")


def _split_X_y(df: pd.DataFrame, scope: NormalizationScope) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separa explicitamente X (features) e y (target) conforme o escopo.

    Esta função **não valida o escopo** (isso é responsabilidade de `_validate_scope`)
    e **não transforma valores**: ela apenas seleciona colunas e retorna cópias.

    Retorna
    -------
    (X, y)
        - X: DataFrame com as features na ordem definida em `scope.features`
        - y: Series com o target definido em `scope.target`
    """
    X = df.loc[:, scope.features].copy()
    y = df.loc[:, scope.target].copy()
    return X, y


def run_train_test_split(
    df: pd.DataFrame,
    scope: NormalizationScope,
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executa a separação estrutural X/y e o split treino/teste
    de forma explícita, auditável e semanticamente controlada.

    (docstring mantido como você já construiu; abaixo, apenas a execução)
    """
    # Validações (fail fast)
    _validate_scope(df, scope)
    _validate_decision(decision, scope)

    # Separação explícita X / y (sem transformar valores)
    X, y = _split_X_y(df, scope)

    # Estratificação: somente se decidida explicitamente
    stratify_series = None
    if decision.get("stratify") is True:
        stratify_col = decision.get("stratify_col", scope.target)
        stratify_series = df.loc[:, stratify_col].copy()

    # Split supervisionado (irreversível, sem defaults ocultos)
    X_train, X_test, y_train, y_test = _apply_train_test_split(
        X=X,
        y=y,
        decision=decision,
        stratify_series=stratify_series,
    )

    # Diagnósticos auditáveis (sem interpretação)
    shapes = _build_shapes(X_train, X_test, y_train, y_test, scope)

    target_distribution = _build_target_distribution(
        y_all=y,
        y_train=y_train,
        y_test=y_test,
        target_name=scope.target,
    )

    risk_checks = _build_risk_checks(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        scope=scope,
    )

    # Diagnóstico opcional (explicitamente ligado à decision)
    audit_cat = bool(decision.get("audit_categorical_cardinality", False))
    categorical_cardinality = _build_categorical_cardinality(X_train, X_test) if audit_cat else None

    diagnostics: Dict[str, Any] = {
        "shapes": shapes,
        "target_distribution": target_distribution,
        "risk_checks": risk_checks,
    }
    if audit_cat:
        diagnostics["categorical_cardinality"] = categorical_cardinality

    # Payload canônico [S5.0]
    return {
        "df": df,  # dataset de entrada da Seção 5 (não modificado)
        "scope": scope,
        "decision": decision,
        "split": {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
        },
        "diagnostics": diagnostics,
    }



def _validate_decision(decision: Dict[str, Any], scope: NormalizationScope) -> None:
    """
    Valida a decisão explícita de split (Seção 5) sem aplicar defaults implícitos.

    Regras canônicas
    ----------------
    - Nenhum parâmetro é inferido: os campos obrigatórios devem existir em `decision`.
    - `stratify_col` só é permitido (e obrigatório) quando `stratify=True`.
    - Por design do ChurnInsight, a estratificação deve ser feita pelo target:
      `stratify_col` deve ser igual a `scope.target` (quando aplicável).
    - `audit_categorical_cardinality` é opcional, mas se fornecido deve ser bool.

    Campos obrigatórios
    -------------------
    - test_size : float (0,1) ou int (>=1)
    - random_state : int
    - shuffle : bool
    - stratify : bool

    Campos condicionais
    -------------------
    - stratify_col : str (obrigatório somente se stratify=True)

    Campos opcionais
    ----------------
    - audit_categorical_cardinality : bool
    """
    if decision is None or not isinstance(decision, dict):
        raise TypeError("decision deve ser um dicionário.")

    if scope is None:
        raise TypeError("scope não pode ser None.")

    # -------------------------
    # Campos obrigatórios
    # -------------------------
    required = ["test_size", "random_state", "shuffle", "stratify"]
    missing = [k for k in required if k not in decision]
    if missing:
        raise KeyError(f"Campos obrigatórios ausentes em decision: {missing}")

    # -------------------------
    # test_size
    # -------------------------
    test_size = decision["test_size"]
    if not isinstance(test_size, (float, int)):
        raise TypeError("decision['test_size'] deve ser float (0-1) ou int (>=1).")

    if isinstance(test_size, float):
        # sklearn aceita 0 < test_size < 1 quando float
        if not (0.0 < test_size < 1.0):
            raise ValueError("Se float, decision['test_size'] deve estar entre 0 e 1 (exclusivo).")

    if isinstance(test_size, int):
        # sklearn aceita int >= 1 (número absoluto de amostras)
        if test_size < 1:
            raise ValueError("Se int, decision['test_size'] deve ser >= 1.")

    # -------------------------
    # random_state
    # -------------------------
    random_state = decision["random_state"]
    if not isinstance(random_state, int):
        raise TypeError("decision['random_state'] deve ser int.")

    # -------------------------
    # shuffle
    # -------------------------
    shuffle = decision["shuffle"]
    if not isinstance(shuffle, bool):
        raise TypeError("decision['shuffle'] deve ser bool.")

    # -------------------------
    # stratify
    # -------------------------
    stratify = decision["stratify"]
    if not isinstance(stratify, bool):
        raise TypeError("decision['stratify'] deve ser bool.")

    # -------------------------
    # stratify_col (condicional)
    # -------------------------
    has_stratify_col = "stratify_col" in decision and decision.get("stratify_col") is not None

    if stratify is True:
        if not has_stratify_col:
            raise KeyError("decision['stratify_col'] é obrigatório quando stratify=True.")

        stratify_col = decision["stratify_col"]
        if not isinstance(stratify_col, str) or not stratify_col.strip():
            raise TypeError("decision['stratify_col'] deve ser uma string não vazia.")

        # Regra semântica do pipeline: estratificação deve ser pelo target
        if stratify_col != scope.target:
            raise ValueError(
                "No ChurnInsight, decision['stratify_col'] deve ser igual ao scope.target "
                f"('{scope.target}')."
            )
    else:
        # Evita ambiguidade: não permitir stratify_col quando stratify=False
        if has_stratify_col:
            raise ValueError("decision['stratify_col'] não deve ser fornecido quando stratify=False.")

    # -------------------------
    # audit_categorical_cardinality (opcional)
    # -------------------------
    if "audit_categorical_cardinality" in decision:
        acc = decision["audit_categorical_cardinality"]
        if not isinstance(acc, bool):
            raise TypeError("decision['audit_categorical_cardinality'] deve ser bool.")


# ------------------------------------------------------------
# Execução: separação + split
# ------------------------------------------------------------
def _split_X_y(
    df: pd.DataFrame,
    scope: NormalizationScope,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Realiza a separação explícita entre features (X) e target (y)
    com base no escopo definido no contrato.

    Esta função executa uma **separação estrutural e determinística**
    do dataset, utilizada na Seção 5 do pipeline (Preparação para Modelagem),
    com o objetivo de materializar a distinção entre variáveis de entrada
    e variável alvo antes da aplicação do split treino/teste.

    Nenhuma transformação é aplicada aos dados.
    A função apenas **seleciona e isola** colunas conforme o contrato.

    IMPORTANTE
    ----------
    - Esta função **não valida tipos**.
    - Esta função **não altera valores**.
    - Esta função **não decide** quais colunas são features ou target.
    - Toda a definição semântica provém exclusivamente do `scope`.

    A separação realizada aqui é um **pré-requisito estrutural**
    para qualquer etapa supervisionada subsequente.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame completo no estado atual do pipeline,
        já validado estruturalmente nas seções anteriores.

    scope : NormalizationScope
        Objeto de contrato que define explicitamente:
        - `features`: conjunto ordenado de colunas de entrada
        - `target`: coluna correspondente à variável alvo

    Retorno
    -------
    Tuple[pd.DataFrame, pd.Series]
        Tupla contendo:
        - X : DataFrame com as features, na ordem definida pelo escopo
        - y : Série correspondente ao target

        Ambos os objetos são retornados como cópias independentes
        do DataFrame original, evitando efeitos colaterais.

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Etapa de separação estrutural X / y

    Esta função garante que a distinção entre dados de entrada
    e variável supervisionada seja **explícita, rastreável
    e alinhada ao contrato**, antes de qualquer decisão irreversível.
    """
    X = df.loc[:, scope.features].copy()
    y = df.loc[:, scope.target].copy()
    return X, y


def _apply_train_test_split(
    *,
    X: pd.DataFrame,
    y: pd.Series,
    decision: Dict[str, Any],
    stratify_series: Optional[pd.Series],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Aplica a separação treino/teste sobre features e target
    com base em uma decisão explicitamente declarada.

    Esta função executa a **ação irreversível** central da Seção 5
    do pipeline (Preparação para Modelagem): a divisão do dataset
    em conjuntos de treino e teste para aprendizado supervisionado.

    A função é deliberadamente restritiva:
    - nenhum parâmetro possui valor default implícito
    - todos os argumentos são derivados explicitamente do dicionário `decision`
    - a lógica de estratificação é decidida fora desta função

    Nenhuma inferência automática é realizada.

    IMPORTANTE
    ----------
    - Esta função **não valida** se a decisão é adequada.
    - Esta função **não avalia** impacto estatístico do split.
    - Esta função **não corrige** desbalanceamento ou leakage.
    - O split realizado aqui é **irreversível** no contexto do pipeline.

    Parâmetros
    ----------
    X : pd.DataFrame
        DataFrame contendo exclusivamente as features de entrada,
        já conforme o escopo definido para modelagem.

    y : pd.Series
        Série correspondente à variável alvo (target),
        ainda não codificada ou transformada.

    decision : Dict[str, Any]
        Dicionário de decisão explícita contendo, no mínimo:
        - test_size : float
        - random_state : int
        - shuffle : bool

        A presença de estratificação é resolvida externamente
        e refletida apenas via `stratify_series`.

    stratify_series : Optional[pd.Series]
        Série utilizada para estratificação do split.
        Deve ser:
        - a própria série do target, se estratificação for desejada
        - None, caso a decisão explícita seja não estratificar

    Retorno
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]
        Tupla contendo, nesta ordem:
        - X_train : features de treino
        - X_test : features de teste
        - y_train : target de treino
        - y_test : target de teste

        Todos os objetos retornados preservam a ordem e
        a integridade estrutural esperadas pelo pipeline.

    Dependências
    ------------
    - scikit-learn (sklearn.model_selection.train_test_split)

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Etapa de execução do split supervisionado

    Esta função materializa a decisão declarada no notebook
    e viabiliza os diagnósticos estruturais subsequentes,
    sem antecipar qualquer decisão de modelagem.
    """
    try:
        from sklearn.model_selection import train_test_split
    except Exception as e:
        raise RuntimeError(
            "scikit-learn é necessário para executar train_test_split na Seção 5."
        ) from e

    # Nenhum default oculto: tudo vem de decision
    return train_test_split(
        X,
        y,
        test_size=decision["test_size"],
        random_state=decision["random_state"],
        shuffle=decision["shuffle"],
        stratify=stratify_series,
    )


# ------------------------------------------------------------
# Diagnósticos (auditáveis, sem interpretação)
# ------------------------------------------------------------
def _build_shapes(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    scope: NormalizationScope,
) -> Dict[str, Any]:
    """
    Constrói um relatório estrutural de shapes dos conjuntos
    de treino e teste após o split supervisionado.

    Esta função gera um **artefato puramente diagnóstico**, utilizado
    na Seção 5 do pipeline (Preparação para Modelagem), com o objetivo
    de tornar explícita a estrutura dimensional dos dados após a
    separação entre features (X) e target (y).

    O relatório permite verificar, de forma objetiva:
    - o número de registros em cada subconjunto
    - a dimensionalidade das features
    - a consistência entre os conjuntos de treino e teste
    - a aderência estrutural ao escopo definido para modelagem

    Nenhuma interpretação, validação ou correção é realizada.
    O output serve exclusivamente para **exposição explícita do estado estrutural**.

    IMPORTANTE
    ----------
    - Esta função **não avalia qualidade estatística**.
    - Esta função **não interpreta proporções ou equilíbrio**.
    - Nenhuma ação corretiva é sugerida ou aplicada.
    - O relatório **não implica** prontidão para modelagem,
      apenas descreve a estrutura atual dos dados.

    Parâmetros
    ----------
    X_train : pd.DataFrame
        Conjunto de features destinado ao treinamento, já conforme
        o escopo de modelagem definido no contrato.

    X_test : pd.DataFrame
        Conjunto de features destinado ao teste, com as mesmas
        colunas e ordem esperadas em X_train.

    y_train : pd.Series
        Série do target correspondente ao conjunto de treino.

    y_test : pd.Series
        Série do target correspondente ao conjunto de teste.

    scope : NormalizationScope
        Objeto de contrato que define explicitamente:
        - o conjunto de features válidas
        - a cardinalidade esperada de features após o split

    Retorno
    -------
    Dict[str, Any]
        Dicionário estruturado contendo:
        - X_train : {rows, cols}
        - X_test : {rows, cols}
        - y_train : {rows}
        - y_test : {rows}
        - n_features : número de features conforme o escopo

        Todos os valores são inteiros e representam apenas
        **dimensões estruturais**, não conteúdo dos dados.

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Card [S5.2] — Shapes de Treino e Teste

    Este artefato garante que a separação estrutural
    entre dados de treino e teste esteja explicitamente
    documentada antes de qualquer decisão de modelagem.
    """
    return {
        "X_train": {"rows": int(X_train.shape[0]), "cols": int(X_train.shape[1])},
        "X_test": {"rows": int(X_test.shape[0]), "cols": int(X_test.shape[1])},
        "y_train": {"rows": int(y_train.shape[0])},
        "y_test": {"rows": int(y_test.shape[0])},
        "n_features": int(len(scope.features)),
    }


def _build_target_distribution(
    *,
    y_all: pd.Series,
    y_train: pd.Series,
    y_test: pd.Series,
    target_name: str,
) -> pd.DataFrame:
    """
    Constrói um relatório de distribuição do target antes e após
    a aplicação do split treino/teste.

    Esta função gera um **artefato diagnóstico e auditável** utilizado
    na Seção 5 do pipeline (Preparação para Modelagem), com o objetivo de
    tornar explícito o impacto estrutural do split sobre a distribuição
    da variável alvo.

    O relatório permite comparar:
    - a distribuição global do target
    - a distribuição no conjunto de treino
    - a distribuição no conjunto de teste
    - o desvio relativo introduzido pelo split

    Nenhuma interpretação ou correção é realizada.
    O output serve exclusivamente para **exposição explícita dos números**.

    IMPORTANTE
    ----------
    - Esta função **não avalia qualidade do split**.
    - Esta função **não decide se o desvio é aceitável ou não**.
    - Esta função **não implica** que estratificação seja necessária.
    - Nenhuma ação corretiva é sugerida ou aplicada.

    Metodologia
    -----------
    Para cada conjunto (all, train, test), são calculados:
    - contagem absoluta por classe
    - proporção relativa (rate) em relação ao tamanho do conjunto

    Em seguida, são calculados os deltas:
    - delta_rate_train_vs_all
    - delta_rate_test_vs_all

    Estes valores indicam apenas a **variação relativa** causada pelo split.

    Parâmetros
    ----------
    y_all : pd.Series
        Série do target considerando o dataset completo, antes do split.

    y_train : pd.Series
        Série do target correspondente ao conjunto de treino.

    y_test : pd.Series
        Série do target correspondente ao conjunto de teste.

    target_name : str
        Nome canônico da variável alvo, utilizado para rotular
        semanticamente o índice do relatório.

    Retorno
    -------
    pd.DataFrame
        DataFrame estruturado contendo, para cada classe do target:
        - count_all : contagem total no dataset completo
        - rate_all : proporção relativa no dataset completo
        - count_train : contagem no conjunto de treino
        - rate_train : proporção relativa no conjunto de treino
        - count_test : contagem no conjunto de teste
        - rate_test : proporção relativa no conjunto de teste
        - delta_rate_train_vs_all : diferença entre rate_train e rate_all
        - delta_rate_test_vs_all : diferença entre rate_test e rate_all

        O índice do DataFrame é rotulado com o nome do target
        e posteriormente convertido em coluna.

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Card [S5.3] — Distribuição do Target (Pré vs Pós-Split)

    Este artefato garante que o impacto do split seja
    **explicitamente visível e auditável** antes de qualquer
    decisão de modelagem supervisionada.
    """
    def _dist(s: pd.Series) -> pd.DataFrame:
        vc = s.value_counts(dropna=False)
        total = float(len(s)) if len(s) > 0 else 1.0
        df_ = vc.rename("count").to_frame()
        df_["rate"] = df_["count"].astype(float) / total
        return df_

    all_df = _dist(y_all).rename(columns={"count": "count_all", "rate": "rate_all"})
    tr_df = _dist(y_train).rename(columns={"count": "count_train", "rate": "rate_train"})
    te_df = _dist(y_test).rename(columns={"count": "count_test", "rate": "rate_test"})

    out = all_df.join(tr_df, how="outer").join(te_df, how="outer").fillna(0)

    out["delta_rate_train_vs_all"] = out["rate_train"] - out["rate_all"]
    out["delta_rate_test_vs_all"] = out["rate_test"] - out["rate_all"]

    out.index.name = target_name
    return out.reset_index()


def _build_risk_checks(
    *,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    scope: NormalizationScope,
) -> Dict[str, Any]:
    """
    Constrói um conjunto de diagnósticos objetivos de risco estrutural
    após a aplicação do split treino/teste.

    Esta função produz **artefatos exclusivamente diagnósticos**, utilizados
    na Seção 5 do pipeline (Preparação para Modelagem), com o objetivo de
    verificar a integridade estrutural do dataset separado para treino
    supervisionado.

    Nenhuma interpretação, correção ou decisão automática é realizada.
    O resultado serve apenas para **exposição explícita de sinais de risco**.

    Tipos de risco avaliados
    ------------------------
    1. Integridade do escopo
       - Verifica se o target foi corretamente removido de X_train e X_test
       - Verifica se a ordem e o conjunto de colunas de X_train e X_test
         correspondem exatamente ao escopo de features definido no contrato

    2. Distribuição mínima do target
       - Calcula a menor taxa de ocorrência de classes no target
       - Avalia o conjunto total (treino + teste) e cada partição separadamente
       - O objetivo é sinalizar possíveis riscos de desbalanceamento severo,
         sem assumir que isso exige correção

    IMPORTANTE
    ----------
    - Esta função **não avalia performance**.
    - Esta função **não decide se há desbalanceamento aceitável ou não**.
    - Nenhuma ação corretiva é sugerida ou aplicada.
    - O output **não implica** que técnicas de balanceamento serão utilizadas.

    Parâmetros
    ----------
    X_train : pd.DataFrame
        Conjunto de features de treino após o split, já conforme
        o escopo de modelagem definido no contrato.

    X_test : pd.DataFrame
        Conjunto de features de teste após o split, com as mesmas
        colunas e ordem esperadas em X_train.

    y_train : pd.Series
        Série do target correspondente ao conjunto de treino.

    y_test : pd.Series
        Série do target correspondente ao conjunto de teste.

    scope : NormalizationScope
        Objeto de contrato que define explicitamente:
        - a coluna target
        - o conjunto e a ordem das features válidas para modelagem

    Retorno
    -------
    Dict[str, Any]
        Dicionário estruturado contendo dois blocos principais:

        - scope_integrity:
            * target_in_X_train : bool
            * target_in_X_test : bool
            * columns_match_scope_train : bool
            * columns_match_scope_test : bool

        - target_balance:
            * min_class_rate_all : float
            * min_class_rate_train : float
            * min_class_rate_test : float

        Estes valores devem ser interpretados apenas como
        **indicadores objetivos**, nunca como decisões.

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Card [S5.4] — Diagnóstico de Riscos Estruturais

    Este diagnóstico garante que o pipeline só avance para a etapa
    de representação e modelagem quando a integridade estrutural
    estiver explicitamente verificada.
    """
    # Checks objetivos: não interpretam, não corrigem.
    expected_cols = list(scope.features)

    columns_match_train = list(X_train.columns) == expected_cols
    columns_match_test = list(X_test.columns) == expected_cols

    target_in_X_train = scope.target in X_train.columns
    target_in_X_test = scope.target in X_test.columns

    def _min_class_rate(s: pd.Series) -> float:
        if len(s) == 0:
            return 0.0
        rates = s.value_counts(dropna=False) / float(len(s))
        return float(rates.min()) if len(rates) else 0.0

    return {
        "scope_integrity": {
            "target_in_X_train": bool(target_in_X_train),
            "target_in_X_test": bool(target_in_X_test),
            "columns_match_scope_train": bool(columns_match_train),
            "columns_match_scope_test": bool(columns_match_test),
        },
        "target_balance": {
            "min_class_rate_all": _min_class_rate(pd.concat([y_train, y_test], axis=0)),
            "min_class_rate_train": _min_class_rate(y_train),
            "min_class_rate_test": _min_class_rate(y_test),
        },
    }


def _build_categorical_cardinality(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame
) -> pd.DataFrame:
    """
    Constrói um relatório de cardinalidade categórica pós-split entre
    conjuntos de treino e teste.

    Esta função é utilizada exclusivamente como **artefato de auditoria**
    na Seção 5 do pipeline (Preparação para Modelagem), com o objetivo de
    diagnosticar riscos estruturais associados a variáveis categóricas
    após a aplicação do split treino/teste.

    O foco do relatório é identificar:
    - diferenças de cardinalidade entre treino e teste
    - categorias presentes apenas em um dos conjuntos
    - possíveis riscos para estratégias futuras de encoding (ex.: One-Hot)

    IMPORTANTE
    ----------
    - Esta função **não executa nenhuma transformação** nos dados.
    - Nenhuma decisão automática é tomada com base neste relatório.
    - O resultado é puramente diagnóstico e informativo.
    - O uso deste artefato **não implica** que encoding será aplicado
      posteriormente.

    Critério de identificação categórica
    ------------------------------------
    Uma coluna é considerada categórica se o dtype indicar:
    - object
    - string
    - category

    Todas as comparações são realizadas após:
    - remoção de valores nulos
    - conversão explícita dos valores para string (apenas para comparação)

    Parâmetros
    ----------
    X_train : pd.DataFrame
        Conjunto de features de treino após o split. Deve refletir
        exatamente o escopo definido para modelagem.

    X_test : pd.DataFrame
        Conjunto de features de teste após o split, com o mesmo
        conjunto de colunas de X_train.

    Retorno
    -------
    pd.DataFrame
        DataFrame ordenado contendo, para cada feature categórica:
        - feature : nome da coluna
        - n_unique_train : número de categorias distintas no treino
        - n_unique_test : número de categorias distintas no teste
        - n_only_in_test : categorias exclusivas do teste
        - n_only_in_train : categorias exclusivas do treino

        O resultado é ordenado priorizando:
        1. maior número de categorias exclusivas no teste
        2. menor cardinalidade no treino

    Uso no pipeline
    ---------------
    - Seção 5 — Preparação para Modelagem
    - Card [S5.5] — Cardinalidade Categórica Pós-Split

    Este artefato subsidia decisões futuras de representação,
    mas **não antecipa nenhuma delas**.
    """

    def _is_cat(s: pd.Series) -> bool:
        dt = str(s.dtype).lower()
        return ("object" in dt) or ("string" in dt) or ("category" in dt)

    cat_cols = [c for c in X_train.columns if _is_cat(X_train[c])]
    rows: List[Dict[str, Any]] = []

    for c in cat_cols:
        tr_vals = set(X_train[c].dropna().astype(str).unique().tolist())
        te_vals = set(X_test[c].dropna().astype(str).unique().tolist())

        rows.append({
            "feature": c,
            "n_unique_train": int(len(tr_vals)),
            "n_unique_test": int(len(te_vals)),
            "n_only_in_test": int(len(te_vals - tr_vals)),
            "n_only_in_train": int(len(tr_vals - te_vals)),
        })

    return pd.DataFrame(rows).sort_values(
        by=["n_only_in_test", "n_unique_train"],
        ascending=[False, True],
    ).reset_index(drop=True)
