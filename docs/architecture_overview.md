# 🏗️ Architecture Overview — ChurnInsight

Este documento descreve a **arquitetura oficial** do projeto **ChurnInsight**, desenvolvido no contexto do **Hackathon ONE + No Country 2025**.

O objetivo da arquitetura é permitir que um **modelo de Machine Learning** seja treinado em Python e disponibilizado de forma segura e escalável por meio de uma **API REST**, integrando times de **Data Science**, **Engenharia de Dados** e **Back-end Java**.

---

## 🎯 Visão Geral

O ChurnInsight é composto por **quatro camadas principais**:

1. **Data Science (Python / Notebooks)**
2. **Core de Dados e ML (Python)**
3. **Serviço de Inferência (Python / FastAPI)**
4. **API de Negócio (Java / Spring Boot)**

Essas camadas se comunicam por meio de um **contrato JSON bem definido**, garantindo desacoplamento entre responsabilidades.

---

## 🧱 Arquitetura em Camadas

### 1️⃣ Data Science — Exploração e Modelagem

Responsável por:
- Análise exploratória de dados (EDA)
- Engenharia de features
- Testes de modelos de classificação
- Avaliação de métricas
- Consolidação do modelo final

📁 Organização:
- Cada cientista de dados trabalha em seu próprio diretório:
  ```
  notebooks/individual/<nome>/
  ```
- Apenas o dataset original é compartilhado:
  ```
  data/raw/
  ```

Essa separação evita conflitos de código e dá liberdade para experimentação.

---

### 2️⃣ Core de Dados e ML — Python (`src/`)

Responsável por:
- Centralizar funções reutilizáveis
- Padronizar carregamento de dados
- Definir preprocessamentos oficiais
- Treinar e avaliar o modelo final

📁 Estrutura:
```
src/
├── data/
│   └── load_data.py
├── features/
│   └── preprocess.py
├── models/
│   ├── train_model.py
│   └── evaluate.py
```

Esse core funciona como um **SDK interno**, podendo ser reutilizado pelos notebooks individuais e pelo serviço de inferência.

---

### 3️⃣ Serviço de Inferência — Python / FastAPI

Responsável por:
- Carregar o modelo treinado (`joblib`)
- Expor um endpoint de previsão
- Validar entrada básica
- Retornar previsão e probabilidade

📌 Endpoint principal:
```
POST /predict
```

📁 Localização:
```
src/api_python/
```

Esse serviço é **interno**, focado apenas em ML, e não é exposto diretamente ao usuário final.

---

### 4️⃣ API de Negócio — Java / Spring Boot

Responsável por:
- Receber requisições externas (Postman, frontend, etc.)
- Validar rigorosamente os dados de entrada
- Mapear strings para enums internos
- Chamar o serviço FastAPI
- Tratar erros, logs e respostas

📁 Localização:
```
backend_java/
```

Essa é a **API oficial apresentada no Demo Day**.

---

## 🔄 Fluxo de Dados

```text
Cliente / Frontend
        ↓
API Java (Spring Boot)
        ↓
Serviço Python (FastAPI)
        ↓
Modelo de ML
        ↓
FastAPI retorna previsão
        ↓
Java retorna resposta final
```

---

## 🔌 Contrato de Integração

O contrato JSON garante que Java e Python se comuniquem corretamente.

### Entrada (exemplo)

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

### Saída (exemplo)

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
```

📄 Contrato completo:
```
docs/api_contract.md
```

---

## 🧠 Decisões Arquiteturais

- **FastAPI em Python** para servir o modelo:
  - alinhado ao ecossistema de ML
  - simples e rápido para inferência

- **Java / Spring Boot** como API de negócio:
  - forte validação
  - padrão enterprise
  - melhor apresentação no Demo Day

- **Contrato simples e enxuto**:
  - reduz risco de integração
  - facilita manutenção
  - adequado a um MVP

- **Separação clara de responsabilidades**:
  - evita acoplamento excessivo
  - facilita colaboração entre iniciantes

---

## 🚀 Extensões Futuras (Opcionais)

A arquitetura permite evoluções como:
- Persistência de previsões em banco
- Endpoint de estatísticas (`/stats`)
- Batch prediction (CSV)
- Dashboard simples
- Integração via ONNX (avançado)

Essas extensões não comprometem o fluxo principal.

---

## 📌 Conclusão

A arquitetura do ChurnInsight foi pensada para:
- ser simples,
- ser didática,
- refletir práticas reais de mercado,
- permitir colaboração entre perfis diferentes,
- entregar um MVP funcional dentro do prazo do hackathon.

Ela equilibra **qualidade técnica**, **aprendizado** e **viabilidade prática**.
