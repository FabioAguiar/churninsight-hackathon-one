# 📄 Contrato de Integração — ChurnInsight

Este documento descreve o **contrato oficial de integração** entre:

- **API Java (Spring Boot)**
- **Serviço de Previsão Python (FastAPI)**

Ele representa a **interface pública e estável** do projeto **ChurnInsight**.

---

## 📌 Contexto Geral

O projeto **ChurnInsight** foi inicialmente concebido utilizando um dataset de churn do domínio de **telecomunicações (Telco)**.

Durante a execução do **Hackathon ONE**, a organização do evento publicou um aviso recomendando **não utilizar o dataset TelecomX** como base principal, por se tratar de um dataset pequeno, já tratado e com baixo potencial de diferenciação entre projetos.

Diante desse contexto, a equipe decidiu **substituir o dataset base por um dataset de churn bancário**, mais desafiador do ponto de vista de **engenharia de dados** e **modelagem**, **sem quebrar a integração existente entre os serviços**.

Essa decisão impacta **exclusivamente a implementação interna do modelo**, não a interface pública da API.

---

## 🧭 Princípio de Arquitetura Adotado

- O **contrato da API** representa uma **interface estável do MVP**
- O **dataset** e o **modelo** são considerados **detalhes de implementação interna**
- A adaptação entre a **interface externa** e as **features internas do modelo** é responsabilidade do **serviço Python (FastAPI)**
- Essa adaptação é governada por **contratos internos** localizados no diretório `contracts/`

Essa abordagem permite:

- troca de dataset **sem quebrar o backend Java**
- desenvolvimento **paralelo entre equipes**
- **estabilidade** para demonstração no *Demo Day*

---

## 🔌 Endpoint

**POST** `/predict`

---

## 📥 Entrada (JSON)

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

### 📋 Descrição dos Campos

| Campo | Tipo | Descrição |
|------|------|-----------|
| tenure | int | Tempo de relacionamento do cliente (em meses) |
| contract | string | Tipo de contrato |
| internet_service | string | Tipo de serviço contratado |
| online_security | string | Indicador de segurança online |
| tech_support | string | Indicador de suporte técnico |
| monthly_charges | float | Valor financeiro associado ao cliente |
| paperless_billing | string | Indicador de faturamento digital |
| payment_method | string | Método de pagamento |

---

## ⚠️ Observação Importante sobre o Dataset Atual

Com a adoção do **dataset bancário**, nem todos os campos acima possuem **equivalência semântica direta** no novo domínio.

Por isso:

- **6 campos** do contrato alimentam o modelo com **dados reais e variáveis**, derivados do dataset bancário
- **2 campos** (`internet_service` e `payment_method`) são mantidos como **defaults controlados**, exclusivamente para preservar:
  - compatibilidade do contrato
  - estabilidade da integração
  - previsibilidade da API

Esses campos continuam fazendo parte da **interface pública**, mas **não influenciam o modelo preditivo atual**.

Essa decisão é:

- consciente
- documentada
- adequada ao escopo de um **MVP de hackathon**

---

### 📢 Contexto oficial da troca de dataset (comunicado da organização)

A troca do dataset **TelecomX (Telco)** ocorreu **em resposta direta a uma mensagem oficial publicada pela organização do Hackathon ONE + No Country 2025 no Discord**.

Nessa comunicação, foi esclarecido que, embora o uso do dataset TelecomX **não fosse proibido**, ele **não era recomendado como dataset principal**, por apresentar:

- tamanho reduzido para o escopo do hackathon
- dados já amplamente tratados
- baixo desafio de preparação e exploração
- pouco potencial de diferenciação entre projetos

Essa orientação motivou a equipe a **buscar um dataset alternativo**, culminando na adoção do **dataset de churn bancário**, sem quebra do contrato externo da API.

![Aviso oficial sobre o uso do dataset TelecomX no Hackathon](docs/images/aviso_telecomx_hackathon.png)

---

## 📤 Saída (JSON)

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
```

### 📋 Descrição dos Campos

| Campo | Tipo | Descrição |
|------|------|-----------|
| previsao | string | Resultado da previsão de churn |
| probabilidade | float | Probabilidade associada à previsão |

---

## 🔒 Garantias do Contrato

- Este contrato deve ser respeitado **integralmente** pela **API Java** e pelo **serviço Python**
- A troca de dataset **não implica alteração** deste payload
- Ajustes de mapping, feature engineering ou defaults são tratados **internamente**, via contratos no diretório `contracts/`
- Evoluções futuras podem:
  - versionar este contrato (`/predict/v2`)
  - ou introduzir contratos alternativos mais genéricos  
  **sem quebrar compatibilidade** com esta versão

---

## 📚 Referências

- `docs/integration_flow.md`
- `contracts/bank_churn.yaml`
- Aviso da organização (*Discord — Hackathon ONE + No Country 2025*)
