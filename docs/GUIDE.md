# 🧭 Guia Prático — ChurnInsight (End-to-End)
**Hackathon ONE | ChurnInsight Bancário**  | **Team Nexus**

Este guia apresenta uma visão **equilibrada, prática e direta** de como o **ChurnInsight** funciona de ponta a ponta.  
O objetivo é permitir que qualquer integrante da equipe ou avaliador do hackathon consiga **entender, executar e validar** o sistema completo sem esforço cognitivo excessivo.

> 🔑 Estrutura do guia:
> - **Parte 1 — Data Science**: Como gerar o modelo.
> - **Parte 2 — Infra & Execução**: Como subir, integrar e validar os serviços.

---

## PARTE 1 — DATA SCIENCE

### 1.1 Papel do notebook `pipeline_main.ipynb`

O notebook é o **orquestrador oficial** do pipeline de Data Science.  
Ele é responsável por:

- carregar o dataset bancário ([Bank Customer Churn Dataset — Kaggle](https://www.kaggle.com/datasets/gauravtopre/bank-customer-churn-dataset))
- aplicar o **contrato interno (`bank_churn.yaml`)**
- treinar e avaliar modelos
- exportar o **artefato final de inferência**

📦 **Saída**
```
artifacts/churn_model.joblib
```

---

### 1.2 Contrato interno como fonte de verdade

Arquivo central:
```
contracts/bank_churn.yaml
```

Ele define:
- target (`Exited`)
- features internas reais do modelo
- mapping explícito do payload externo (8 campos) → modelo (6 features), conforme definido no contrato da API ([docs/api_contract.md](docs/api_contract.md))
- defaults controlados (compatibilidade)

---

### 1.3 Execução prática do pipeline

1. Abrir `notebooks/pipeline_main.ipynb`.

2. Executar o notebook de forma sequencial, respeitando a ordem das seções:
   - executar todas as etapas iniciais do pipeline, desde a ingestão dos dados até a **avaliação e comparação dos modelos candidatos**;
   - na etapa de **seleção de modelo**, escolher explicitamente o estimador que será adotado como modelo final.  
     Os **valores padrão de hiperparâmetros** utilizados nos grids de busca estão documentados em:
     ```
     docs/hyperparameter_grids.md
     ```

3. Após a definição do modelo, prosseguir para a **exportação do artefato final** e confirmar que o arquivo foi gerado em:
   ```
   artifacts/churn_model.joblib
   ```


---

## PARTE 2 — INFRA & EXECUÇÃO (DOCKER)

Esta parte foca **exclusivamente no que é necessário para rodar os serviços**.

---

### 2.1 Arquitetura resumida

```
Usuário
  ↓
Streamlit (UI)
  ↓
Java API (Gateway)
  ↓
FastAPI (Inferência)
  ↓
Modelo + Contrato Interno
```

**Princípios**
- contrato externo imutável
- FastAPI como ponte semântica
- Java sem dependência de ML
- modelo isolado como detalhe de implementação

---

### 2.2 Componentes e responsabilidades

**Streamlit**
- UI em contexto bancário
- gera payload Telco-like (8 campos), mantendo compatibilidade com o contrato externo da API ([docs/api_contract.md](docs/api_contract.md))

**Java (Spring Boot)**
- recebe `/api/predict`
- valida e orquestra chamadas

**FastAPI**
- aplica contrato interno
- monta DataFrame interno
- executa inferência
- retorna `{ previsao, probabilidade }`

---

### 2.3 Pré-requisitos antes de subir

Checklist rápido:

- ✅ `artifacts/churn_model.joblib`
- ✅ `contracts/bank_churn.yaml`
- ✅ Docker e Docker Compose funcionando
- ✅ Portas livres:
  - 8501 (Streamlit)
  - 8080 (Java)
  - 8001 (FastAPI)

---

### 2.4 Subindo tudo (passo único)

Certifique-se de que o **Docker Desktop (Docker Engine)** está em execução.

O arquivo `docker-compose.yml` está no diretório `docker/`. Execute os comandos a partir dele:

```bash
docker compose up --build
```

Ou em background:

```bash
docker compose up --build -d
```

Serviços esperados:
- `churn-streamlit`
- `churn-java-api`
- `churn-python-api`

---

### 2.5 Validação rápida (5 minutos)

- FastAPI health  
  `http://localhost:8001/health`

- Streamlit  
  `http://localhost:8501`

- Fluxo completo:
  1. preencher formulário
  2. enviar
  3. receber previsão + probabilidade variável

---

### 2.6 Exemplos de cenários de entrada (validação orientada)

A seguir estão alguns **exemplos de cenários de preenchimento da interface**, com o objetivo de orientar a avaliação do comportamento do modelo durante a demonstração.

Os valores são ilustrativos e servem apenas para **comparação relativa entre cenários**.

#### Cenário 1 — Perfil com menor risco de evasão
- Tempo como cliente: 12
- Salário estimado: 3500,00
- Número de produtos: 2
- Credit Score: 600
- Possui cartão de crédito: sim
- Cliente ativo: sim

**Resultado esperado:**  
Probabilidade de evasão baixa: 32.0%

---

#### Cenário 2 — Perfil intermediário
- Tempo como cliente: 7
- Salário estimado: 1000,00
- Número de produtos: 1
- Credit Score: 820
- Possui cartão de crédito: sim
- Cliente ativo: sim

**Resultado esperado:**  
Probabilidade de evasão intermediária: 50%

---

#### Cenário 3 — Perfil com maior risco de evasão
- Tempo como cliente: 14
- Salário estimado: 3500,00
- Número de produtos: 3
- Credit Score: 100
- Possui cartão de crédito: sim
- Cliente ativo: não

**Resultado esperado:**  
Probabilidade de evasão mais elevada: 78.0%

---

Esses cenários permitem validar rapidamente se o sistema está respondendo de forma coerente às variações de perfil, sem a necessidade de inspeção técnica interna.

---

## Encerramento

Este guia formaliza o funcionamento completo do ChurnInsight, consolidando as decisões técnicas, arquiteturais e operacionais adotadas ao longo do projeto.

A solução apresentada:
- preserva o **contrato externo estável** da API;
- introduz um **contrato interno explícito** como fonte de verdade do domínio bancário;
- garante rastreabilidade entre **treino, inferência e execução em produção**;
- permite evolução do modelo sem impacto nas integrações existentes.

Para aprofundamento ou auditoria técnica, a documentação complementar em `docs/` deve ser utilizada como referência oficial.

---

**ChurnInsight — Team Nexus | Hackathon ONE 2025**
