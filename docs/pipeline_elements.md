# 📙 Referência Técnica dos Elementos do Pipeline — ChurnInsight

Este documento descreve a **lógica técnica por trás dos elementos exibidos no notebook principal** do projeto **ChurnInsight**.

Enquanto o arquivo `pipeline_notebook.md` apresenta o pipeline como uma **narrativa operacional**, este documento tem caráter **técnico**, explicando **o que cada elemento representa, como ele é obtido e quais contratos de UI ele consome**.

> 📌 A numeração e nomenclatura dos elementos seguem exatamente o que é apresentado no notebook, utilizando identificadores técnicos hierárquicos para permitir referência cruzada estável.

---

## 🧭 Como usar este documento

- Cada **subseção `[Sx.y]`** descreve **um único elemento visível no notebook**
- O objetivo é tornar explícita a **lógica técnica implícita** de cada elemento
- Este documento não descreve layout nem código linha a linha
- Ele deve ser lido como material de apoio ao pipeline visual
- Sempre que aplicável, cada elemento declara:
  - **Origem (core)**: funções que produzem o artefato
  - **Render (UI)**: funções que exibem o artefato
  - **Contrato de UI**: campos/colunas consumidos pelo renderer

---

## Correspondência Notebook ↔ Documento Técnico

Este documento (`pipeline_elements.md`) é a **fonte canônica técnica** dos elementos exibidos no `pipeline_notebook.md`.

A relação entre os dois artefatos segue estas regras:

- Todo **card/indicador/elemento** exibido no notebook possui uma seção `[Sx.y]` correspondente aqui.
- O notebook pode conter **elementos narrativos** (observações, transições, perguntas-guia) que não produzem payloads, mas possuem papel técnico explícito.
- Cada seção do notebook possui uma **Âncora visual canônica** (imagem) que funciona como **mapa visual** para interpretação dos elementos `[Sx.*]` descritos neste documento.

---

## Elementos Narrativos do Pipeline

Além dos elementos visuais (cards, indicadores e elementos), o pipeline reconhece **elementos narrativos formais** no notebook, utilizados para garantir clareza semântica e continuidade entre etapas.

Esses elementos **não produzem payloads**, mas possuem papel técnico explícito no pipeline.

### Tipo: Observação geral da seção

- Função: Consolidar o significado semântico dos cards apresentados e declarar o estado do dataset ao final da seção.
- Produz artefato: ❌ Não
- Impacta execução: ❌ Não
- Papel técnico: Contextualização e fechamento semântico.

### Tipo: Transição de seção

- Função: Declarar o estado do dataset ao final de uma etapa e justificar o avanço para a próxima.
- Produz artefato: ❌ Não
- Impacta execução: ❌ Não
- Papel técnico: Continuidade semântica e rastreabilidade do fluxo.

---

## Elementos de Execução Técnica Não-Visual (Sx.pre)

Algumas seções executam uma fase técnica obrigatória **antes** de renderizar qualquer elemento visual. Esses elementos são identificados pelo sufixo `.pre`.

Características:

- Não geram cards visuais
- Não possuem âncora visual própria
- São executados antes da renderização da seção correspondente
- Produzem dados intermediários consumidos pelos cards da seção

Exemplos (estado atual do pipeline):

- `S2.pre` — Validações estruturais e tipagem
- `S3.pre` — Aplicação de contrato, escopo e diagnóstico de features
- `S4.pre` — Preparação e execução de imputação auditável


# Seção 1 — Ingestão e Diagnóstico Inicial


### Correspondência com o Pipeline Visual

Esta seção corresponde diretamente à **Seção 1 — Ingestão** apresentada no arquivo `pipeline_notebook.md`.

- **Âncora visual canônica:** `./images/card_s1_ingestao_diagnostico_inicial.png`
- **Indexação visual:** Cards numerados de **1️⃣ a 5️⃣**
- **Função da âncora:** servir como **mapa visual** de referência para interpretação dos elementos desta seção (`[S1.*]`).

> 📌 A âncora visual não é decorativa: ela define o **espaço semântico e visual** no qual os elementos técnicos desta seção devem ser interpretados.

Esta seção documenta os elementos responsáveis por **descrever o estado inicial do dataset logo após a ingestão**, sem aplicar transformações ou pré-processamentos.

Os elementos aqui definidos têm caráter **informativo e diagnóstico**, servindo como base para todas as decisões técnicas subsequentes.

---

## [S1.1] Elemento — Arquivo

**Referência no pipeline visual:**  
Seção 1️⃣ → Identificação do Arquivo

### Finalidade

Indicar de forma explícita **qual arquivo de dados bruto** está sendo utilizado como fonte ativa do pipeline no momento da execução.

Este elemento permite que qualquer leitor identifique imediatamente a origem física dos dados utilizados.

### Origem dos dados

O valor exibido corresponde ao **nome do arquivo localizado no diretório `data/raw/`**, informado no momento da ingestão dos dados.

Esse nome é extraído diretamente do caminho do arquivo carregado, sem qualquer transformação.

### Funções envolvidas

```text
Origem (core)
src/data/load_data.py
- load_raw_data(...)
- _resolve_raw_dir(...)

Render (UI)
src/reporting/ui.py
- render_dataset_overview(...)
```

### Regras de obtenção

- O nome do arquivo pode ser definido explicitamente ou inferido quando há apenas um arquivo disponível.
- O valor exibido corresponde exatamente ao nome físico do arquivo carregado.
- Nenhuma modificação é aplicada ao nome para fins de exibição.

### Contrato de UI (campos consumidos)

- `render_dataset_overview(df=..., filename=resolved_filename, ...)`
- `filename` pode ser `None` → UI exibe placeholder `"—"`.

### Observações técnicas

- Elemento puramente informativo.
- Não influencia cálculos ou transformações.
- Estabelece rastreabilidade entre notebook e fonte de dados.

---

## [S1.2] Indicador — Faltantes (Global)

**Referência no pipeline visual:**  
Seção 1️⃣ → Indicador Global de Qualidade

### Finalidade

Fornecer uma **visão consolidada da presença de valores ausentes** no dataset recém-ingerido, funcionando como um indicador inicial e sintético de qualidade dos dados.

### Origem dos dados

Os valores são calculados diretamente a partir do **DataFrame ativo**, imediatamente após a ingestão, dentro da camada de UI.

### Funções envolvidas

```text
Render (UI)
src/reporting/ui.py
- render_dataset_overview(...)
- _missing_badge(...)

pandas
- DataFrame.isna()
- sum()
- shape
```

### Regras de obtenção / cálculo

O percentual global exibido é calculado exatamente como:

```text
overall_missing_pct = (df.isna().sum().sum() / (n_rows * max(n_cols, 1))) * 100
```

Blindagens/edge cases aplicados pelo renderer:

- Se `n_rows == 0` → `overall_missing_pct = 0.0`
- `max(n_cols, 1)` evita divisão por zero quando `n_cols == 0`

### Classificação de severidade (badge)

A severidade do badge é derivada por `_missing_badge(pct_missing, theme)`:

- **OK** — `pct_missing == 0`
- **Baixo** — `pct_missing > 0` e `pct_missing <= 5`
- **Alto** — `pct_missing > 5`

> Observação: estes limiares são heurísticos e existem para **sinalização visual**, não para decisões automáticas.

### Contrato de UI (campos consumidos)

- `df` (obrigatório)
- `theme` (opcional, default `DEFAULT_THEME`)
- Badge renderiza: `miss_label` + `overall_missing_pct` arredondado para 2 casas.

### Observações técnicas

- Indicador global não substitui análises por coluna.
- É calculado sobre **todas as células** do DataFrame (não por subconjunto).
- Limiares podem ser alterados sem impacto na camada de dados.

---

## [S1.3] Card — Métricas gerais

**Referência no pipeline visual:**  
Seção 1️⃣ → Métricas gerais

### Finalidade

Exibir métricas estruturais básicas que descrevem a **dimensão e composição geral** do dataset ingerido.

### Métricas incluídas (estado atual)

- Número de linhas (`n_rows`)
- Número de colunas (`n_cols`)
- Uso aproximado de memória (MB) com `deep=True`

### Funções envolvidas

```text
Render (UI)
src/reporting/ui.py
- render_dataset_overview(...)
- _human_mb(...)

pandas
- shape
- memory_usage(deep=True)
```

### Regras de obtenção / cálculo

- `n_rows, n_cols = df.shape`
- `mem_mb = _human_mb(int(df.memory_usage(deep=True).sum()))`
- Conversão MB (base binária): `bytes / 1024²`

### Contrato de UI (campos consumidos)

- `df` (obrigatório)
- Renderiza cards com `Linhas`, `Colunas`, `Memória`.

### Observações técnicas

- Métricas descritivas, não analíticas.
- Uso de memória é aproximado e depende de `deep=True`.

---

## [S1.4] Card — Tipos de dados

**Referência no pipeline visual:**  
Seção 1️⃣ → Tipos

### Finalidade

Apresentar um **resumo da tipagem das colunas**, permitindo compreender a estrutura do dataset e antecipar necessidades de pré-processamento.

### Estratégia de agrupamento

- Identificação do tipo de cada coluna via `df.dtypes.astype(str)`
- Agregação por dtype via `value_counts()`

### Funções envolvidas

```text
Render (UI)
src/reporting/ui.py
- _dtype_summary(...)
- render_dataset_overview(...)

pandas
- dtypes
- value_counts
```

### Contrato de UI (campos consumidos)

- `df` (obrigatório)
- `_dtype_summary(df)` retorna DataFrame com colunas:
  - `dtype`
  - `cols`
- Renderização via `_df_to_html_table(...)` com truncamento de strings.

### Observações técnicas

- Tipos são inferidos pelo pandas e podem divergir da semântica real.
- Serve como diagnóstico estrutural (não semântico).

---

## [S1.5] Card — Faltantes (top N)

**Referência no pipeline visual:**  
Seção 1️⃣ → Faltantes (top N)

### Finalidade
Detalhar as colunas com maior incidência de valores ausentes, permitindo **priorização objetiva** de tratamento.

### Origem dos dados

A tabela é produzida no renderer a partir de `_missing_summary(df, top_n=max_missing_rows)`.

### Funções envolvidas

```text
Render (UI)
src/reporting/ui.py
- _missing_summary(...)
- _missing_badge(...)
- render_dataset_overview(...)
- _df_to_html_table(...)

pandas
- isna
- sum
- sort_values
- head
```

### Regras de obtenção / cálculo

1) Resumo base:

- `missing = df.isna().sum()`
- `pct_missing = (missing / len(df) * 100).round(2)`
- Ordena por `missing` e `pct_missing` descrescente
- Retorna `head(top_n)`

2) Enriquecimento para UI (coluna adicional):

- A UI adiciona `severity` por linha:
  - `severity = _missing_badge(pct_missing)[0]`

3) Limite de exibição (top N):

- `top_n` é `max_missing_rows`
- No notebook, esse valor costuma vir do orquestrador:
  - `src/data/load_data.py::load_and_report_raw_data(..., max_missing_rows=12)`

### Contrato de UI (colunas consumidas)

A tabela exibida utiliza (na ordem atual do UI):

- `column`
- `dtype`
- `missing`
- `pct_missing`
- `severity` *(adicionada pela UI)*

### Observações técnicas

- Complementa o indicador global.
- A tabela é diagnóstica; nenhuma correção/imputação é feita aqui.

---

# Seção 2 — Qualidade Estrutural & Tipagem


### Correspondência com o Pipeline Visual

Esta seção corresponde diretamente à **Seção 2 — Qualidade Estrutural & Tipagem** apresentada no arquivo `pipeline_notebook.md`.

- **Âncora visual canônica:** `./images/card_s2_qualidade_estrutural_tipagem.png`
- **Indexação visual:** Cards numerados de **1️⃣ a 4️⃣** (além do `S2.pre`)
- **Função da âncora:** servir como **mapa visual** de referência para interpretação dos elementos desta seção (`[S2.*]`).

> 📌 A âncora visual não é decorativa: ela define o **espaço semântico e visual** no qual os elementos técnicos desta seção devem ser interpretados.

Esta seção documenta os elementos responsáveis por **avaliar e consolidar a qualidade estrutural do dataset após a ingestão**, com foco em impactos técnicos decorrentes de conversões de tipo, verificações de integridade básica e efeitos colaterais como introdução de valores nulos.

Diferentemente da Seção 1, que possui caráter **puramente diagnóstico**, os elementos aqui definidos **podem modificar o DataFrame**, porém **sem alterar sua semântica de negócio**.

Os resultados desta seção atuam como uma **ponte técnica** entre a ingestão bruta e as etapas posteriores de padronização, imputação e engenharia de atributos.

---

## [S2.pre] Fase de Execução Técnica — Validações Estruturais

**Referência no pipeline visual:**  
Seção 2️⃣ → Execução Técnica (pré-renderização dos cards)

### Finalidade

Tornar explícita a **fase de execução técnica obrigatória** da Seção 2, responsável por aplicar
validações estruturais e de tipagem ao dataset **antes da renderização de qualquer card visual**.

Esta fase garante que o estado do DataFrame esteja **tecnicamente validado** antes da
avaliação de impactos, auditorias e indicadores exibidos nos elementos subsequentes.

### Origem dos dados

- DataFrame ativo ao final da **Seção 1 — Ingestão e Diagnóstico Inicial**
- Execução direta de funções do core, sem dependência de UI

### Funções envolvidas

```text
src/data/quality_typing.py
- apply_type_conversions(...)
- check_duplicates(...)
- summarize_introduced_nans(...)
```

### Ordem lógica de execução

1. `apply_type_conversions(...)`
2. `check_duplicates(...)`
3. `summarize_introduced_nans(...)`

### Observações técnicas

- Esta fase é executada **sempre**, mesmo quando o impacto final é zero.
- Os cards [S2.1–S2.4] **não executam validações**: eles **medem e exibem** efeitos.
- “Impacto 0” deve ser interpretado como **estabilidade estrutural validada**.

---

<a id="s20-contrato-ui-secao-2"></a>
## [S2.0] Contrato de UI da Seção 2 (artefatos esperados)

**Referência no pipeline visual:**  
Seção 2️⃣ → Contrato de UI

### Finalidade

Declarar o **schema mínimo** esperado pelo renderer da Seção 2, garantindo rastreabilidade e manutenção segura.

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- build_before_after_table(...)
- apply_type_conversions(...)
- check_duplicates(...)
- summarize_introduced_nans(...)

Render (UI)
src/reporting/ui.py
- render_quality_typing_overview(...)
```

### Contrato de UI (campos consumidos)

O renderer `render_quality_typing_overview(...)` consome:

- `impact_df: pandas.DataFrame` (S2.1)
- `conversions_df: pandas.DataFrame` (S2.2)
- `dup_info: dict` (S2.3) com:
  - `has_duplicates: bool`
  - `duplicate_count: int`
- `introduced_nans_df: pandas.DataFrame` (S2.4)

> Observação: quando DataFrames chegam vazios, o UI exibe placeholders (“Nenhuma conversão…”, “Sem nulos introduzidos…”).

---

## [S2.1] Card — Impacto estrutural (Antes × Depois)

**Referência no pipeline visual:**  
Seção 2️⃣ → Impacto Estrutural

### Finalidade

Evidenciar de forma explícita o **impacto estrutural causado pelas operações desta seção**, comparando o estado do dataset antes e depois das conversões e verificações aplicadas.

### Origem dos dados

Tabela comparativa produzida pelo core (antes × depois), entregue ao UI como `impact_df`.

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- build_before_after_table(...)

Render (UI)
src/reporting/ui.py
- render_quality_typing_overview(...)
- _df_to_html_table(...)
```

### Regras de obtenção / cálculo

- Métricas esperadas no comparativo:
  - linhas
  - colunas
  - memória (MB)
  - delta (Δ) por métrica

> Nota: o formato exato das colunas é definido pelo core; o UI apenas renderiza a tabela.

### Contrato de UI (colunas consumidas)

- `impact_df` deve ser tabular e legível (colunas e linhas já prontas para exibição).
- O UI renderiza `impact_df` com `max_rows=6`.

### Observações técnicas

- Não há inferência semântica.
- Serve como trilha de auditoria técnica.
- Diagnostica e audita NaNs introduzidos por conversões de tipo.
- Esta etapa mede e audita o delta estrutural em relação à fase [S2.pre].


---

## [S2.2] Card — Conversões de tipos aplicadas

**Referência no pipeline visual:**  
Seção 2️⃣ → Conversões de Tipos

### Finalidade

Documentar de forma explícita **quais colunas sofreram conversão de tipo**, evidenciando alterações efetivamente aplicadas ao DataFrame.

### Origem dos dados

Relatório de conversões produzido pelo core e entregue ao UI como `conversions_df`.

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- apply_type_conversions(...)

Render (UI)
src/reporting/ui.py
- render_quality_typing_overview(...)
- _df_to_html_table(...)
```

### Regras de obtenção / cálculo

- O relatório deve conter apenas colunas impactadas (mudança de dtype e/ou nulos introduzidos).
- Quando `conversions_df` está vazio, o UI exibe:
  - `"Nenhuma conversão de tipo aplicada."`

### Contrato de UI (colunas consumidas)

- `conversions_df` é renderizado com `max_rows=8`.
- O UI não calcula conversões: ele apenas exibe o DataFrame pronto.

### Observações técnicas

- Conversões devem ser explícitas (core).
- Mantém rastreabilidade de mudanças estruturais.

---

## [S2.3] Card — Integridade estrutural

**Referência no pipeline visual:**  
Seção 2️⃣ → Integridade Estrutural

### Finalidade

Verificar a **integridade estrutural básica do dataset**, com foco na detecção de registros duplicados.

### Origem dos dados

Resultado de checagem produzido pelo core como `dup_info: dict`.

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- check_duplicates(...)

Render (UI)
src/reporting/ui.py
- render_quality_typing_overview(...)
```

### Regras de obtenção / cálculo

O UI espera um dicionário com:

- `has_duplicates: bool`
- `duplicate_count: int`

Renderização:

- Se `has_duplicates == True`: UI exibe alerta com contagem
- Se `False`: UI exibe confirmação de ausência

### Observações técnicas

- Indicador não corrige duplicidades.
- Decisões de deduplicação são postergadas.

---

## [S2.4] Card — Nulos introduzidos por conversão

**Referência no pipeline visual:**  
Seção 2️⃣ → Nulos Introduzidos

### Finalidade

Evidenciar valores ausentes **introduzidos como efeito colateral direto das conversões de tipo**, distinguindo-os de nulos originalmente presentes no dataset.

### Origem dos dados

Resumo produzido pelo core e entregue ao UI como `introduced_nans_df`.

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- summarize_introduced_nans(...)

Render (UI)
src/reporting/ui.py
- render_quality_typing_overview(...)
- _df_to_html_table(...)
```

### Regras de obtenção / cálculo

- Identifica colunas onde o estado pós-conversão introduziu `NaN`.
- Quando `introduced_nans_df` está vazio, o UI exibe:
  - `"Sem nulos introduzidos por conversão."`

### Contrato de UI (colunas consumidas)

- `introduced_nans_df` é renderizado com `max_rows=8`.

### Observações técnicas

- Indica entradas não parseáveis (strings vazias, formatos inválidos etc.).
- Nenhuma imputação ocorre nesta seção.

---

## 🧭 Observação geral da Seção 2 — Qualidade Estrutural & Tipagem

- Nenhuma transformação semântica de negócio é aplicada.
- Todas as alterações são **técnicas, rastreáveis e reversíveis**.
- Os elementos aqui definidos preparam o terreno para:
  - Padronização categórica
  - Imputações conscientes
  - Engenharia de atributos segura

---

# Seção 3 — Conformidade ao Contrato de Entrada (API), Diagnóstico de Features & Padronização Categórica (Diagnóstico)


### Correspondência com o Pipeline Visual

Esta seção corresponde diretamente à **Seção 3 — Conformidade ao Contrato & Preparação Semântica** apresentada no arquivo `pipeline_notebook.md`.

- **Âncora visual canônica:** `./images/card_s3_conformidade_contrato_api_01.png`
- **Indexação visual:** Cards numerados de **1️⃣ a 7️⃣** (além do `S3.pre`)
- **Função da âncora:** servir como **mapa visual** de referência para interpretação dos elementos desta seção (`[S3.*]`).

> 📌 A âncora visual não é decorativa: ela define o **espaço semântico e visual** no qual os elementos técnicos desta seção devem ser interpretados.

Esta seção documenta os elementos responsáveis por **estabelecer o escopo semântico do pipeline**, conectando o dataset **tecnicamente validado** nas etapas anteriores ao **contrato formal de entrada da API**, além de realizar um **diagnóstico categórico inicial**.

Nenhuma transformação semântica ou codificação é aplicada nesta etapa.  
Todos os elementos possuem caráter **diagnóstico, explicativo e auditável**.

---

## [S3.pre] Fase de Execução Técnica — Contrato, Escopo e Diagnóstico de Features

**Referência no pipeline visual:**  
Seção 3️⃣ → Execução Técnica (pré-renderização dos cards)

### Finalidade

Tornar explícita a **fase de execução técnica obrigatória** da Seção 3, responsável por:

- carregar e interpretar o contrato da API,
- aplicar o recorte semântico (kept/dropped),
- capturar snapshots estruturais (antes/depois),
- construir o escopo (`features` e `target`),
- executar o diagnóstico categórico e gerar candidatos,

**antes** da renderização de qualquer card visual.

### Origem dos dados

- DataFrame ativo ao final da Seção 2 (já validado estruturalmente)
- Contrato externo (`api_contract.md` / YAML equivalente), carregado pelo core

### Funções envolvidas

```text
src/data/contract_loader.py
- load_contract_yaml(...)
- ContractConfig.to_scope(...)

src/features/contract_and_candidates.py
- run_contract_and_candidates(...)
- enforce_contract_columns(...)
- find_categorical_candidates(...)
- _safe_capture_snapshot(...)
```

### Ordem lógica de execução (visão operacional)

1. Carrega contrato → `load_contract_yaml(...)`
2. Constrói escopo → `ContractConfig.to_scope(...)`
3. Aplica recorte conforme contrato → `enforce_contract_columns(...)`
4. Captura snapshots antes/depois → `_safe_capture_snapshot(...)`
5. Executa diagnóstico categórico → `find_categorical_candidates(...)`
6. Consolida payload final → `run_contract_and_candidates(...)`

### Observações técnicas

- Esta fase é executada antes dos cards **[S3.1–S3.7]**; os cards **não executam** contrato nem diagnóstico.
- `target` pode existir no DataFrame supervisionado, mas é **fora do contrato** do `/predict`.
- Snapshots podem ser opcionais: quando ausentes, a UI usa fallback via `df.shape` e `df.memory_usage(...)`.
- Se `contract` estiver ausente no payload, a UI **não prova conformidade** — ela apenas exibe `df.columns` como fallback.

---

<a id="s30-contrato-ui-secao-3"></a>
## [S3.0] Contrato de UI da Seção 3 (payload esperado)

**Referência no pipeline visual:**  
Seção 3️⃣ → Painel Consolidado

### Finalidade

Declarar explicitamente o **payload** consumido pelo renderer da Seção 3 (`render_contract_and_candidates_report`), garantindo compatibilidade e manutenção segura.

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- run_contract_and_candidates(...)
- enforce_contract_columns(...)
- find_categorical_candidates(...)
- _safe_capture_snapshot(...)

Contrato/entrada
src/data/contract_loader.py
- load_contract_yaml(...)
- ContractConfig.to_scope(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(payload)
```

### Contrato de UI (campos consumidos)

O renderer consome um `payload: dict` com:

- `payload["df"] : pandas.DataFrame` (**obrigatório**)  
  DataFrame no estado pós-contrato (ou estado atual do pipeline).

- `payload["contract"] : object | None` (opcional)  
  A UI tenta ler, quando presentes:
  - `kept_columns : list[str]`
  - `dropped_columns : list[str]`
  - `missing_contract_columns : list[str]` *(lido, mas não exibido atualmente)*
  - `snapshot_before : object | None`
  - `snapshot_after : object | None`

- `payload["candidates"] : object | None` (opcional)  
  A UI tenta ler:
  - `overview : dict`
  - `top_candidates : pandas.DataFrame`
  - `binary_candidates : pandas.DataFrame`
  - `service_phrase_candidates : pandas.DataFrame`

- `payload["scope"] : object | None` (opcional)  
  Estrutura semântica (ex.: `NormalizationScope`) contendo:
  - `features : list[str]`
  - `target : str | None`

> Observação: o renderer é tolerante a payload parcial (aplica fallbacks).

---

## [S3.1] Card — Conformidade ao Contrato de Entrada (API)

**Referência no pipeline visual:**  
Seção 3️⃣ → Conformidade ao Contrato de Entrada (API)

### Finalidade

Garantir que o pipeline opere **exclusivamente sobre o conjunto de colunas esperado pela API de inferência**, eliminando ambiguidades entre treino/validação/produção.

### Origem dos dados

- Contrato carregado (ex.: YAML) convertido em escopo semântico
- Resultado de conformidade (ex.: `ContractConformanceResult`)
- Fallback de UI: `df.columns` quando `contract` não está disponível no payload

### Funções envolvidas

```text
Origem (core)
src/data/contract_loader.py
- load_contract_yaml(...)
- ContractConfig.to_scope(...)

src/features/contract_and_candidates.py
- run_contract_and_candidates(...)
- enforce_contract_columns(...)
- _scope_from_contract_columns(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Regras de obtenção / cálculo

- Core define o conjunto de colunas mantidas como:
  - `features` do contrato
  - + `target` (mantido no DataFrame do pipeline supervisionado, embora não pertença ao contrato do /predict)

- UI utiliza:
  - `kept = contract.kept_columns OR list(df.columns)` *(fallback rastreável)*

### Contrato de UI (campos consumidos)

- `payload["contract"].kept_columns` (preferencial)
- Fallback: `payload["df"].columns`

### Observações técnicas

- Se o `contract` não estiver no payload, a UI **não consegue provar** conformidade real: ela apenas exibe as colunas atuais do DataFrame como “mantidas”.
- `missing_contract_columns` é lido pelo renderer, mas **não é exibido** na UI atual.

---

## [S3.2] Card — Impacto Estrutural (Antes × Depois)

**Referência no pipeline visual:**  
Seção 3️⃣ → Impacto Estrutural (antes × depois)

### Finalidade

Evidenciar o **impacto estrutural causado pela aplicação do contrato**, permitindo auditoria explícita de alterações técnicas no dataset.

### Origem dos dados

- Snapshots estruturais antes/depois capturados pelo core
- Fallback do UI: métricas calculadas a partir de `df` quando snapshots não estiverem disponíveis

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- run_contract_and_candidates(...)
- _safe_capture_snapshot(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Regras de obtenção / cálculos (compatibilidade e fallback)

A UI suporta dois “formatos” de snapshot:

1) Formato antigo:
- `rows`, `cols`

2) Formato oficial (StructuralSnapshot):
- `n_rows`, `n_cols`, `memory_bytes`
- propriedade opcional: `memory_mb`

Fallback (sempre disponível) para o “Depois”:

- `after_rows = df.shape[0]`
- `after_cols = df.shape[1]`
- `after_mem_mb = df.memory_usage(deep=True).sum() / 1024²`

Regras do delta (Δ):

- `Δ = after - before` somente quando o “Antes” existe; caso contrário, Δ é exibido como indisponível.

### Contrato de UI (campos consumidos)

- `payload["contract"].snapshot_before` (opcional)
- `payload["contract"].snapshot_after` (opcional)
- `payload["df"]` (fallback)

### Observações técnicas

- Quando `snapshot_before` não é fornecido, a UI exibe “(indisponível)” para “Antes”.
- O painel mede custo técnico do recorte (não semântica).

---

## [S3.3] Card — Auditoria de Colunas

**Referência no pipeline visual:**  
Seção 3️⃣ → Auditoria de Colunas

### Finalidade

Documentar explicitamente o **papel semântico de cada grupo de colunas** no pipeline, evitando decisões implícitas.

### Origem dos dados

- Metadados do contrato e escopo semântico
- Lista de colunas descartadas pelo core
- O bloco de “features” é informativo via `scope.features` (quando presente)

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- enforce_contract_columns(...)
- run_contract_and_candidates(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Regras de obtenção / cálculo (o que a UI exibe)

A UI exibe:

1) **Target** (se disponível em `scope.target`)
- “fora do contrato de entrada da API”
- sinaliza que **não participa** do diagnóstico categórico desta etapa

2) **Features do contrato (contagem)** (se `scope.features` existir e for lista)
- UI exibe o número (não lista as features nesse card)

3) **Colunas descartadas** (`contract.dropped_columns`)
- se vazio: “Nenhuma descartada.”

> Importante: o card “Auditoria” **não lista** as features do contrato; ele foca em target + descartadas.

### Contrato de UI (campos consumidos)

- `payload["scope"].target` (opcional)
- `payload["scope"].features` (opcional; apenas contagem)
- `payload["contract"].dropped_columns` (opcional)

### Observações técnicas

- Nenhum descarte ocorre implicitamente: descartadas devem vir do core.
- O target é tratado como fora do contrato do /predict, mas pode permanecer no dataset do pipeline supervisionado.

---

## [S3.4] Indicador — Descoberta de Candidatos

**Referência no pipeline visual:**  
Seção 3️⃣ → Descoberta de Candidatos

### Finalidade

Oferecer uma **visão quantitativa da complexidade categórica** do dataset, antes da aplicação de qualquer padronização.

### Origem dos dados

- `candidates.overview` produzido pelo core
- UI aplica blindagens para evitar inconsistências de contagem

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- find_categorical_candidates(...)
- run_contract_and_candidates(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Regras de obtenção / cálculos

A UI utiliza as seguintes chaves do `overview`:

- `suspected_columns`
- `binary_candidates`
- `service_phrase_columns`
- `excluded_columns`
- `total_columns`

Blindagem importante (auditoria):

- `total_columns` deve representar **quantidade de colunas analisadas** (não linhas).
- Se `total_columns` vier inválido, a UI corrige:
  - se `<= 0` ou `> df.shape[1]` → assume `df.shape[1]`

Exclusões exibidas:

- `excluded_columns` é mostrado como “Excluídas do diagnóstico” em chips.

### Contrato de UI (campos consumidos)

- `payload["candidates"].overview : dict` (opcional)
- `payload["df"]` (para blindagem e fallback)

### Observações técnicas

- “Total analisadas” é **colunas**, não registros.
- Diagnóstico é heurístico; não aplica transformações.

---

## [S3.5] Card — Top Candidatos

**Referência no pipeline visual:**  
Seção 3️⃣ → Top candidatos

### Finalidade

Permitir **inspeção detalhada** das colunas mais propensas à padronização categórica, com base em critérios objetivos.

### Origem dos dados

DataFrame `top_candidates` produzido pelo core e entregue ao UI.

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- find_categorical_candidates(...)
- _pct_unique(...)
- _sample_values(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Contrato de UI (schema esperado)

A UI não impõe schema rígido (renderiza HTML direto), mas para rastreabilidade recomenda-se que `top_candidates` traga colunas auditáveis como:

- `column` (nome da coluna)
- `dtype` (dtype atual)
- `n_unique` (cardinalidade absoluta)
- `pct_unique` (proporção de únicos)
- `sample_values` (amostra curta)
- `reason` / `signals` (motivos heurísticos)

> Nota: o core é a fonte de verdade; o UI apenas exibe.

### Observações técnicas

- Nenhuma coluna é automaticamente selecionada pelo UI.
- Serve de base para decisões explícitas na etapa de padronização.

---

## [S3.6] Card — Provavelmente Binárias (Yes/No ou 0/1)

**Referência no pipeline visual:**  
Seção 3️⃣ → Provavelmente binárias

### Finalidade

Identificar colunas cujo conjunto de valores sugere **binariedade semântica**, demandando estratégias específicas de encoding.

### Origem dos dados

DataFrame `binary_candidates` produzido pelo core e entregue ao UI.

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- find_categorical_candidates(...)
- _is_binary_like(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Contrato de UI (schema esperado)

Recomenda-se que o DataFrame inclua:

- `column`
- `dtype`
- `n_unique`
- `sample_values`
- `binary_pattern` (ex.: yes/no, 0/1, true/false)
- `reason`

### Observações técnicas

- Classificação é probabilística.
- Nenhuma conversão é aplicada nesta seção.

---

## [S3.7] Card — Frases de Serviço Detectadas

**Referência no pipeline visual:**  
Seção 3️⃣ → Frases de serviço detectadas

### Finalidade

Detectar colunas que contêm **padrões textuais de “frases de serviço”** associados a estado negativo (ex.: ausência de serviço), comuns em datasets como churn.

### Origem dos dados

DataFrame `service_phrase_candidates` produzido pelo core a partir de heurísticas textuais.

### Funções envolvidas

```text
Origem (core)
src/features/contract_and_candidates.py
- find_categorical_candidates(...)
- _has_service_phrase(...)

Render (UI)
src/reporting/ui.py
- render_contract_and_candidates_report(...)
```

### Regras de obtenção / cálculo (estado atual)

O UI referencia explicitamente exemplos do tipo:

- `"No internet service" → "No"`

> Importante: o documento deve refletir o comportamento real do core.  
> Se o core estiver limitado a padrões específicos, não declarar “variações semânticas” sem suporte.

### Contrato de UI (schema esperado)

Recomenda-se que o DataFrame inclua:

- `column`
- `sample_values`
- `detected_phrase` / `match`
- `reason`

### Observações técnicas

- Nenhum colapso semântico é aplicado nesta etapa.
- É apenas sinalização diagnóstica para padronização posterior.

---

## 🧭 Observação geral da Seção 3

- Nenhuma transformação semântica é aplicada.
- Nenhum encoding é executado.
- Todos os elementos possuem caráter **diagnóstico, auditável e reversível**.
- A seção estabelece o **contrato semântico e o universo de features** do pipeline, criando base técnica para a **padronização categórica consciente**, executada na etapa seguinte.

---

A seguir está a Seção 3.2 completa (execução da padronização), no mesmo padrão técnico do seu pipeline_elements.md, pronta para você copiar e colar logo após a “🧭 Observação geral da Seção 3” (ou, se preferir, como continuação natural da Seção 3).

---

# Seção 3.2 — Padronização Categórica (Execução)


### Correspondência com o Pipeline Visual

Esta seção corresponde diretamente à **Seção 3.2 — Padronização Categórica (Execução)** apresentada no arquivo `pipeline_notebook.md`.

- **Âncora visual canônica:** `./images/card_s3_padronizacao_categorica_execucao.png`
- **Indexação visual:** Cards numerados de **S3.9 a S3.13** (além do `S3.2.pre`)
- **Função da âncora:** servir como **mapa visual** de referência para interpretação dos elementos desta seção (`[S3.2.*]`).

> 📌 A âncora visual não é decorativa: ela define o **espaço semântico e visual** no qual os elementos técnicos desta seção devem ser interpretados.

Esta seção documenta os elementos responsáveis por executar a **padronização categórica declarada**, derivada explicitamente do diagnóstico apresentado na Seção 3 (**S3.1–S3.7**).

Diferentemente da etapa diagnóstica, aqui ocorre **transformação efetiva** no DataFrame, porém restrita ao **escopo semântico** (features do contrato) e **sem encoding**.

---

<a id="s32pre-execucao-padronizacao-categorica"></a>
## [S3.2.pre] Fase de Execução Técnica — Padronização Categórica (Execução)

**Referência no pipeline visual:**  
Seção 3️⃣ → Execução (padronização categórica)

### Finalidade

Tornar explícita a fase de execução técnica responsável por:

- aplicar normalização textual mínima (`lower/strip/collapse whitespace`),
- aplicar substituições explícitas (ex.: `"no internet service" → "no"`),
- limitar alterações ao escopo do contrato (features),
- manter o target intocado,
- produzir um payload auditável para renderização dos cards (**S3.8+**).

### Origem dos dados

- DataFrame ativo pós-contrato (resultado da Seção 3 diagnóstica / `payload["df"]`)
- `scope` semântico (`features/target`) derivado do contrato
- decisão explícita do notebook (`phrase_map` + `cols_scope`)

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- run_categorical_standardization(...)
- apply_service_phrase_standardization(...)
- _normalize_text_value(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
```

### Ordem lógica de execução (visão operacional)

1) **Notebook declara decisão explícita**
- `phrase_map` (mapa de substituições)
- `cols_scope` (colunas que devem ser consideradas)

2) **Orquestração**
- `run_categorical_standardization(df, scope, phrase_map, cols_scope, ...)`

3) **Execução efetiva**
- `apply_service_phrase_standardization(...)` aplica regras apenas nas colunas válidas

4) **Auditoria e payload**
- captura snapshots antes/depois
- gera tabelas e metadados (impacto, regras, mudanças, resumo)

### Observações técnicas

- Esta fase é **irreversível** no sentido do pipeline (altera o estado do DataFrame).
- Nenhuma inferência semântica é aplicada: **só regras explícitas**.
- Não aplica encoding, não cria features novas, não remove colunas.
- O **target** não participa nem do escopo de alteração nem do relatório de execução.

---

<a id="s38-contrato-ui-secao-32"></a>
## [S3.8] Contrato de UI da Seção 3.2 (payload esperado)

**Referência no pipeline visual:**  
Seção 3️⃣ → Painel de Execução (padronização)

### Finalidade

Declarar explicitamente o payload consumido pelo renderer da execução (`render_categorical_standardization_report`), garantindo compatibilidade, rastreabilidade e tolerância a payload parcial.

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- run_categorical_standardization(...)
- apply_service_phrase_standardization(...)
- capture_structural_snapshot(...)
- build_before_after_table(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
```

### Contrato de UI (campos consumidos)

O renderer consome um `payload: dict` com:

- `payload["df"] : pandas.DataFrame` (**obrigatório**)  
  DataFrame já padronizado.

- `payload["impact_df"] : pandas.DataFrame` (opcional, recomendado)  
  Tabela “Antes × Depois” (linhas/colunas/memória e Δ).

- `payload["rules_df"] : pandas.DataFrame` (opcional, recomendado)  
  Regras efetivamente aplicadas (ex.: colunas from, to).

- `payload["changes_df"] : pandas.DataFrame` (opcional, recomendado)  
  Relatório auditável por coluna (ex.: `column`, `cells_changed`, `examples`, `rule_type`).

- `payload["meta"] : dict` (opcional)  
  Metadados consolidados (ex.: `scoped_cols_considered`, `total_cells_changed`, `rules_count`).

- `payload["decision"] : dict` (opcional, recomendado)  
  Decisão explícita utilizada na execução:
  - `phrase_map : dict[str, str]`
  - `cols_scope : list[str]`

- `payload["scope"] : object | None` (opcional)  
  Estrutura semântica (ex.: `NormalizationScope`), contendo:
  - `features : list[str]`
  - `target : str | None`

> Observação: o renderer é tolerante a DataFrames vazios e ausência de campos (exibe placeholders).

---

## [S3.9] Card — Decisão explícita (derivada do diagnóstico)

**Referência no pipeline visual:**  
Seção 3️⃣ → Decisão explícita (execução)

### Finalidade

Fixar, de forma rastreável, quais regras e quais colunas foram declaradas para execução, evitando padronização “silenciosa”.

Este card separa claramente:

- Colunas selecionadas pelo diagnóstico (entrada da decisão)
- Colunas efetivamente padronizadas (escopo final aplicado após filtros)

### Origem dos dados

- `payload["decision"]` (entrada declarada no notebook)
- `payload["meta"]["scoped_cols_considered"]` (escopo final aplicado)

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- run_categorical_standardization(...)
- apply_service_phrase_standardization(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
```

### Regras / interpretação

- `cols_scope` representa intenção (seleção derivada do diagnóstico).
- `scoped_cols_considered` representa execução real após filtros:
  - apenas colunas que existem em `df`
  - se `scope.features` existir, apenas colunas que pertencem às features

### Contrato de UI (campos consumidos)

- `payload["decision"]["cols_scope"]`
- `payload["meta"]["scoped_cols_considered"]`
- `payload["decision"]["phrase_map"]`

### Observações técnicas

- Evita confusão com target: este card não usa a palavra “alvo”.
- O escopo final pode ser menor que o diagnóstico (ex.: coluna ausente ou fora das features).

---

## [S3.10] Card — Resumo da execução

**Referência no pipeline visual:**  
Seção 3️⃣ → Resumo da execução

### Finalidade

Comunicar, de forma sintética, o que realmente aconteceu na execução:

- volume total de células alteradas,
- confirmação explícita de que encoding não foi aplicado,
- confirmação de que target não foi modificado.

### Origem dos dados

- `payload["meta"]["total_cells_changed"]`
- `payload["scope"].target` (quando presente)
- texto fixo controlado na camada de UI (sem inferência)

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- apply_service_phrase_standardization(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
```

### Contrato de UI (campos consumidos)

- `payload["meta"]["total_cells_changed"]`
- (opcional) `payload["scope"].target`

### Observações técnicas

- “0 células alteradas” é estado válido: indica que regras foram avaliadas, mas não houve match.
- A ausência de encoding é deliberada (próxima etapa do pipeline).

---

## [S3.11] Card — Impacto estrutural (Antes × Depois)

**Referência no pipeline visual:**  
Seção 3️⃣ → Impacto estrutural (execução)

### Finalidade

Evidenciar impacto estrutural da execução (principalmente memória), mantendo trilha auditável.

### Origem dos dados

- Snapshots capturados pelo core antes/depois da execução
- Tabela gerada por `build_before_after_table(before, after)`

### Funções envolvidas

```text
Origem (core)
src/data/quality_typing.py
- capture_structural_snapshot(...)
- build_before_after_table(...)

src/features/categorical_standardization.py
- apply_service_phrase_standardization(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
- _df_to_html_table(...)
```

### Contrato de UI (campos consumidos)

- `payload["impact_df"]` (tabular, pronto para renderização)

### Observações técnicas

- Normalização textual pode reduzir memória (ex.: remoção de espaços redundantes).
- Não deve alterar número de linhas/colunas (qualquer variação seria bug desta etapa).

---

## [S3.12] Card — Regras aplicadas

**Referência no pipeline visual:**  
Seção 3️⃣ → Regras aplicadas (execução)

### Finalidade

Registrar as regras declaradas e efetivamente utilizadas na execução, como trilha mínima de governança do pré-processamento.

### Origem dos dados

- `phrase_map` fornecido pelo notebook (decisão explícita)
- serialização estável em `rules_df` pelo core

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- StandardizationRule(...)
- apply_service_phrase_standardization(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
- _df_to_html_table(...)
```

### Contrato de UI (colunas consumidas)

Recomenda-se que `rules_df` contenha:

- `from`
- `to`

A UI renderiza tabela com fallback:

- se vazio: “Nenhuma regra aplicada.”

### Observações técnicas

- Regras são normalizadas para `lower/strip` no core para evitar divergência.
- Regras não devem ser inferidas automaticamente.

---

## [S3.13] Card — Relatório de mudanças

**Referência no pipeline visual:**  
Seção 3️⃣ → Relatório de mudanças

### Finalidade

Exibir relatório auditável por coluna, indicando:

- quais colunas mudaram,
- quantas células foram alteradas,
- exemplos de substituições observadas.

### Origem dos dados

- Máscara de mudança calculada por coluna (normalizado vs substituído)
- Tabela consolidada `changes_df` produzida no core

### Funções envolvidas

```text
Origem (core)
src/features/categorical_standardization.py
- apply_service_phrase_standardization(...)

Render (UI)
src/reporting/ui.py
- render_categorical_standardization_report(payload)
- _df_to_html_table(...)
```

### Contrato de UI (schema recomendado)

Para rastreabilidade, `changes_df` deve incluir:

- `column`
- `rule_type`
- `cells_changed`
- `examples` (string curta)

### Observações técnicas

- `examples` é amostra limitada (não é prova exaustiva).
- Colunas com `cells_changed == 0` podem aparecer (dependendo da política do core); UI deve tolerar.
- Este relatório é o artefato que “fecha” a execução de forma verificável.

---

## 🧭 Observação geral da Seção 3.2

Esta etapa executa transformação irreversível no estado do DataFrame (no pipeline), porém controlada e rastreável.

A execução é sempre derivada de uma decisão explícita, nunca inferida automaticamente.

O escopo é restrito às features do contrato; target permanece intocado.

Nenhum encoding é aplicado: a saída desta seção é um dataset semanticamente coerente e pronto para etapas posteriores.

> **Transição para a Seção 4** — Após a padronização categórica, o dataset encontra-se semanticamente estável e aderente ao contrato, porém ainda pode conter valores ausentes introduzidos originalmente ou preservados por decisão técnica. A Seção 4 avança sobre esse ponto executando, de forma explícita e auditável, o tratamento de dados faltantes.

---

### Correspondência com o Pipeline Visual

Este elemento corresponde ao card exibido no `pipeline_notebook.md` na **Seção 3.3 — Auditoria do Target (diagnóstico supervisionado)**.

- **Âncora visual canônica:** `./images/card_s3_auditoria_target.png`
- **Indexação visual:** Card **S3.14**
- **Função da âncora:** servir como referência visual do encerramento supervisionado da Seção 3.

## [S3.14] Card — Auditoria do Target (diagnóstico supervisionado)
Este elemento representa a **auditoria diagnóstica da variável-alvo (target)**, encerrando a Seção 3 do pipeline.

Diferente das auditorias anteriores — voltadas às features — esta etapa atua sobre o **alvo supervisionado**, verificando se ele está **presente, consistente e semanticamente adequado** para a fase de modelagem.

Esta auditoria **não transforma dados** e **não aplica inferências silenciosas**. Seu papel é exclusivamente **diagnóstico**, funcionando como uma **barreira de segurança semântica** antes de qualquer etapa irreversível de execução.

---

### Objetivo técnico

Responder explicitamente às seguintes perguntas:

- A coluna target está presente no dataset atual?
- O target possui valores ausentes?
- O domínio observado é compatível com o domínio esperado?
- O target apresenta cardinalidade adequada (ex.: binário)?
- Existem variações problemáticas de casing, whitespace ou valores inesperados?

---

### Origem dos dados

- **DataFrame:** estado atual do pipeline após aplicação do contrato de entrada e diagnósticos categóricos
- **Escopo:** definição semântica contendo a chave `target`
- **Domínio esperado:** opcional, quando informado no pipeline (ex.: `["Yes", "No"]`)

---

### Elementos técnicos

Este card é alimentado pelo wrapper de core:

- `run_target_audit(...)`

Que encapsula a função diagnóstica:

- `audit_target(...)`

Produzindo um payload padronizado contendo:

- `audit`: dicionário com métricas e achados diagnósticos
- `audit_df`: tabela auditável de distribuição do target
- `meta`: resumo completo para UI (linhas, únicos, nulos, inválidos, domínio esperado e observado)

---

### Contrato de saída (payload → UI)

```json
{
  "df": "<DataFrame>",
  "scope": "<dict | object>",
  "target": "<str>",
  "audit": {
    "status": "ok | warning | error",
    "missing_count": "<int>",
    "missing_pct": "<float>",
    "nunique": "<int>",
    "unique_values_preview": "<list>",
    "value_counts": "<list>",
    "anomalies": "<list>"
  },
  "audit_df": "<DataFrame>",
  "meta": {
    "executed": true,
    "n_rows": "<int>",
    "n_unique": "<int>",
    "missing_count": "<int>",
    "invalid_count": "<int>",
    "expected_values": "<list | null>",
    "observed_values": "<list>"
  }
}
```

### Finalidade

Este elemento representa a **auditoria diagnóstica da variável-alvo (target)** do pipeline supervisionado.

Seu objetivo é **descrever o estado atual do target**, verificando se ele é **adequado para modelagem supervisionada**, antes de qualquer transformação irreversível (imputação, encoding ou balanceamento).

Esta etapa atua como uma **barreira de segurança semântica**, prevenindo erros comuns como:
- targets ausentes ou mal definidos
- targets com classe única
- domínios inesperados
- valores nulos silenciosos
- variações semânticas (ex.: casing, whitespace)

> ⚠️ Importante: esta auditoria **não transforma** o target.  
> Ela apenas descreve e sinaliza riscos.

---


### Funções envolvidas

**Core (diagnóstico):**
- `audit_target(df, target, ...)`
  - Realiza a auditoria não destrutiva da coluna target
  - Retorna distribuição, métricas e achados semânticos

**Core (orquestração):**
- `run_target_audit(df, scope, ...)`
  - Envolve o diagnóstico do core
  - Monta o payload padronizado para consumo pela UI
  - Calcula métricas-resumo esperadas pelo card

**UI (renderização):**
- `render_target_audit_report(payload)`
  - Renderiza o card HTML da auditoria do target no notebook
  - Exibe resumo técnico + tabela auditável

---

### Contrato de UI (payload consumido)

O renderer espera um payload tolerante com as seguintes chaves:

- `payload["target"] : str | None`
- `payload["audit_df"] : pandas.DataFrame`
  - Tabela de distribuição do target (`value`, `count`, `pct`)
- `payload["meta"] : dict`
  - `executed`
  - `status` (`ok` | `warning` | `error`)
  - `n_rows`
  - `n_unique`
  - `missing_count`
  - `invalid_count`
  - `expected_values`
  - `observed_values`

---

### Comportamento esperado

- ❌ Não normaliza valores
- ❌ Não converte tipos
- ❌ Não aplica encoding
- ❌ Não corrige inconsistências
- ✔️ Apenas diagnostica e sinaliza

O status final do card reflete:
- **ok** → target consistente para modelagem
- **warning** → inconsistências não críticas
- **error** → target inadequado para uso supervisionado

---

### Referência no pipeline visual

Este card aparece ao final da **Seção 3 — Conformidade ao Contrato & Diagnóstico Categórico**, marcando o encerramento do **estado supervisionado seguro** do dataset, imediatamente antes de qualquer etapa de execução ou modelagem.

---

<a id="secao-4-inicio"></a>
# Seção 4 — Tratamento de Dados Faltantes (Execução)


### Correspondência com o Pipeline Visual

Esta seção corresponde diretamente à **Seção 4 — Tratamento de Dados Faltantes (Execução)** apresentada no arquivo `pipeline_notebook.md`.

- **Âncora visual canônica:** `./images/card_s4_tratamento_dados_faltantes_execucao.png`
- **Indexação visual:** Cards numerados de **S4.1 a S4.5** (além do `S4.pre`)
- **Função da âncora:** servir como **mapa visual** de referência para interpretação dos elementos desta seção (`[S4.*]`).

> 📌 A âncora visual não é decorativa: ela define o **espaço semântico e visual** no qual os elementos técnicos desta seção devem ser interpretados.

Esta seção documenta a **execução efetiva da imputação de dados faltantes**, realizada de forma **explícita, controlada e auditável**, respeitando integralmente o escopo semântico definido nas seções anteriores do pipeline.

Diferentemente das etapas diagnósticas, esta fase **altera o estado do DataFrame** e, portanto, representa uma **transformação irreversível no contexto do pipeline**.

A execução segue rigorosamente a filosofia do projeto:

**diagnóstico → decisão explícita → execução → auditoria**

---

## [S4.pre] Fase de Execução Técnica — Imputação de Dados Faltantes

**Referência no pipeline visual:**  
Seção 4️⃣ → Execução (tratamento de dados faltantes)

### Finalidade

Tornar explícita a fase técnica responsável por:

- validar a decisão declarada no notebook,
- aplicar imputação apenas nas colunas permitidas pelo escopo (`scope.features`),
- garantir que o `target` não seja imputado automaticamente,
- executar a imputação de forma determinística,
- gerar artefatos completos de auditoria.

### Origem dos dados

- DataFrame ativo após a Seção 3 (já conforme contrato e padronizado)
- Estrutura semântica `scope` (features + target)
- Decisão explícita do notebook (`decision`)

### Funções envolvidas

```text
Origem (core)
src/features/missing_imputation.py
- run_missing_imputation(...)
- _validate_decision(...)
- _apply_imputation(...)
- _resolve_fill_value(...)
- _changes_row(...)

Render (UI)
src/reporting/ui.py
- render_missing_imputation_report(payload)
```

---

<a id="s40-contrato-ui-secao-4"></a>
## [S4.0] Contrato de UI da Seção 4 (payload esperado)

O renderer da Seção 4 consome um `payload: dict` com os seguintes campos:

- `payload["df"] : pandas.DataFrame` (**obrigatório**)  
  DataFrame já imputado (estado final da seção).

- `payload["decision"] : dict`  
  Decisão explícita utilizada na execução.

- `payload["impact_df"] : pandas.DataFrame`  
  Comparativo estrutural Antes × Depois (linhas, colunas, memória).

- `payload["changes_df"] : pandas.DataFrame`  
  Relatório auditável por coluna contendo:
  - `column`
  - `dtype`
  - `kind`
  - `strategy`
  - `fill_value_used`
  - `missing_before`
  - `missing_after`
  - `imputed`
  - `pct_imputed`

- `payload["meta"] : dict`  
  Metadados consolidados da execução:
  - `executed`
  - `total_imputed_cells`
  - `affected_columns`
  - `scoped_cols_considered`
  - `excluded_cols_effective`
  - `target_preserved`

- `payload["scope"] : NormalizationScope`  
  Estrutura semântica contendo:
  - `features`
  - `target`

---

## [S4.1] Card — Decisão explícita de imputação

### Finalidade

Fixar de forma rastreável **quais estratégias foram declaradas** para imputação, evitando qualquer aplicação silenciosa de defaults no core.

### Origem dos dados

- `payload["decision"]`

---

## [S4.2] Card — Resumo da execução

### Finalidade

Comunicar, de forma sintética e objetiva, **o que efetivamente aconteceu** na execução.

### Métricas exibidas

- Total de células imputadas
- Total de colunas afetadas
- Quantidade de features consideradas
- Confirmação de preservação do target

---

## [S4.3] Card — Impacto estrutural (Antes × Depois)

### Finalidade

Auditar o impacto técnico causado pela imputação, principalmente em termos de memória.

---

## [S4.4] Card — Estratégias aplicadas

### Finalidade

Exibir, de forma tabular, **quais estratégias foram utilizadas por tipo de coluna**, funcionando como resumo operacional da execução.

---

## [S4.5] Card — Relatório de imputação

### Finalidade

Encerrar a Seção 4 com um **relatório auditável por coluna**, permitindo verificar:

- quantidade de valores ausentes antes e depois,
- número de células imputadas,
- estratégia aplicada,
- valor efetivamente utilizado na imputação.

---

## Observações gerais da Seção 4

- Esta etapa executa transformação irreversível no pipeline.
- Nenhuma inferência automática é aplicada.
- O escopo é estritamente limitado às features do contrato.
- O target é explicitamente preservado.
- A saída desta seção está pronta para etapas posteriores (encoding, scaling e modelagem).

---

## 🔹 Seção 5 — Preparação para Modelagem

Esta seção marca a transição entre o **pré-processamento semântico concluído** e a futura etapa de modelagem supervisionada.

Seu objetivo **não é treinar modelos**, nem definir representações finais do target, mas sim:

- preparar estruturalmente o dataset para treino futuro;
- separar explicitamente features (`X`) e target (`y`);
- aplicar um split reprodutível e auditável;
- diagnosticar os impactos estruturais e distributivos dessa separação.

⚠️ Nenhuma transformação irreversível é permitida nesta seção.

Todo o processamento aqui respeita rigorosamente o padrão:

**diagnóstico → decisão explícita → execução → auditoria**

---

<a id="secao-5-inicio"></a>

# Seção 5 — Preparação para Modelagem

Esta seção marca a transição entre o **pré-processamento semântico concluído** e a futura etapa de modelagem supervisionada.

Seu objetivo **não é treinar modelos**, nem definir representações finais do target, mas sim:

- preparar estruturalmente o dataset para treino futuro;
- separar explicitamente features (`X`) e target (`y`);
- aplicar um split reprodutível e auditável;
- diagnosticar os impactos estruturais e distributivos dessa separação.

⚠️ Nenhuma transformação irreversível é permitida nesta seção.

Todo o processamento aqui respeita rigorosamente o padrão:

**diagnóstico → decisão explícita → execução → auditoria**

---

<a id="s50-contrato-ui-preparacao-modelagem"></a>

## [S5.0] Contrato de UI — Preparação para Modelagem

Define o contrato de dados esperado para execução e auditoria da Seção 5.

### Entradas obrigatórias

- **`payload["df"]`**  
  Dataset completo ao final da Seção 4, já validado, tipado e com imputações irreversíveis concluídas **apenas nas features**.

- **`payload["scope"]`**  
  Escopo semântico do dataset, contendo explicitamente:
  - `features`: lista de colunas de entrada (`X`)
  - `target`: coluna alvo (`y`)

- **`payload["decision"]`**  
  Decisão explícita sobre o split treino/teste, contendo:
  - `test_size`
  - `random_state`
  - `shuffle`
  - `stratify` (boolean)
  - `stratify_col` (obrigatório apenas se `stratify = true`)

### Saídas obrigatórias

- **`payload["split"]`**
  Artefatos estruturais do split:
  - `X_train`, `X_test`
  - `y_train`, `y_test`

- **`payload["diagnostics"]`**
  Consolidação dos diagnósticos auditáveis da seção:
  - `shapes`
  - `target_distribution`
  - `risk_checks`
  - `categorical_cardinality` (opcional)

---

<a id="s51pre-execucao-tecnica-separacao-split"></a>

## [S5.1.pre] Execução Técnica — Separação e Split

Fase técnica **não visual**, responsável exclusivamente por executar o split após a decisão explícita ter sido declarada.

### Responsabilidades

- Separar o dataset em:
  - `X` = colunas definidas em `scope.features`
  - `y` = coluna definida em `scope.target`
- Aplicar `train_test_split` **exatamente conforme a decisão declarada**
- Garantir:
  - ausência do target em `X`
  - preservação dos valores originais (nenhuma transformação)
  - reprodutibilidade do split

### Restrições semânticas

- Nenhuma inferência automática é permitida
- Nenhuma transformação de valores é realizada
- Nenhuma decisão pode ser tomada nesta fase

---

<a id="s51-card-decisao-explicita-split"></a>

## [S5.1] Card — Decisão Explícita do Split

Elemento visual que documenta, de forma auditável, a decisão tomada para separação treino/teste.

### Conteúdo mínimo

- `test_size`
- `random_state`
- `shuffle`
- `stratify`
- `stratify_col` (se aplicável)
- Dimensão do dataset (derivada do DataFrame de entrada)

Este card representa **a decisão consciente** que governa toda a execução da Seção 5.

---

<a id="s52-card-shapes-treino-teste"></a>

## [S5.2] Card — Shapes de Treino e Teste

Diagnóstico estrutural do resultado do split.

### Conteúdo

- Shape de `X_train`
- Shape de `X_test`
- Shape de `y_train`
- Shape de `y_test`
- Número total de features (`len(scope.features)`)

⚠️ Nenhuma interpretação é realizada neste card.

---

<a id="s53-card-distribuicao-target-pre-pos-split"></a>

## [S5.3] Card — Distribuição do Target (Pré vs Pós-Split)

Auditoria comparativa da distribuição do target:

- Dataset completo
- Conjunto de treino
- Conjunto de teste

### Conteúdo

- Contagem absoluta por classe
- Proporção relativa (%)
- Diferença absoluta e percentual entre:
  - geral vs treino
  - geral vs teste

Este card permite identificar **impactos distributivos do split**, sem induzir decisões automáticas.

---

<a id="s54-card-diagnostico-riscos-estruturais"></a>

## [S5.4] Card — Diagnóstico de Riscos Estruturais

Diagnóstico objetivo de sinais de risco detectáveis após o split.

### Verificações mínimas

- **Integridade do escopo**
  - Target não presente em `X_train` / `X_test`
  - Colunas de `X` exatamente iguais a `scope.features`

- **Distribuição mínima do target**
  - Proporção da menor classe (geral / treino / teste)

- **Integridade do split**
  - Ausência de vazamento estrutural direto (target presente em `X`)

⚠️ Este card **não toma decisões**, apenas expõe sinais.

---

<a id="s55-card-cardinalidade-categorica-pos-split"></a>

## [S5.5] Card — Cardinalidade Categórica Pós-Split (Opcional)

Auditoria da cardinalidade das features categóricas após o split.

### Conteúdo (quando aplicável)

- Número de categorias únicas por feature:
  - treino
  - teste
- Identificação de categorias presentes no teste e ausentes no treino

Este diagnóstico antecipa **riscos potenciais para etapas futuras**, sem executar encoding ou transformação.

---

## Encerramento Semântico da Seção 5

Ao final desta seção, o pipeline deve ser capaz de responder com clareza:

- O dataset está estruturalmente pronto para treino?
- Como o split impactou a distribuição do target?
- Existem sinais objetivos de risco?
- Quais decisões ainda permanecem em aberto?

⚠️ Sem essas respostas, a Seção 6 **não pode ser iniciada**.

Nenhuma decisão de modelagem é tomada nesta etapa.

---

# 6️⃣ Seção 6 — Representação para Modelagem Supervisionada

Esta seção materializa, de forma **explícita e auditável**, como os dados serão representados para aprendizado supervisionado,
atuando como ponte formal entre:

- **Seção 5** (dados estruturais prontos + split executado) e
- **Seção 7** (estratégia de avaliação, métricas e baselines).

⚠️ **Escopo rígido:** esta seção **não treina modelos**, **não compara algoritmos**, **não define métricas finais** e **não realiza tuning**.
Ela apenas define e executa a **representação** de `X` e `y` após decisão explícita.

---

## [S6.0] Contrato da Seção (inputs, outputs e garantias)

### Inputs (pré-requisitos invariáveis)
Origem: **payload final da Seção 5**.

- `split.X_train` (DataFrame)
- `split.X_test` (DataFrame)
- `split.y_train` (Series)
- `split.y_test` (Series)
- `scope` (NormalizationScope) com:
  - `scope.features` (lista ordenada de features)
  - `scope.target` (coluna target)

> 📌 A Seção 6 assume que o split já foi executado e auditado na Seção 5.

### Decisão explícita (entrada declarada no notebook)
A execução desta seção depende de uma decisão declarada no notebook, sem inferência automática.

Campos mínimos esperados:

- `decision.X.categorical.strategy` (ex.: `onehot`)
- `decision.X.categorical.handle_unknown` (ex.: `ignore`)
- `decision.X.numeric.strategy` (ex.: `passthrough` ou `standard_scaler`)
- `decision.y.strategy` (ex.: `map_binary`)
- `decision.y.mapping` (ex.: `{"No": 0, "Yes": 1}` **ou** `{0: 0, 1: 1}`, conforme domínio observado)
- `decision.y.dtype` (ex.: `int64`)

> ✅ Regra de segurança: `decision.y.mapping` deve cobrir **100% dos valores observados** em `y_train` e `y_test`.  
> Se algum valor observado não estiver no mapping, a execução deve ser interrompida por segurança.

### Outputs (artefatos produzidos)
A seção deve produzir um payload consolidado contendo:

- `representation.X_train` / `representation.X_test`
- `representation.y_train` / `representation.y_test`
- `representation.feature_names`
- `representation.transformer`
- `representation.target_mapping` (quando aplicável)
- `diagnostics` (auditorias pós-representação)

### Garantias semânticas (invariantes)
- **Anti-leakage:** qualquer ajuste (`fit`) de transformadores ocorre **somente no treino**.
- **Consistência:** `X_train` e `X_test` devem resultar em **mesma dimensionalidade** e **mesma base de features**.
- **Transparência:** toda transformação é consequência direta de decisão explícita.
- **Nenhuma decisão de modelagem** é tomada nesta seção.

---

### 🔧 Padronização de nomenclatura (Seção 6)

A partir desta seção, todos os artefatos de saída relacionados à representação supervisionada
devem ser referenciados **exclusivamente** dentro do namespace `representation`, seguindo o padrão:

- `representation.X_train`
- `representation.X_test`
- `representation.y_train`
- `representation.y_test`
- `representation.feature_names`
- `representation.transformer`

Termos como `X_train_repr` / `y_train_repr` devem ser considerados apenas **aliases informais**
e não devem aparecer na documentação técnica canônica.

---

## [S6.1] Decisão de Representação das Features (X)

Esta etapa registra, de forma rastreável, como `X` será representado para modelagem supervisionada.

### Diagnóstico (entrada)
- `X_train` e `X_test` devem estar alinhados ao `scope.features` (mesma ordem e conjunto).
- Tipos finais devem refletir o estado pós-Seção 5 (sem encoding/scaling aplicados anteriormente).

### Decisão explícita (exemplo canônico)
- Categóricas: `OneHotEncoder(handle_unknown="ignore")`
- Numéricas: `passthrough` (sem scaling por padrão nesta fase)

> 📌 Qualquer outra estratégia (ex.: scaling) só é permitida se for declarada explicitamente em `decision`.

### Justificativa (sem antecipar Seção 7/8)
- A representação deve ser **estável** e **compatível com múltiplos modelos**, sem assumir métrica ou algoritmo.
- `handle_unknown="ignore"` é uma decisão de robustez para categorias presentes no teste e ausentes no treino.

---

## [S6.2] Execução do Pré-processamento (após decisão)

Esta etapa executa a transformação **somente após** a decisão estar declarada.

### Procedimento canônico (anti-leakage)
1. Construir transformador de `X` (ex.: `ColumnTransformer`) com rotas:
   - categóricas → encoder
   - numéricas → passthrough (ou scaler declarado)
2. `fit` do transformador em `X_train` **apenas**
3. `transform` em `X_train` e `X_test`
4. Extração de `feature_names` (ordem estável, rastreável)

### Auditorias obrigatórias pós-execução
- Shapes antes vs depois (`X_train`, `X_test`)
- `n_features_before` vs `n_features_after`
- Consistência treino/teste:
  - `same_feature_count == True`
  - `feature_names_match == True`
- Registro explícito:
  - `fit_on: "train_only"`

> ⚠️ Qualquer inconsistência entre treino e teste nesta fase deve interromper o pipeline (erro), pois compromete a validade da avaliação supervisionada.

---

## [S6.3] Decisão de Representação do Target (y)

Esta etapa define explicitamente como o target será representado para treinamento e avaliação.

### Diagnóstico do target
- Confirmar domínio observado em `y_train` e `y_test`
- Confirmar ausência de valores fora do mapping declarado (quando aplicável)

### Decisão explícita (exemplo canônico)
- Estratégia: `map_binary`
- Tipo final: `int64`
- Mapping (conforme domínio observado):
  - Dataset Telco (texto): `{"No": 0, "Yes": 1}`
  - Dataset Bancário (numérico): `{0: 0, 1: 1}`

> 📌 Quando o target já vem binário (0/1), o mapping pode ser uma **função identidade** (0→0, 1→1), usada para **materializar explicitamente** a representação, mantendo rastreabilidade e coerência com o contrato do pipeline.

### Garantias
- A codificação deve ser **determinística** e **rastreadora** (mapping exibido).
- A transformação deve ser aplicada de forma consistente em treino e teste.
- Nenhuma inferência automática (ex.: ordenar labels alfabeticamente) é permitida.

---

## [S6.4] Consolidação do Dataset Modelável (pronto para Seção 7)

Esta etapa encerra a Seção 6 consolidando o estado final modelável, sem decisões de avaliação/modelo.

### Artefatos finais consolidados
- `representation.X_train` e `representation.X_test` com mesma dimensionalidade
- `representation.y_train` e `representation.y_test` codificados conforme decisão
- `representation.feature_names` (base final de features)
- `representation.transformer` ajustado no treino (reutilizável na inferência)

### Respostas que o pipeline deve conseguir fornecer ao final
- Como `X` está representado?
- Como `y` está representado?
- Quantas features existem agora?
- Treino e teste estão consistentes?
- Quais decisões foram tomadas?
- Quais decisões **não** foram tomadas?

### Declaração explícita do que NÃO foi feito (limites da seção)
- ❌ Definição de métrica principal
- ❌ Treinamento de modelos (exceto “fit” do transformador de features)
- ❌ Baselines (DummyClassifier) e comparação
- ❌ GridSearch / tuning / ranking

---

## Observação geral da Seção 6

A Seção 6 encerra com o dataset **representado e auditado**, estabelecendo as condições mínimas para iniciar a Seção 7,
onde serão definidas métricas e baselines.

> ✅ Se `X` e `y` não estiverem representados de forma explícita e consistente, a Seção 7 **não deve** ser iniciada.

---

# Seção 7 — Estratégia de Avaliação e Baselines

## [S7.0] Contrato da Seção

### Objetivo
Definir explicitamente **o que significa ser bom** para o problema de churn bancário antes de qualquer comparação entre modelos.

Esta seção estabelece:
- critérios de avaliação,
- métrica principal e métricas secundárias,
- baselines mínimos aceitáveis,
- e os limites claros do que **não** é decidido aqui.

Nenhuma decisão implícita é permitida.

### Inputs
- `representation.X_train`
- `representation.X_test`
- `representation.y_train`
- `representation.y_test`  
(Resultantes da Seção 6, já auditadas e congeladas)

### Outputs
- Métrica principal definida (ou regra explícita de decisão entre métricas)
- Métricas secundárias registradas
- Resultados de baselines
- Artefatos auditáveis:
  - distribuição de classes
  - matriz de confusão (baselines)
  - relatório de métricas

### Funções envolvidas
- Core: `run_section7_evaluation_and_baselines`
- UI: `render_section7_evaluation_report`

### Garantias
- Nenhum modelo real é comparado
- Nenhum tuning é realizado
- Nenhuma feature é criada ou alterada
- Nenhum threshold é ajustado

### Limites
- Esta seção **não seleciona modelo**
- Esta seção **não ranqueia algoritmos**
- Esta seção **não otimiza score**

---

## [S7.1] Diagnóstico do Problema e Custo do Erro

### Classe Positiva
- `churn = 1`

### Contexto do Problema
O churn bancário representa a perda de clientes ativos.
Erros de classificação possuem impactos assimétricos:

- **Falso Negativo (FN)**  
  Cliente que iria sair é classificado como não churn → nenhuma ação preventiva é tomada.
- **Falso Positivo (FP)**  
  Cliente fiel é classificado como churn → possível custo operacional desnecessário.

### Avaliação do Custo Relativo
- FN tende a ser **mais custoso** que FP
- Retenção tardia geralmente é mais cara do que prevenção antecipada

📌 Conclusão:  
Métricas sensíveis à classe positiva devem ser consideradas com prioridade.

---

## [S7.2] Decisão de Métricas

### Métricas Candidatas
- Accuracy
- Precision (classe positiva)
- Recall (classe positiva)
- F1-score
- ROC-AUC

### Decisão
- **Métrica principal:** `Recall (classe positiva)`
- **Métrica secundária:** `F1-score`

### Regra Explícita
O modelo só poderá ser considerado aceitável na Seção 8 se:
- superar **ambos os baselines** na métrica principal (Recall),
- sem degradação crítica de Precision (avaliada qualitativamente).

---

## [S7.3] Baselines

### Objetivo do Baseline
Estabelecer um **piso mínimo** de desempenho.
Nenhum modelo real pode ser avaliado sem superar o baseline.

### Baselines Definidos
- `DummyClassifier(strategy="most_frequent")`
- `DummyClassifier(strategy="stratified")`

📌 Regra:  
Qualquer modelo futuro deve **superar ambos os baselines**
na métrica principal definida.

---

## [S7.4] Execução Leve e Auditoria

### Diagnósticos Gerados
- Distribuição de classes em treino e teste
- Predições dos baselines
- Matrizes de confusão
- Relatório de métricas:
  - Accuracy
  - Precision
  - Recall
  - F1-score

### Auditoria
Todos os resultados devem ser:
- reproduzíveis,
- registrados,
- interpretáveis sem contexto externo.

Nenhuma inferência automática é permitida.

---

## [S7.5] Fechamento da Seção

### Decisões Tomadas
- Métrica principal definida: **Recall**
- Métrica secundária: **F1-score**
- Baselines estabelecidos e executados
- Trade-off FN > FP explicitamente aceito

### Decisões Não Tomadas
- Escolha de modelo
- Ajuste de hiperparâmetros
- Ranking de algoritmos
- Ajuste de threshold

📌 Essas decisões ficam **exclusivamente** para a Seção 8.

---


## [S8] Modelos, Hiperparâmetros e Comparação Empírica

A Seção 8 é responsável pela **avaliação empírica controlada de modelos supervisionados**, utilizando os dados preparados até a Seção 6 e os critérios definidos na Seção 7.

Esta etapa **não altera dados, métricas ou decisões de risco**. Seu objetivo é gerar **evidência comparável e auditável** para fundamentar a escolha do modelo candidato à exportação.

---

### [S8.0] Contrato da Seção (visão operacional)

**Inputs**
- `payload_s5.split`
  - `X_train`, `X_test`, `y_train`, `y_test`
- `payload_s6.representation`
  - dados transformados (`X_train_rep`, `X_test_rep`)
  - artefato de transformação (pipeline/transformer)
- `payload_s7.decision`
  - métrica principal (governança de risco)
  - métricas secundárias
  - baselines conceituais

**Outputs**
- leaderboard consolidado de modelos
- métricas de avaliação no conjunto de teste
- registros de execução:
  - modelo
  - modo de treinamento
  - hiperparâmetros utilizados
- decisão empírica do modelo candidato à exportação

**Garantias**
- nenhum dado é modificado
- nenhuma métrica é redefinida
- nenhuma decisão de risco é alterada
- a execução ocorre **apenas por ação explícita do usuário**

---

### [S8.1] Seleção de Modelos

Define quais algoritmos supervisionados participam da avaliação empírica.

- múltipla seleção permitida
- execução em fila determinística
- modelos não selecionados não são avaliados

---

### [S8.2] Estratégia de Treinamento

Define o modo de treinamento aplicado a cada modelo.

- **Treino direto**
  - uso de hiperparâmetros explícitos
- **Busca de hiperparâmetros**
  - uso de GridSearchCV
  - parâmetros definidos via dicionário

O modo é exclusivo por modelo e não admite estados implícitos.

---

### [S8.3] Configuração de Hiperparâmetros

Os hiperparâmetros podem ser definidos a partir de duas fontes:

- painel de configuração (treino direto)
- dicionário de grid (busca de hiperparâmetros)

Os grids utilizados seguem definições **deliberadas e documentadas**, descritas no arquivo:

📄 `hyperparameter_grids.md`

---

### [S8.4] Execução Controlada

A execução dos experimentos:
- ocorre apenas ao acionar explicitamente o comando de execução
- segue ordem sequencial em fila
- gera logs auditáveis
- não é disparada automaticamente por alterações de configuração

---

### [S8.5] Avaliação no Conjunto de Teste

Cada modelo treinado é avaliado exclusivamente no conjunto de teste.

As métricas calculadas incluem:
- accuracy
- precision
- recall
- f1-score
- ROC-AUC

As métricas são calculadas de forma independente da métrica principal definida na Seção 7.

---

### [S8.6] Leaderboard

Os resultados são consolidados em um leaderboard empírico:

- ordenável dinamicamente por qualquer métrica
- destaque visual da métrica selecionada
- ranking informativo (não decisório)

O leaderboard **não impõe decisões automáticas**.

---

### [S8.7] Decisão Empírica

A leitura final dos resultados:
- identifica trade-offs entre modelos
- seleciona candidatos viáveis
- fundamenta a escolha do modelo a ser exportado

A decisão final mantém explícita a separação entre:
- **governança avaliativa** (Seção 7)
- **exploração empírica** (Seção 8)

---


## [S9] Exportação do Modelo

A Seção 9 é responsável por **materializar em artefato persistente** o modelo selecionado na Seção 8.
Nenhum novo treinamento, avaliação ou decisão ocorre nesta etapa.

O objetivo é garantir que o modelo exportado preserve integralmente:
- a representação de dados definida na Seção 6;
- os parâmetros aprendidos durante o treinamento;
- a decisão empírica documentada na Seção 8.

---

### [S9.0] Contrato da Seção (visão operacional)

**Inputs**
- `payload_s6.representation`
  - transformer / pipeline de pré-processamento
- `payload_s8.decision`
  - chave do modelo selecionado
  - estimador treinado correspondente
  - justificativa da decisão

**Outputs**
- artefato persistente do modelo:
  - pipeline completo de inferência (pré-processamento + modelo)
- metadados de exportação (opcional):
  - critério de decisão
  - timestamp
  - identificador do modelo

**Garantias**
- nenhum dado é modificado
- nenhum treinamento adicional é executado
- nenhuma métrica é recalculada
- nenhuma decisão é alterada

---

### [S9.1] Composição do Artefato Exportado

O artefato exportado deve conter **um único pipeline de inferência**, composto por:

1. etapa de pré-processamento (Seção 6)
2. modelo treinado e selecionado (Seção 8)

Essa composição garante consistência entre treino e inferência,
evitando divergências na transformação dos dados.

---

### [S9.2] Origem do Modelo

O modelo exportado:
- é exclusivamente aquele selecionado na Seção 8;
- não sofre ajustes adicionais;
- não é reavaliado nesta etapa.

A Seção 9 **consome a decisão**, não a redefine.

---

### [S9.3] Persistência

O pipeline final é persistido como artefato reutilizável,
utilizando formato adequado para objetos do scikit-learn.

A estratégia de persistência deve priorizar:
- reprodutibilidade,
- compatibilidade futura,
- simplicidade de carregamento.

---

### [S9.4] Metadados de Exportação (opcional)

Opcionalmente, podem ser persistidos metadados associados ao modelo exportado,
incluindo:

- identificador do modelo;
- critério principal de decisão;
- seção de origem da decisão;
- timestamp da exportação.

Esses metadados não interferem na inferência,
servindo apenas para auditoria e rastreabilidade.

---

### [S9.5] Encerramento do Pipeline de Modelagem

Com a conclusão da Seção 9:
- o pipeline de modelagem supervisionada é considerado encerrado;
- o modelo encontra-se pronto para uso em inferência futura;
- etapas subsequentes podem consumir o artefato exportado sem dependência do notebook.

A separação entre **decisão**, **materialização** e **consumo** é mantida explícita.
