FROM python:3.11-slim

# Metadaten
LABEL maintainer="kirobi-coder" \
      service="video-generation" \
      zone="WORKSPACE"

# Non-root user anlegen
RUN groupadd --gid 1001 kirobi \
 && useradd --uid 1001 --gid kirobi --shell /bin/bash --create-home kirobi

WORKDIR /app

# Abhängigkeiten installieren
COPY services/video-generation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY services/video-generation/main.py .
COPY kirobi_core /app/kirobi_core

# Datenpfad anlegen und Rechte setzen
RUN mkdir -p /data/videos && chown -R kirobi:kirobi /data/videos /app

USER kirobi

EXPOSE 8014

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8014/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8014"]
