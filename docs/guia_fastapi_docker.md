# 🚀 Como subir o serviço FastAPI (Python) usando Docker

Este guia é para qualquer pessoa do time (principalmente dev Java) conseguir **rodar o serviço de inferência Python** de forma rápida, sem precisar instalar Python, venv, notebook ou dependências de Data Science.

Ao final, o serviço estará disponível em:

- http://localhost:8001  
- Docs interativas (Swagger): http://localhost:8001/docs

---

## ✅ Pré-requisitos

Antes de começar, confirme:

1. **Docker Desktop instalado e rodando**
   - No Windows, abra o **Docker Desktop**
   - Espere ficar com status: **Running**

2. **Git instalado** (ou baixar o zip do repositório)

---

## 📥 1) Obter o repositório

### Opção A — Clonar com Git

No terminal (PowerShell / CMD):

```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>
```

### Opção B — Baixar como ZIP

- Baixe o repositório como `.zip`
- Extraia o conteúdo
- Abra o terminal na pasta extraída

---

## 📌 2) Verificar se a estrutura está correta

Você precisa estar na **raiz do projeto** (pasta onde existe o `Dockerfile`).

Estrutura mínima esperada:

```
/
├── Dockerfile
├── requirements.txt
├── src/
│   └── api_python/
│       └── main.py
└── artifacts/
    └── churn_model.joblib
```

⚠️ Se você rodar o build fora da raiz, o Docker não encontrará os arquivos.

---

## 🧱 3) Build da imagem Docker

Na raiz do projeto, execute:

```bash
docker build -t churninsight-api .
```

Esse comando:

- constrói a imagem do serviço FastAPI
- instala as dependências
- copia o código e o modelo para o container

---

## ▶️ 4) Rodar o container

```bash
docker run --rm -p 8001:8001 churninsight-api
```

O que acontece:

- o serviço sobe dentro do container
- a porta 8001 fica disponível no seu computador

⚠️ Mantenha esse terminal aberto.  
Para parar o serviço: **CTRL + C**.

---

## 🧪 5) Teste rápido (sem Postman)

### Health check

Abra no navegador:

```
http://localhost:8001/health
```

Ou via terminal:

```bash
curl http://localhost:8001/health
```

Se retornar um JSON de status OK, o serviço está funcionando.

---

## 📚 6) Documentação interativa (Swagger)

Com o serviço rodando:

```
http://localhost:8001/docs
```

Você pode:

- visualizar o contrato
- testar requisições
- ver exemplos de resposta

---

## 🧩 7) Endpoints disponíveis

- **GET /health** → status do serviço  
- **POST /predict** → previsão de churn

---

## 🛑 Problemas comuns

### ❌ Dockerfile not found
Você não está na raiz do projeto.

```bash
cd <pasta_do_projeto>
```

### ❌ requirements.txt not found
Confirme se o arquivo existe na raiz.

### ❌ port is already allocated
A porta 8001 já está em uso.

Use outra porta:

```bash
docker run --rm -p 8002:8001 churninsight-api
```

Acesse:
```
http://localhost:8002
```

---

## ✅ Pronto

O serviço Python está rodando e pronto para ser consumido pela **API Java via HTTP**.
