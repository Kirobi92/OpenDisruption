FROM python:3.11-slim

# Metadaten
LABEL maintainer="kirobi-coder" \
      service="media-processing" \
      zone="WORKSPACE"

# System-Abhängigkeiten für Pillow (libjpeg, libpng, libwebp)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libjpeg-dev \
        libpng-dev \
        libwebp-dev \
        libopus0 \
        libvorbis0a \
        libflac-dev \
 && rm -rf /var/lib/apt/lists/*

# Non-root user anlegen
RUN groupadd --gid 1001 kirobi \
 && useradd --uid 1001 --gid kirobi --shell /bin/bash --create-home kirobi

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY main.py .

RUN chown -R kirobi:kirobi /app

USER kirobi

EXPOSE 8012

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8012/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
