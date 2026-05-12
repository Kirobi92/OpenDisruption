FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/nutzi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/nutzi/app/ ./app/
COPY services/nutzi/data/ ./data/

ENV PYTHONPATH=/app
ENV OLLAMA_URL=http://ollama:11434
ENV OLLAMA_MODEL=llama3.1:8b

EXPOSE 8015

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD curl -f http://localhost:8015/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8015"]
