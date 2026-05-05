# Kirobi Supervisor Service
FROM python:3.11-slim

# Prevent interactive prompts
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Mount points for repository
VOLUME ["/kirobi-core", "/experiences", "/canon", "/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import asyncio; asyncio.run(__import__('supervisor').health_check())" || exit 1

# Run supervisor
CMD ["python3", "supervisor.py"]
