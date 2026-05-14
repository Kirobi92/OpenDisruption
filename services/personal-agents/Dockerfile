FROM python:3.11-slim

WORKDIR /app

COPY services/personal-agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/personal-agents/app/ ./app/

# Profile und Memory werden als Volumes gemountet (FAMILY_PRIVATE — nicht im Image!)
VOLUME ["/app/profiles"]
VOLUME ["/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner"]

EXPOSE 8017

ENV PYTHONUNBUFFERED=1
ENV BENUTZER_BASE=/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner
ENV PROFILES_DIR=/app/profiles

# Kein curl in slim — Python für Healthcheck verwenden
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=25s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8017/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8017"]
