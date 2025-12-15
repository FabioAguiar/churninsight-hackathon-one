# 🔄 Integration Flow — ChurnInsight

Este documento descreve **o fluxo de integração completo** entre as camadas do projeto **ChurnInsight**, desde a requisição externa até a geração da previsão pelo modelo de Machine Learning.

O objetivo é deixar claro **como os componentes se comunicam**, **quem é responsável por cada etapa** e **onde ocorrem validações e decisões técnicas**.

---

## 🎯 Visão Geral do Fluxo

O ChurnInsight segue um modelo de **arquitetura desacoplada**, onde:

- o **Java (Spring Boot)** atua como API de negócio,
- o **Python (FastAPI)** atua como serviço de inferência,
- o **modelo de ML** permanece isolado e protegido.

Esse desenho reduz acoplamento e facilita manutenção.

---

## 🧩 Componentes Envolvidos

1. Cliente externo (Postman, frontend, cURL, etc.)
2. API de Negócio — Java / Spring Boot
3. Serviço de Inferência — Python / FastAPI
4. Modelo de Machine Learning (joblib)

---

## 🔁 Fluxo Passo a Passo

### 1️⃣ Requisição externa

O cliente envia uma requisição HTTP para a API Java:

```
POST /api/predict
```

Com o JSON conforme o contrato definido.

---

### 2️⃣ Validação na API Java

A API Java é responsável por:

- validar campos obrigatórios,
- validar tipos e valores,
- validar enums (valores permitidos),
- rejeitar dados inválidos antes de chamar o Python.

📌 Essa etapa garante que o modelo **só receba dados limpos**.

---

### 3️⃣ Mapeamento e preparação

Após validação:

- os campos recebidos em `snake_case` são mapeados para o padrão interno do Java,
- os dados são organizados no formato esperado pelo serviço Python.

---

### 4️⃣ Chamada ao serviço FastAPI

A API Java realiza uma chamada HTTP para o serviço Python:

```
POST /predict
```

Esse serviço é interno e não exposto ao usuário final.

---

### 5️⃣ Serviço de Inferência (FastAPI)

O serviço Python executa:

- carregamento do modelo treinado,
- aplicação do preprocessamento oficial,
- inferência do modelo,
- cálculo da probabilidade.

O serviço **não contém regras de negócio**.

---

### 6️⃣ Resposta do FastAPI

O serviço retorna:

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
```

---

### 7️⃣ Tratamento de resposta no Java

A API Java:

- recebe a resposta,
- registra logs,
- trata possíveis erros,
- formata a resposta final.

---

### 8️⃣ Resposta ao cliente

O cliente recebe a resposta final da API Java.

---

## 🧠 Responsabilidades Claras

| Camada | Responsabilidade |
|------|-----------------|
| Java API | Validação, contrato, logs, erros |
| FastAPI | Inferência e acesso ao modelo |
| Modelo ML | Cálculo da previsão |
| Cliente | Enviar dados válidos |

---

## ⚠️ Tratamento de Erros

### Possíveis falhas:
- JSON inválido
- campo obrigatório ausente
- valor fora do permitido
- FastAPI indisponível
- erro interno no modelo

### Estratégia:
- Java retorna mensagens claras
- FastAPI retorna erro técnico
- Logs registram contexto

---

## 🚀 Extensões Futuras

O fluxo permite evoluções como:

- batch prediction
- persistência em banco
- fallback de modelo
- integração ONNX

Sem alterar o fluxo principal.

---

## 📌 Conclusão

O fluxo de integração do ChurnInsight foi definido para garantir uma comunicação clara entre os componentes do sistema, mantendo responsabilidades bem delimitadas entre Data Science, Engenharia de Dados e Back-end.

Essa abordagem reduz acoplamento, facilita a evolução do projeto e permite que o time foque na entrega de um MVP funcional, confiável e alinhado às expectativas do hackathon.
