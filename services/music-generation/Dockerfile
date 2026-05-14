FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

LABEL maintainer="kirobi-coder"
LABEL zone="WORKSPACE"
LABEL service="music-generation"
LABEL port="8013"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/data/hf-cache
ENV TORCH_HOME=/data/torch-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3-dev \
    build-essential gcc libpq-dev pkg-config \
    ffmpeg libsndfile1 \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/music-generation/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
      torch==2.5.0+cu121 \
      torchaudio==2.5.0+cu121 \
      --index-url https://download.pytorch.org/whl/cu121 \
 && pip install --no-cache-dir -r requirements.txt

COPY services/music-generation/main.py .
COPY kirobi_core /app/kirobi_core

RUN mkdir -p /data/audio /data/hf-cache /data/torch-cache

RUN useradd -m -u 1000 kirobi && chown -R kirobi:kirobi /app /data
USER kirobi

EXPOSE 8013

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8013/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013", "--workers", "1"]
