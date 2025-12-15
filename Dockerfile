FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY artifacts/ artifacts/

EXPOSE 8001

CMD ["uvicorn", "src.api_python.main:app", "--host", "0.0.0.0", "--port", "8001"]
