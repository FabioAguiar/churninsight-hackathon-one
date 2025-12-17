# 🧭 Boas Práticas de Git — ChurnInsight (Java x Data Science)

Este guia existe para evitar *bagunça no repositório* e *conflitos desnecessários* durante o Hackathon ONE + No Country 2025.

> ✅ Regra de ouro: **cada pessoa mexe apenas no seu “território”**  
> ❌ Evite `git add .` — esse é o maior causador de problemas.

---

## 📌 Estrutura e “territórios”

### ☕ Time Java (Spring Boot)
- Trabalha em:
  - `backend_java/`
- Evitar alterar:
  - `src/`
  - `notebooks/`
  - `data/`
  - `artifacts/`
  *(a menos que combinado)*

---

### 📊 Time Data Science (Notebooks)
- Trabalha exclusivamente em:
  ```text
  notebooks/individual/<seu_nome>/
  ```
- Não alterar notebooks de outros integrantes
- Core (`src/`) só com alinhamento prévio

---

### 🔧 Integração / Infra (FastAPI, Docker, Docs)
- `src/api_python/`
- `docker/`
- `docker-compose.yml`
- `artifacts/`
- `docs/`

⚠️ Alterações nessas pastas impactam a integração e devem ser combinadas.

---

## 🔐 Fluxo simples de trabalho (SEM branches)

### 1️⃣ Sempre atualizar antes de começar
```bash
git pull
```
Nunca comece a trabalhar sem dar `git pull`.

---

### 2️⃣ Trabalhe apenas no seu território
Antes de commitar, confira:
```bash
git status
```

---

### 3️⃣ Adicione SOMENTE o que você alterou

#### Java
```bash
git add backend_java/src/main/java/...
git add backend_java/pom.xml
git commit -m "feat: cria endpoint /api/predict"
```

#### Data Science
```bash
git add notebooks/individual/<seu_nome>/
git commit -m "docs: adiciona EDA inicial"
```

---

### 4️⃣ Envie suas alterações
```bash
git push
```

Se der erro de conflito:
- não force
- chame alguém para ajudar

---

## ❌ O que NÃO fazer (muito importante)

### 🚫 Não use `git add .`
Isso pode subir:
- arquivos locais
- caches
- dados grandes
- arquivos de outros colegas

✅ Sempre adicione pastas ou arquivos específicos.

---

### 🚫 Não altere pastas de outros integrantes
Cada diretório em:
```text
notebooks/individual/
```
tem dono.

---

### 🚫 Não altere o contrato sem alinhamento
- `docs/api_contract.md` é estável
- Mudanças só com decisão do grupo

---

## 📁 Manter pastas vazias no Git
Para manter estrutura de diretórios, use:
```bash
touch notebooks/individual/<seu_nome>/.gitkeep
```

---

## 🧠 Boas práticas gerais
- Commits pequenos
- Mensagens claras
- Sempre rodar `git status` antes de commitar
- Se tiver dúvida → pergunte antes de subir
