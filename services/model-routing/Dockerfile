FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic python-dotenv
COPY main.py .
RUN useradd -m -u 1000 kirobi && chown -R kirobi:kirobi /app
USER kirobi
EXPOSE 8009
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1
CMD ["python", "main.py"]
