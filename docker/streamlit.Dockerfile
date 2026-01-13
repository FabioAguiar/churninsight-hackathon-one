# ============================================================
# ChurnInsight — Streamlit Frontend
# ============================================================

FROM python:3.11-slim

# Evita arquivos .pyc e melhora logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# ------------------------------------------------------------
# Dependências do frontend
# ------------------------------------------------------------
COPY frontend_streamlit/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Código do frontend
# ------------------------------------------------------------
COPY frontend_streamlit/ ./frontend_streamlit/

# ------------------------------------------------------------
# Exposição e inicialização
# ------------------------------------------------------------
EXPOSE 8501

CMD ["streamlit", "run", "frontend_streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
