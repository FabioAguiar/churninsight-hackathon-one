
# 🔍 ChurnInsight — Hackathon ONE
**Previsão de Cancelamento de Clientes (Churn) — Dataset Bancário**  
**Team Nexus**

Este repositório apresenta a solução final do projeto **ChurnInsight**, desenvolvida para o Hackathon ONE.  
O objetivo é prever a **probabilidade de evasão (churn)** de clientes bancários e disponibilizar essa previsão por meio de uma **arquitetura desacoplada, rastreável e integrável**, simulando um cenário real de produção.

O projeto foi concebido como um **MVP completo e funcional**, com foco em:
- clareza arquitetural
- contratos explícitos
- integração entre times (Data Science e Back-end)
- facilidade de execução para avaliação e demonstração

---

## 🏗️ Visão Geral da Arquitetura

A solução adota uma arquitetura em camadas, inspirada em ambientes reais de mercado:

```
Usuário
  ↓
Frontend (Streamlit)
  ↓
API de Negócio (Java / Spring Boot)
  ↓
Serviço de Inferência (Python / FastAPI)
  ↓
Pipeline ML + Contrato Interno
```

### Camadas

- **Data Science (Python / Notebooks)**  
  Exploração, engenharia de features, seleção e avaliação de modelos.

- **Core de Dados e ML (Python)**  
  Pipeline canônico, preprocessamento oficial, treino controlado e exportação de artefatos.

- **Serviço de Inferência (FastAPI)**  
  Ponte semântica entre o contrato externo estável e o contrato interno do modelo.

- **API Oficial (Java / Spring Boot)**  
  Camada de negócio responsável por validações, orquestração e exposição pública da previsão.

📌 Detalhamento completo:  
`docs/architecture_overview.md`

---

## 🔌 Contratos e Integração

### Contrato Externo (Estável)

A API exposta mantém um contrato **Telco-like**, estável e independente do dataset bancário:

```json
{
  "tenure": 12,
  "contract": "Month-to-month",
  "internet_service": "Fiber optic",
  "online_security": "No",
  "tech_support": "No",
  "monthly_charges": 89.5,
  "paperless_billing": "Yes",
  "payment_method": "Electronic check"
}
```

### Resposta

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.52
}
```

📄 Contrato completo e enums:  
`docs/api_contract.md`

### Contrato Interno (Fonte de Verdade)

O modelo utiliza um **contrato interno explícito**, baseado no dataset bancário:

```
contracts/bank_churn.yaml
```

Esse contrato define:
- target
- features reais do modelo
- regras de mapeamento do contrato externo → modelo
- defaults controlados

Essa abordagem permite **evolução do modelo sem impacto nas integrações externas**.

---

## 🧠 Pipeline de Machine Learning

- Pipeline canônico definido em `pipeline_main.ipynb`
- Pré-processamento + modelo encapsulados em `Pipeline`
- Avaliação e seleção explícita de modelos
- Exportação final do artefato de inferência

📦 Artefato final:
```
artifacts/churn_model.joblib
```

O pipeline garante **rastreabilidade completa** entre:
- dados de treino
- modelo selecionado
- inferência em produção

---

## 🔬 Organização do Time de Data Science

### Compartilhado
- Dataset em `data/`
- Código reutilizável em `src/`
- Pipeline oficial controlado

### Individual
```
notebooks/individual/<nome>/
```

Cada integrante pode:
- explorar modelos
- realizar análises adicionais
- gerar evidências visuais

Sem alterar o pipeline oficial.

📌 Guia: `docs/how_to_data_science.md`

---

## 🚀 Execução com Docker (End-to-End)

O projeto é executado via **Docker Compose**, com múltiplos serviços integrados.

### Pré-requisitos
- Docker Desktop (Engine em execução)
- Portas livres:
  - 8501 (Streamlit)
  - 8080 (Java)
  - 8001 (FastAPI)

### Subindo os serviços

```bash
docker compose up --build
```

Ou em background:

```bash
docker compose up --build -d
```

### Serviços esperados
- `churn-streamlit`
- `churn-java-api`
- `churn-python-api`

---

## ✔ Status do Projeto

- Arquitetura definida e validada
- Contratos externo e interno explícitos
- Pipeline de ML fechado e rastreável
- Modelo avaliado e documentado
- Integração Python + Java funcional
- Frontend operacional para demonstração

---

## 📝 Observações Finais

O **ChurnInsight** demonstra uma abordagem realista para projetos de churn em produção, equilibrando:

- rigor técnico
- simplicidade operacional
- clareza de integração
- colaboração entre perfis técnicos

Este repositório representa o **estado final do projeto para avaliação no Hackathon ONE 2025**.

---

**ChurnInsight — Team Nexus | Hackathon ONE**
