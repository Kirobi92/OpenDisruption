FROM python:3.12-slim

LABEL maintainer="keycodi" \
      zone="WORKSPACE" \
      agent="obsidian" \
      phase="2"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY kidi/ ./kidi/
# Vault wird als Volume gemountet — nicht in das Image kopiert
# docker run -v ./obsidian:/vault kirobi-agent-obsidian

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    KIROBI_VAULT_PATH=/vault

CMD ["python3", "-c", "from agents.obsidian.agent import ObsidianAgent; print('obsidian-agent ready')"]
