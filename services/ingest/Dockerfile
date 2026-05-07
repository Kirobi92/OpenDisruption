FROM python:3.11-slim

WORKDIR /app

# System dependencies: gcc for asyncpg, pdfplumber needs pdfminer which needs no extras
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ingest data directory is mounted at runtime; pre-create so the service
# can start without a volume mount in development.
RUN mkdir -p /data/ingest

# Non-root user
RUN useradd -m -u 1000 kirobi && chown -R kirobi:kirobi /app /data/ingest
USER kirobi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
