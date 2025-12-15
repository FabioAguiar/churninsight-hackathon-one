# Imagem base enxuta com Python
FROM python:3.11-slim

# Evita arquivos .pyc e ativa logs imediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia dependências primeiro (melhora cache)
COPY src/api_python/requirements.txt ./requirements.txt

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da FastAPI + core necessário
COPY src/ ./src/
COPY artifacts/ ./artifacts/

# Expõe a porta do serviço
EXPOSE 8001

# Comando de inicialização
CMD ["uvicorn", "src.api_python.main:app", "--host", "0.0.0.0", "--port", "8001"]
