FROM python:3.11-slim

# Metadaten
LABEL maintainer="kirobi-coder"
LABEL zone="WORKSPACE"
LABEL service="music-generation"
LABEL port="8013"

# Systemabhängigkeiten (für asyncpg Build und WAV-Verarbeitung)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Abhängigkeiten zuerst (Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode
COPY main.py .

# Audio-Storage-Verzeichnis anlegen
RUN mkdir -p /data/audio

# Non-root User für Sicherheit
RUN useradd -m -u 1000 kirobi && chown -R kirobi:kirobi /app /data
USER kirobi

EXPOSE 8013

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8013/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013", "--workers", "1"]
