FROM python:3.11-slim

# Metadaten
LABEL maintainer="kirobi-coder" \
      service="image-generation" \
      zone="WORKSPACE"

# Non-root user anlegen
RUN groupadd --gid 1001 kirobi \
 && useradd --uid 1001 --gid kirobi --shell /bin/bash --create-home kirobi

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY main.py .

# Datenpfad anlegen und Rechte setzen
RUN mkdir -p /data/images && chown -R kirobi:kirobi /data/images /app

USER kirobi

EXPOSE 8011

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
