FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

LABEL maintainer="kirobi-coder" \
      service="image-generation" \
      zone="WORKSPACE"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/data/hf-cache
ENV TORCH_HOME=/data/torch-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3-dev build-essential \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1001 kirobi \
 && useradd --uid 1001 --gid kirobi --shell /bin/bash --create-home kirobi

WORKDIR /app

COPY services/image-generation/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
      torch==2.5.0+cu121 \
      torchvision==0.20.0+cu121 \
      --index-url https://download.pytorch.org/whl/cu121 \
 && pip install --no-cache-dir -r requirements.txt

COPY services/image-generation/main.py .
COPY kirobi_core /app/kirobi_core

RUN mkdir -p /data/images /data/hf-cache /data/torch-cache \
 && chown -R kirobi:kirobi /data /app

USER kirobi

EXPOSE 8011

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
