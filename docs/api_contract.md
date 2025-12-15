# 📄 Contrato de Integração — ChurnInsight

Este documento descreve o contrato oficial de integração entre:

- **API Java (Spring Boot)**  
- **Serviço de Previsão Python (FastAPI)**

---

## Endpoint

**POST** `/predict`

---

## Entrada (JSON)

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

### Descrição dos Campos

| Campo | Tipo | Descrição |
|------|-----|-----------|
| tenure | int | Tempo de contrato do cliente (meses) |
| contract | string | Tipo de contrato |
| internet_service | string | Tipo de serviço de internet |
| online_security | string | Possui segurança online |
| tech_support | string | Possui suporte técnico |
| monthly_charges | float | Valor mensal cobrado |
| paperless_billing | string | Fatura digital |
| payment_method | string | Forma de pagamento |

---

## Saída (JSON)

```json
{
  "previsao": "Vai cancelar",
  "probabilidade": 0.81
}
```

| Campo | Tipo | Descrição |
|------|-----|-----------|
| previsao | string | Resultado da previsão |
| probabilidade | float | Probabilidade associada à previsão |

---

## Observações

- Este contrato deve ser respeitado tanto pela API Java quanto pelo serviço Python.
- Novos campos podem ser adicionados futuramente sem quebrar compatibilidade, desde que opcionais.
