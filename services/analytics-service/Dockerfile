FROM python:3.11-slim

# Non-root user for security
RUN groupadd --gid 1001 kirobi \
    && useradd --uid 1001 --gid kirobi --shell /bin/bash --create-home kirobi

WORKDIR /app

# Install dependencies as root, then hand off
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Switch to non-root user
USER kirobi

EXPOSE 8010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
