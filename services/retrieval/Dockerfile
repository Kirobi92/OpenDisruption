FROM python:3.11-slim

LABEL maintainer="kirobi-coder"
LABEL zone="WORKSPACE"
LABEL service="retrieval"

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Service-Code
COPY main.py .

# Nicht-root User
RUN useradd -m -u 1000 kirobi && chown -R kirobi:kirobi /app
USER kirobi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
