FROM python:3.12-slim

LABEL maintainer="keycodi" \
      zone="WORKSPACE" \
      agent="hermes-reasoner" \
      phase="2"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY kidi/ ./kidi/

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

CMD ["python3", "-c", "from agents.hermes.agent import HermesReasonerAgent; print('hermes-reasoner-agent ready')"]
