# ── Build-Stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Abhängigkeiten installieren (kein Cache im finalen Image)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime-Stage ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Sicherheits-Best-Practice: kein Root-User
RUN addgroup --system kirobi && adduser --system --ingroup kirobi kirobi

WORKDIR /app

# Installierte Pakete aus Build-Stage übernehmen
COPY --from=builder /install /usr/local

# Anwendungscode kopieren
COPY main.py .

# Nicht-Root-User aktivieren
USER kirobi

# Umgebungsvariablen mit sicheren Defaults
ENV OLLAMA_HOST=http://ollama:11434 \
    QDRANT_HOST=qdrant \
    QDRANT_PORT=6333 \
    EMBED_MODEL=nomic-embed-text \
    EMBED_DIM=768 \
    ALLOWED_ORIGINS=http://localhost:3000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
