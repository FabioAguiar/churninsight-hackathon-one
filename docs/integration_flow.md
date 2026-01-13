# 🔄 Integration Flow — ChurnInsight

Este documento descreve o **fluxo de integração completo** entre as camadas do projeto **ChurnInsight**, desde a requisição externa até a geração da previsão pelo modelo de **Machine Learning**.

O objetivo é deixar claro:

- como os componentes se comunicam,
- quem é responsável por cada etapa,
- onde ocorrem validações,
- e onde acontece a adaptação entre o **contrato externo da API** e o **modelo interno**.

---

## 🎯 Visão Geral do Fluxo

O **ChurnInsight** segue uma arquitetura **desacoplada e orientada a contrato**, onde:

- a **API Java (Spring Boot)** atua como camada de entrada e governança,
- o **serviço Python (FastAPI)** atua como camada de inferência e adaptação,
- o **modelo de ML** permanece isolado como detalhe de implementação.

Esse desenho permite a **troca de dataset e modelo sem quebra de integração**, mantendo a API estável.

---

## 🧩 Componentes Envolvidos

- Cliente externo (Postman, frontend, cURL, etc.)
- API de Negócio — **Java / Spring Boot**
- Serviço de Inferência — **Python / FastAPI**
- Modelo de Machine Learning (`joblib`)
- Contratos internos (`contracts/`)

---

## 🔁 Fluxo Passo a Passo

### 1️⃣ Requisição externa
O cliente envia uma requisição HTTP para a API Java:

```
POST /api/predict
```

Com o JSON conforme o **contrato externo da API**, definido em `api_contract.md`.

📌 Esse contrato é considerado **estável** e **independente do dataset** utilizado pelo modelo.

---

### 2️⃣ Validação na API Java
A API Java é responsável por:

- validar campos obrigatórios,
- validar tipos de dados,
- validar valores permitidos (enums),
- rejeitar payloads inválidos antes de qualquer chamada ao Python.

📌 Essa etapa garante que apenas dados **válidos e previsíveis** sigam no fluxo.

---

### 3️⃣ Encaminhamento do payload
Após validação:

- o payload **não sofre transformação semântica** na camada Java,
- os dados são repassados ao serviço Python **respeitando exatamente o contrato externo**.

📌 A API Java **não conhece o dataset** nem as **features internas do modelo**.

---

### 4️⃣ Chamada ao serviço FastAPI
A API Java realiza uma chamada HTTP para o serviço Python:

```
POST /predict
```

Esse endpoint é **interno**, utilizado exclusivamente para inferência.

---

### 5️⃣ Serviço de Inferência (FastAPI)
O serviço Python atua como **ponte explícita** entre a API e o modelo.

Nessa etapa, o FastAPI executa:

- leitura do **contrato interno ativo** (ex.: `contracts/bank_churn.yaml`),
- aplicação do **mapping** do payload externo → features internas do modelo,
- preenchimento de **defaults controlados**, quando aplicável,
- montagem do **DataFrame** com as features internas reais,
- carregamento do **modelo treinado** (`joblib`),
- execução da **inferência**.

📌 É neste ponto que ocorre a adaptação entre:
- o **contrato externo** (8 campos),
- e o **modelo interno** (6 features informativas + 2 defaults).

---

### 6️⃣ Resposta do FastAPI
O serviço retorna exclusivamente:

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
```

📌 O FastAPI **não expõe**:
- features internas,
- colunas do dataset,
- regras de mapping.

---

### 7️⃣ Tratamento de resposta no Java
A API Java:

- recebe a resposta do FastAPI,
- trata possíveis erros de comunicação,
- registra logs,
- aplica padronização de erro/resposta,
- devolve o resultado ao cliente.

---

### 8️⃣ Resposta ao cliente
O cliente recebe a resposta final da API Java, mantendo o contrato **estável e previsível**.

---

## 🧠 Responsabilidades Claras

| Camada | Responsabilidade |
|------|------------------|
| Cliente | Enviar payload conforme contrato |
| Java API | Validação, contrato, orquestração, erros |
| FastAPI | Adaptação de contrato, inferência |
| Contratos internos | Governar mapping e defaults |
| Modelo ML | Cálculo da previsão |

---

## ⚠️ Tratamento de Erros

### Possíveis falhas
- payload inválido (tratado no Java),
- valores fora do domínio permitido,
- indisponibilidade do FastAPI,
- erro interno de inferência.

### Estratégia
- Java retorna mensagens claras ao cliente,
- FastAPI retorna erros técnicos controlados,
- logs mantêm rastreabilidade sem expor detalhes sensíveis.

---

## 🚀 Extensões Futuras

Esse fluxo permite evoluções como:

- versionamento de contrato (`/predict/v2`),
- múltiplos contratos internos por dataset,
- batch prediction,
- fallback de modelo,
- persistência em banco,
- exportação para ONNX.

Sem alteração do fluxo principal.

---

## 📌 Conclusão

O fluxo de integração do **ChurnInsight** foi projetado para:

- manter a API estável,
- permitir troca de dataset e modelo,
- separar responsabilidades com clareza,
- garantir previsibilidade para o *Demo Day*.

A adaptação entre domínio externo e modelo interno é **explícita, documentada e governada por contrato**, evitando acoplamentos e decisões implícitas.
