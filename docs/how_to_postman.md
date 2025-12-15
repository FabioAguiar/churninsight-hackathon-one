# 📮 Como Usar o Postman — ChurnInsight

Este documento explica passo a passo como utilizar o Postman para testar a API de previsão de churn do projeto ChurnInsight.

Ele foi escrito pensando em pessoas iniciantes, então não se preocupe se você nunca usou o Postman antes.

🤔 O que é o Postman?

O Postman é uma ferramenta que permite enviar requisições HTTP para uma API e visualizar as respostas de forma simples e visual.

Com ele, conseguimos:

testar endpoints sem precisar criar uma interface gráfica;
simular requisições de sistemas externos;
validar se a API está funcionando corretamente;
visualizar erros, respostas e tempos de resposta.

No nosso projeto, o Postman é usado para:

✅ Testar a API de previsão de churn antes de integrá-la ao back-end Java.

🧱 Pré-requisitos

Antes de usar o Postman, verifique se:

o serviço FastAPI está rodando localmente;
você consegue acessar:
http://localhost:8001/docs

🛠️ Instalando o Postman

Acesse:
https://www.postman.com/downloads/

Baixe a versão adequada para seu sistema operacional.

🧭 Criando uma nova requisição

Abra o Postman
Clique em “New”
Escolha HTTP Request

🔗 Configurando a requisição

Método: POST  
URL: http://localhost:8001/predict  

Headers:
Content-Type: application/json

Body (raw / JSON):

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

Resposta esperada:

{
  "previsao": "Vai cancelar",
  "probabilidade": 0.52
}

✅ Conclusão

O Postman é a forma mais simples de validar a API e facilitar a integração entre os times.
