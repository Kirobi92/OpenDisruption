FROM python:3.12-slim

LABEL maintainer="keycodi" \
      zone="WORKSPACE" \
      agent="opencode" \
      phase="2"

WORKDIR /app

# Nur stdlib + redis-py als Runtime-Abhängigkeit
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Agenten-Code
COPY agents/ ./agents/
COPY kidi/ ./kidi/

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Headless-Aufruf: docker run kirobi-agent-opencode python3 -m agents.opencode.cli
CMD ["python3", "-c", "from agents.opencode.agent import OpenCodeAgent; print('opencode-agent ready')"]
