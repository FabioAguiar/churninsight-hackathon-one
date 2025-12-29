# Pipeline Principal — ChurnInsight
Este notebook representa o **pipeline operacional do projeto ChurnInsight**, apresentando de forma **visual, progressiva e narrativa** o fluxo completo de análise de dados — desde a ingestão até a preparação para modelagem.
O objetivo principal deste pipeline é **tornar explícito o estado atual dos dados em cada etapa**, permitindo que o leitor compreenda:
- qual dado está sendo utilizado,
- em que condição ele se encontra,
- e quais decisões técnicas serão tomadas.

---
## Como ler este pipeline

- O pipeline é organizado em **seções numeradas**, exibidas sequencialmente
- Cada seção contém **elementos visuais e indicadores técnicos**
- O foco aqui é **compreensão do fluxo**, não implementação de código
- A lógica técnica detalhada de cada elemento está documentada separadamente no documento de referência técnica

📎 [pipeline_elements.md](./pipeline_elements.md)

> 📌 Sempre que um elemento aparecer neste notebook, ele possui uma definição técnica correspondente no documento de referência.

---
## Estrutura geral do pipeline

O pipeline está dividido em grandes blocos conceituais:

1. **Ingestão e diagnóstico inicial**  
   Identificação da fonte de dados e avaliação básica de qualidade.

2. **Qualidade Estrutural & Tipagem**  
   Ajustes técnicos controlados (conversões, memória e checagens estruturais).

3. **Pré-processamento orientado à modelagem**  
   Aplicação de contrato (API) + diagnóstico categórico para orientar padronização.

Cada seção é construída para tornar **explícito** o estado dos dados e as decisões técnicas implícitas, garantindo que o avanço no pipeline ocorra com base em informações verificáveis.

---
## Princípio de Transformações Reversíveis vs Irreversíveis

Este pipeline distingue explicitamente entre dois tipos de operações:

### 🔁 Operações Reversíveis (Diagnóstico e Auditoria)
- Não alteram semanticamente o dataset
- Servem para inspeção, validação e tomada de decisão
- Podem ser executadas múltiplas vezes sem impacto cumulativo

Exemplos:
- Diagnóstico de qualidade
- Avaliação de impacto estrutural
- Descoberta de candidatos categóricos
- Auditorias e relatórios

Essas operações **não consolidam alterações no estado final dos dados**.

### 🔒 Operações Irreversíveis (Transformações Assumidas)
- Alteram o estado definitivo do dataset
- Exigem decisão explícita e rastreável
- São executadas apenas após validação técnica e semântica

Exemplos:
- Aplicação do contrato da API
- Padronização categórica
- Tratamento de dados faltantes
- Encoding e normalização para modelagem

Cada operação irreversível é documentada e executada apenas quando seu impacto é plenamente compreendido.

---
## Seção 1 — Ingestão e Diagnóstico Inicial

Esta seção marca o **ponto de entrada do pipeline**.

Seu papel é responder, de forma clara e imediata, às seguintes perguntas:

- Qual arquivo está sendo utilizado?
- Os dados estão completos?
- Há problemas estruturais evidentes?
- O dataset está apto para avançar no pipeline?

Os elementos exibidos a seguir **não realizam transformações** —  
eles **descrevem o estado atual dos dados** logo após a ingestão.

---
## Elementos da Seção 1 — Ingestão e Diagnóstico Inicial

Cada item abaixo possui uma descrição técnica detalhada no documento de referência:

📎 [pipeline_elements.md — Seção 1 (início)](./pipeline_elements.md#s11-elemento--arquivo)

---

<!-- Âncora visual canônica da Seção 1 -->
<p align="center">
  <img src="./images/card_s1_ingestao_diagnostico_inicial.png"
       alt="Seção 1 — Ingestão e Diagnóstico Inicial (cards numerados)"
       width="95%">
</p>

<p align="center">
  <em>
    Visão geral dos cards da Seção 1 (Ingestão e Diagnóstico Inicial), com
    indexação visual utilizada como referência ao longo desta seção.
  </em>
</p>


---
### 1️⃣ Elemento — Arquivo

Indica qual arquivo de dados bruto está sendo utilizado como fonte ativa do pipeline, garantindo rastreabilidade entre o notebook e a origem física dos dados.

**Referência técnica:**  
[S1.1 — Elemento: Arquivo](./pipeline_elements.md#s11-elemento--arquivo)

---
### 2️⃣ Indicador — Faltantes (Global)

Apresenta uma visão consolidada da presença de valores ausentes no dataset, funcionando como um indicador inicial de qualidade dos dados e sinalizando severidade de forma resumida.

**Referência técnica:**  
[S1.2 — Indicador: Faltantes (Global)](./pipeline_elements.md#s12-indicador--faltantes-global)

---
### 3️⃣ Card — Métricas gerais

Exibe métricas estruturais básicas do dataset (volume de registros, colunas e memória), oferecendo uma visão imediata da dimensão dos dados ingeridos.

**Referência técnica:**  
[S1.3 — Card: Métricas gerais](./pipeline_elements.md#s13-secao--metricas-gerais)

---
### 4️⃣ Card — Tipos de dados

Resume a distribuição dos tipos de dados presentes no dataset, apoiando o entendimento estrutural e antecipando decisões de pré-processamento.

**Referência técnica:**  
[S1.4 — Card: Tipos de dados](./pipeline_elements.md#s14-secao--tipos-de-dados)

---
### 5️⃣ Card — Faltantes (top N)

Lista as colunas com maior incidência de valores ausentes, permitindo identificar rapidamente pontos críticos e priorizar intervenções futuras.

**Referência técnica:**  
[S1.5 — Card: Faltantes (top N)](./pipeline_elements.md#s15-secao--faltantes-top-n)

---
### Observação geral da seção

Os elementos desta seção **não alteram o dataset**.  
Eles estabelecem um **ponto de referência inicial**, sobre o qual as decisões técnicas das etapas seguintes serão fundamentadas.

---
## Seção 2 — Qualidade Estrutural & Tipagem

Esta seção aprofunda a análise do dataset já ingerido, com foco na **integridade estrutural** após conversões e validações técnicas básicas.

Diferente da Seção 1, aqui o objetivo é tornar explícitos **impactos técnicos reais** decorrentes de ajustes necessários para o avanço seguro do pipeline.

As ações desta seção **não aplicam transformações semânticas** nem decisões de negócio.  
Elas se concentram em garantir que o dataset esteja **tecnicamente consistente**, bem tipado e livre de problemas estruturais críticos.

---
### O que esta seção responde

Ao final desta etapa, o pipeline deve ser capaz de responder com clareza:

- O dataset sofreu alterações estruturais após conversões?
- Quais colunas tiveram seus tipos ajustados?
- As conversões introduziram novos valores ausentes?
- Existem problemas de duplicidade (integridade estrutural)?
- O dataset está apto para avançar para o recorte semântico (contrato da API)?

---

### Contrato de UI (artefatos esperados)

A UI desta seção consome artefatos pré-calculados pelo core (tabelas e dicionários) — o notebook apenas exibe.

**Referência técnica:**  
[S2.0 — Contrato de UI da Seção 2 (artefatos esperados)](./pipeline_elements.md#s20-contrato-de-ui-da-secao-2-artefatos-esperados)

---

## Elementos da Seção 2 — Qualidade Estrutural & Tipagem

 Cada item abaixo possui uma descrição técnica detalhada no documento de referência:

 [pipeline_elements.md — Seção 2 (início)](./pipeline_elements.md#s21-secao--impacto-estrutural-antesxdepois)

---

<!-- Âncora visual canônica da Seção 2 -->
<p align="center">
  <img src="./images/card_s2_qualidade_estrutural_tipagem.png"
       alt="Seção 2 — Qualidade Estrutural & Tipagem (cards numerados)"
       width="95%">
</p>

<p align="center">
  <em>
    Visão geral dos cards da Seção 2 (Qualidade Estrutural & Tipagem), com
    indexação visual utilizada como referência ao longo desta seção.
  </em>
</p>

---

### Elementos apresentados nesta seção

📎 [pipeline_elements.md — Seção 2 (início)](./pipeline_elements.md#s21-secao--impacto-estrutural-antesxdepois)

---
### 1️⃣ Card — Impacto estrutural (Antes × Depois)

Comparativo direto entre o estado estrutural do dataset **antes e depois** das validações e conversões aplicadas (linhas, colunas e memória).

**Referência técnica:**  
[S2.1 — Impacto estrutural (Antes × Depois)](./pipeline_elements.md#s21-secao--impacto-estrutural-antesxdepois)

---
### 2️⃣ Card — Conversões de tipos aplicadas

Lista exclusivamente as colunas que tiveram seus tipos convertidos, destacando efeitos colaterais relevantes (incluindo nulos introduzidos).

**Referência técnica:**  
[S2.2 — Conversões de tipos aplicadas](./pipeline_elements.md#s22-secao--conversoes-de-tipos-aplicadas)

---
### 3️⃣ Card — Integridade estrutural

Indicador sintético de integridade: informa se há registros duplicados no dataset (checagem conservadora, sem correção automática).

**Referência técnica:**  
[S2.3 — Indicador: Integridade estrutural](./pipeline_elements.md#s23-indicador--integridade-estrutural)

---
### 4️⃣ Card — Nulos introduzidos por conversão

Resumo dos valores ausentes que surgiram **como consequência direta** das conversões de tipo, diferenciando-os de nulos já existentes no bruto.

**Referência técnica:**  
[S2.4 — Nulos introduzidos por conversão](./pipeline_elements.md#s24-secao--nulos-introduzidos-por-conversao)

---
### Observação geral da seção

Os elementos desta seção **podem alterar a estrutura técnica do dataset**, mas **não modificam seu significado semântico**.

Eles estabelecem um estado confiável e validado, a partir do qual o pipeline pode avançar para a etapa de **conformidade ao contrato (API)** com rastreabilidade total.

---
## Seção 3 — Conformidade ao Contrato de Entrada (API) & Diagnóstico Categórico

Esta seção marca o **início do pré-processamento orientado à modelagem**, estabelecendo um elo explícito entre:

- o dataset **tecnicamente validado** nas etapas anteriores, e  
- o **contrato formal de entrada da API de previsão**.

Aqui é introduzido o conceito de **escopo semântico**, tornando explícito:

- quais colunas **participam do modelo**,  
- quais colunas são **descartadas**, e  
- quais colunas **exigirão tratamento categórico** nas próximas etapas.

📎 **Referência externa obrigatória**  
O contrato aplicado nesta seção está documentado em `api_contract.md`.

---

<!-- Âncora visual canônica da Seção 3 -->
<p align="center">
  <img src="./images/card_s3_conformidade_contrato_api_01.png"
       alt="Seção 3 — Conformidade ao Contrato de Entrada (API) & Diagnóstico Categórico (cards numerados)"
       width="95%">
</p>

<p align="center">
  <em>
    Visão geral dos cards da Seção 3 (Conformidade ao Contrato de Entrada (API) & Diagnóstico Categórico),
    com indexação visual utilizada como referência ao longo desta seção.
    <br>
    Os cards numerados (1–7) correspondem diretamente às descrições textuais apresentadas a seguir.
  </em>
</p>

---
### Contrato de UI (payload esperado)

A UI desta seção opera sobre um `payload` consolidado (df + relatórios de contrato/scope/candidatos). O notebook apenas exibe.

**Referência técnica:**  
[S3.0 — Contrato de UI da Seção 3 (payload esperado)](./pipeline_elements.md#s30-contrato-de-ui-da-secao-3-payload-esperado)

---
### Elementos apresentados nesta seção

📎 [pipeline_elements.md — Seção 3 (início)](./pipeline_elements.md#s31-secao--conformidade-ao-contrato-de-entrada-api)

---
### 1️⃣ Card — Conformidade ao Contrato de Entrada (API)

Exibe as **colunas mantidas** após aplicar o contrato:
- features do contrato
- + target (apenas no pipeline supervisionado)

**Referência técnica:**  
[S3.1 — Conformidade ao Contrato de Entrada (API)](./pipeline_elements.md#s31-secao--conformidade-ao-contrato-de-entrada-api)

---
### 2️⃣ Card — Impacto Estrutural (Antes × Depois)

Comparativo estrutural entre o estado do dataset **antes e depois** da aplicação do contrato (linhas, colunas, memória).

**Referência técnica:**  
[S3.2 — Impacto Estrutural (Antes × Depois)](./pipeline_elements.md#s32-secao--impacto-estrutural-antesxdepois)

---
### 3️⃣ Card — Auditoria de Colunas

Documenta o papel semântico dos grupos de colunas no pipeline:

- **Target** (quando presente): mantido, mas **fora do diagnóstico categórico**  
- **Features**: as variáveis de entrada do contrato  
- **Descartadas**: colunas removidas por estarem fora do contrato

**Referência técnica:**  
[S3.3 — Auditoria de Colunas](./pipeline_elements.md#s33-secao--auditoria-de-colunas)

---
### 4️⃣ Card — Descoberta de Candidatos

Resumo quantitativo do diagnóstico categórico:

- total de colunas analisadas (features)  
- candidatas  
- prováveis binárias  
- colunas com frases de serviço  
- excluídas do diagnóstico (ex.: target)

**Referência técnica:**  
[S3.4 — Descoberta de Candidatos](./pipeline_elements.md#s34-indicador--descoberta-de-candidatos)

---
### 5️⃣ Card — Top Candidatos

Tabela detalhada com as principais colunas candidatas à padronização categórica (cardinalidade, % únicos, amostra, motivos).

**Referência técnica:**  
[S3.5 — Top Candidatos](./pipeline_elements.md#s35-secao--top-candidatos)

---
### 6️⃣ Card — Provavelmente Binárias (Yes/No ou 0/1)

Lista colunas cujo conjunto de valores sugere binariedade semântica, sinalizando necessidade de encoding específico.

**Referência técnica:**  
[S3.6 — Provavelmente Binárias (Yes/No ou 0/1)](./pipeline_elements.md#s36-secao--provavelmente-binarias-yes-no-ou-0-1)

---
### 7️⃣ Card — Frases de Serviço Detectadas

Sinaliza colunas com frases compostas (ex.: “No internet service”), que normalmente exigem regra explícita de normalização.

**Referência técnica:**  
[S3.7 — Frases de Serviço Detectadas](./pipeline_elements.md#s37-secao--frases-de-servico-detectadas)

---
### Observação geral da seção

Os elementos desta seção **não aplicam padronização nem encoding**.  
Eles estabelecem:

- conformidade explícita com o **contrato de entrada da API**,  
- separação clara entre **features**, **target** e **descartadas**,  
- e um **diagnóstico completo** que fundamenta a próxima etapa de padronização categórica.

---

## Seção 3.2 — Padronização Categórica (Execução)

Esta etapa marca a transição do diagnóstico para a ação: o pipeline passa a executar padronizações categóricas de forma auditável, com base em regras declaradas explicitamente no notebook.

A execução desta etapa obedece aos seguintes princípios:

- aplica apenas normalização textual mínima (ex.: `lower`, `strip`, colapso de espaços)
- aplica apenas substituições explícitas (ex.: `"no internet service" → "no"`)
- não executa encoding
- não altera colunas fora do escopo (restrita às features do contrato)
- não toca no target (mantido, porém fora desta transformação)
- gera um relatório rastreável: impacto estrutural, regras aplicadas e mudanças por coluna

---

### Contrato de UI (payload esperado)

A UI desta etapa consome um payload consolidado (`df` + impacto + regras + mudanças + decisão explícita). O notebook apenas exibe.

**Referência técnica:**  
[S3.8 — Contrato de UI da Seção 3.2 (payload esperado)](./pipeline_elements.md#s38-contrato-de-ui-da-secao-32-payload-esperado)

---

## Elementos da Seção 3.2 — Padronização Categórica (Execução)

Cada item abaixo possui uma descrição técnica detalhada no documento de referência:

📎 [pipeline_elements.md — Seção 3.2 (início)](./pipeline_elements.md#s32pre-fase-de-execucao-tecnica--padronizacao-categorica-execucao)

---

<!-- Âncora visual canônica da Seção 3.2 -->
<p align="center">
  <img src="./images/card_s3_padronizacao_categorica_execucao.png"
       alt="Seção 3.2 — Padronização Categórica (Execução) (cards numerados)"
       width="95%">
</p>

<p align="center">
  <em>
    Visão geral dos cards da Seção 3.2 (Execução da Padronização Categórica), com indexação visual utilizada como referência ao longo desta etapa.
    <br>
    Os cards numerados (S3.9–S3.13) correspondem diretamente às descrições textuais apresentadas a seguir.
  </em>
</p>

---

### 1️⃣ Card — Decisão explícita (derivada do diagnóstico)

Declara, de forma rastreável, quais regras e quais colunas foram selecionadas para execução, deixando explícita a diferença entre:

- seleção derivada do diagnóstico (intenção)
- escopo final aplicado (execução real após filtros do contrato)

**Referência técnica:**  
[S3.9 — Decisão explícita (derivada do diagnóstico)](./pipeline_elements.md#s39-card--decisao-explicita-derivada-do-diagnostico)

---

### 2️⃣ Card — Resumo da execução

Resumo sintético do que ocorreu na execução:

- total de células alteradas
- confirmação de que encoding não foi aplicado
- confirmação de que o target não foi alterado

**Referência técnica:**  
[S3.10 — Resumo da execução](./pipeline_elements.md#s310-card--resumo-da-execucao)

---

### 3️⃣ Card — Impacto estrutural (Antes × Depois)

Comparativo estrutural do dataset antes e depois da padronização (linhas, colunas e memória), como trilha de auditoria do impacto técnico.

**Referência técnica:**  
[S3.11 — Impacto estrutural (Antes × Depois)](./pipeline_elements.md#s311-card--impacto-estrutural-antes--depois)

---

### 4️⃣ Card — Regras aplicadas

Lista as regras efetivamente utilizadas na execução (ex.: `from → to`), garantindo rastreabilidade do que foi aplicado ao dataset.

**Referência técnica:**  
[S3.12 — Regras aplicadas](./pipeline_elements.md#s312-card--regras-aplicadas)

---

### 5️⃣ Card — Relatório de mudanças (auditável)

Tabela de auditoria por coluna indicando:

- volume de alterações (`cells_changed`)
- tipo de regra aplicada (`rule_type`)
- exemplos de mudanças observadas (`examples`)

**Referência técnica:**  
[S3.13 — Relatório de mudanças (auditável)](./pipeline_elements.md#s313-card--relatorio-de-mudancas-auditavel)

---

### Observação geral da etapa

Esta etapa executa padronização categórica de forma controlada, sendo uma transformação assumida no estado do dataset (irreversível no pipeline).  
O escopo permanece restrito às features do contrato, e o target é preservado sem modificações.

## Seção 4 — Tratamento de Dados Faltantes (Execução)

Esta seção executa o **tratamento de valores ausentes** por meio de **imputação** — uma transformação
**irreversível** no estado do pipeline.

Aqui, o objetivo é tornar explícito:

- **quais colunas** serão tratadas (restritas às *features* do contrato),
- **quais estratégias** foram escolhidas (numérica vs categórica),
- **o impacto** (quantidade imputada e auditoria por coluna),
- e a confirmação de que o **target permanece intocado**.

> 📌 Esta seção não faz encoding, não normaliza features numéricas, não cria features novas e não remove colunas.

---

<!-- Âncora visual canônica da Seção 4 -->
<p align="center">
  <img src="./images/card_s4_tratamento_dados_faltantes_execucao.png"
       alt="Seção 4 — Tratamento de Dados Faltantes (Execução) (cards numerados)"
       width="95%">
</p>

<p align="center">
  <em>
    Visão geral dos cards da Seção 4 (Tratamento de Dados Faltantes — Execução),
    com indexação visual utilizada como referência ao longo desta etapa.
  </em>
</p>

---

### Contrato de UI (payload esperado)

A UI desta seção consome um payload consolidado (`df` + decisão explícita + impacto + relatório por coluna).
O notebook apenas exibe.

**Referência técnica:**  
[S4.0 — Contrato de UI da Seção 4 (payload esperado)](./pipeline_elements.md#s40-contrato-de-ui-da-secao-4-payload-esperado)

---

### Elementos apresentados nesta seção

📎 [pipeline_elements.md — Seção 4 (início)](./pipeline_elements.md#secao-4--tratamento-de-dados-faltantes-execucao)

---

### 1️⃣ Card S4.1 — Decisão explícita de imputação

Declara, de forma rastreável:

- quais colunas foram intencionalmente incluídas/excluídas,
- quais estratégias foram escolhidas por tipo (numérica/categórica),
- qual foi o escopo final aplicado (features ∩ intenção ∩ colunas existentes),
- confirmação explícita de que o target **não** será imputado automaticamente.

**Referência técnica:**  
[S4.1 — Decisão explícita de imputação](./pipeline_elements.md#s41-card--decisao-explicita-de-imputacao)

---

### 2️⃣ Card S4.2 — Resumo da execução

Resumo sintético do que ocorreu na execução:

- total de valores imputados,
- número de colunas afetadas,
- confirmação de preservação do target,
- e (quando aplicável) motivo de não execução (ex.: ausência de escopo).

**Referência técnica:**  
[S4.2 — Resumo da execução](./pipeline_elements.md#s42-card--resumo-da-execucao)

---

### 3️⃣ Card S4.3 — Impacto estrutural (Antes × Depois)

Auditoria técnica do impacto de imputação:

- linhas
- colunas
- memória

Esta etapa **não deve** alterar shape — qualquer alteração indica bug.

**Referência técnica:**  
[S4.3 — Impacto estrutural (Antes × Depois)](./pipeline_elements.md#s43-card--impacto-estrutural-antes--depois)

---

### 4️⃣ Card S4.4 — Estratégias aplicadas

Tabela por coluna contendo:

- coluna
- tipo (numérica/categórica)
- estratégia
- valor utilizado (quando aplicável)

**Referência técnica:**  
[S4.4 — Estratégias aplicadas](./pipeline_elements.md#s44-card--estrategias-aplicadas)

---

### 5️⃣ Card S4.5 — Relatório de imputação (auditável)

Relatório detalhado por coluna:

- faltantes antes/depois
- quantidade imputada
- percentual imputado
- estratégia e valor utilizado

Este card fecha a etapa com auditoria verificável.

**Referência técnica:**  
[S4.5 — Relatório de imputação (auditável)](./pipeline_elements.md#s45-card--relatorio-de-imputacao-auditavel)

---

### Observação geral da seção

A Seção 4 executa imputação como transformação irreversível, com decisão explícita e rastreabilidade total.
O resultado é um dataset semanticamente consistente, com faltantes tratados (ou exceções explicitadas),
pronto para etapas posteriores (encoding, normalização e modelagem).
