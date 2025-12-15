# 🔍 ChurnInsight — Hackathon ONE + No Country 2025  
Previsão de Cancelamento de Clientes com Python (ML) + Java (API REST)

Este repositório contém a solução desenvolvida para o desafio **ChurnInsight**, cujo objetivo é prever a probabilidade de um cliente cancelar um serviço recorrente (**churn**) e disponibilizar essa previsão por meio de uma **API REST**.

O projeto foi concebido como um **MVP funcional e integrável**, priorizando clareza arquitetural, simplicidade de execução e colaboração entre perfis técnicos distintos (Data Science e Back-end).

---

## 🏗️ Visão Geral da Arquitetura

A solução é organizada em camadas bem definidas, inspiradas em cenários reais de mercado:

- **Data Science (Python / Notebooks)**  
  Exploração dos dados, engenharia de features e experimentação de modelos, de forma individual e colaborativa.

- **Core de Dados e ML (Python)**  
  Camada central com funções reutilizáveis, preprocessamento oficial, treino controlado e exportação do modelo.

- **Serviço de Inferência (Python / FastAPI)**  
  Microserviço interno responsável por carregar o modelo treinado e gerar previsões de churn.

- **API Oficial (Java / Spring Boot)**  
  API de negócio responsável por validações, regras, integração com o serviço Python e exposição ao usuário final.

📌 Detalhamento completo da arquitetura:  
`docs/architecture_overview.md`

---

## 🔌 Contrato de Integração (Resumo)

### Entrada (JSON)

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

### Saída (JSON)

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.52
}
```

📄 Contrato completo, enums e valores permitidos:  
`docs/api_contract.md`

---

## 🧠 Objetivo do MVP

- Classificação binária de churn  
- Retorno de probabilidade associada  
- Exposição via API REST  
- Integração Python + Java  
- Execução simples para Demo Day  

---

## 🔬 Organização do Time de Data Science

### Compartilhado
- Dataset em `data/raw/`
- Core de funções e pipeline em `src/`

### Individual
```
notebooks/individual/<nome>/
```

📌 Guia completo: `docs/how_to_data_science.md`

---

## 🧪 Modelo Versionado para Integração

```
artifacts/churn_model.joblib
```

Modelo provisório, aderente ao contrato e substituível.

---

## 🚀 Serviço de Inferência (FastAPI)

```
uvicorn src.api_python.main:app --reload --port 8001
```

Endpoint:
```
POST http://localhost:8001/predict
```

---

## 🏗️ API Oficial (Java)

Responsável por validações, integração HTTP, regras de negócio e resposta final.

---

## 🐳 Deploy com Docker + OCI

```
docker build -t churninsight-api .
docker run -p 8001:8001 churninsight-api
```

---

## ✔ Status do Projeto

- Arquitetura definida  
- Contrato estável  
- Modelo provisório funcional  
- FastAPI operacional  

---

## 📝 Observações Finais

Projeto desenvolvido com foco em integração, clareza e MVP funcional.
