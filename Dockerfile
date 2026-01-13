# ============================================================
# ChurnInsight — FastAPI (Inferência) — Dockerfile
# ============================================================
FROM python:3.10-slim

# Evita arquivos .pyc e ativa logs imediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# ------------------------------------------------------------
# Dependências do sistema (necessárias para healthcheck com curl)
# ------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Dependências Python (cache-friendly)
# ------------------------------------------------------------
COPY requirements.txt ./

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Código + artefatos
# ------------------------------------------------------------
COPY src/ ./src/
COPY artifacts/ ./artifacts/
COPY contracts/ ./contracts/

# Porta da API
EXPOSE 8001

# Start
CMD ["uvicorn", "src.api_python.main:app", "--host", "0.0.0.0", "--port", "8001"]
