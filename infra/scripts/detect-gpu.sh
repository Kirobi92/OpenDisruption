#!/bin/bash
# =============================================================================
# Kirobi GPU Detection & Optimization Script
# Detects NVIDIA GPU and optimizes configuration for voice processing
# =============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Kirobi GPU Detection & Optimization                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Pop!_OS
echo "→ Checking system..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "  OS: $NAME $VERSION"
    if [[ "$NAME" == *"Pop!_OS"* ]]; then
        echo -e "  ${GREEN}✓${NC} Running on Pop!_OS"
    fi
fi

# Check for NVIDIA GPU
echo ""
echo "→ Detecting NVIDIA GPU..."

if ! command -v nvidia-smi &> /dev/null; then
    echo -e "  ${RED}✗${NC} nvidia-smi not found"
    echo -e "  ${YELLOW}⚠${NC} Please install NVIDIA drivers:"
    echo "     sudo apt install system76-cuda-latest system76-cudnn-11.8"
    exit 1
fi

# Get GPU info
GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo "")

if [ -z "$GPU_INFO" ]; then
    echo -e "  ${RED}✗${NC} No NVIDIA GPU detected"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} NVIDIA GPU detected:"
echo "$GPU_INFO" | while IFS=, read -r name memory driver; do
    echo "    GPU: $name"
    echo "    Memory: $memory"
    echo "    Driver: $driver"
done

# Check CUDA version
echo ""
echo "→ Checking CUDA..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9\.]*\).*/\1/p')
    echo -e "  ${GREEN}✓${NC} CUDA Version: $CUDA_VERSION"
else
    echo -e "  ${YELLOW}⚠${NC} CUDA compiler not found (not required for runtime)"
fi

# Check Docker NVIDIA runtime
echo ""
echo "→ Checking Docker NVIDIA runtime..."
if docker info 2>/dev/null | grep -q nvidia; then
    echo -e "  ${GREEN}✓${NC} NVIDIA Container Runtime detected"
else
    echo -e "  ${YELLOW}⚠${NC} NVIDIA Container Runtime not detected"
    echo "  Installing nvidia-container-toolkit..."

    # Install nvidia-container-toolkit
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker

    echo -e "  ${GREEN}✓${NC} NVIDIA Container Runtime installed"
fi

# Test GPU in Docker
echo ""
echo "→ Testing GPU access in Docker..."
if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} GPU accessible from Docker containers"
else
    echo -e "  ${RED}✗${NC} GPU not accessible from Docker"
    echo "  Please restart Docker: sudo systemctl restart docker"
    exit 1
fi

# Optimize .env for GPU
echo ""
echo "→ Optimizing .env configuration for GPU..."

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "  ${YELLOW}⚠${NC} .env not found, creating from .env.example..."
    cp .env.example "$ENV_FILE"
fi

# Set optimal GPU settings
grep -q "^WHISPER_DEVICE=" "$ENV_FILE" || echo "WHISPER_DEVICE=cuda" >> "$ENV_FILE"
sed -i 's/^WHISPER_DEVICE=.*/WHISPER_DEVICE=cuda/' "$ENV_FILE"

grep -q "^WHISPER_COMPUTE_TYPE=" "$ENV_FILE" || echo "WHISPER_COMPUTE_TYPE=float16" >> "$ENV_FILE"
sed -i 's/^WHISPER_COMPUTE_TYPE=.*/WHISPER_COMPUTE_TYPE=float16/' "$ENV_FILE"

grep -q "^WHISPER_MODEL=" "$ENV_FILE" || echo "WHISPER_MODEL=large-v3" >> "$ENV_FILE"

echo -e "  ${GREEN}✓${NC} .env configured for CUDA acceleration"
echo "    WHISPER_DEVICE=cuda"
echo "    WHISPER_COMPUTE_TYPE=float16"

# Check available GPU memory and recommend models
echo ""
echo "→ Model recommendations based on GPU memory:"

GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
GPU_MEMORY_GB=$((GPU_MEMORY / 1024))

echo "  Available GPU Memory: ${GPU_MEMORY_GB}GB"
echo ""

if [ $GPU_MEMORY_GB -ge 24 ]; then
    echo -e "  ${GREEN}Excellent!${NC} Your GPU can handle all models:"
    echo "    - Whisper large-v3 (recommended)"
    echo "    - llama3.1:70b for supervisor"
    echo "    - Multiple models simultaneously"
elif [ $GPU_MEMORY_GB -ge 16 ]; then
    echo -e "  ${GREEN}Great!${NC} Recommended configuration:"
    echo "    - Whisper large-v3"
    echo "    - llama3.1:32b or llama3.1:8b for supervisor"
elif [ $GPU_MEMORY_GB -ge 8 ]; then
    echo -e "  ${YELLOW}Good${NC} - Consider these optimizations:"
    echo "    - Whisper medium or large-v3 with int8 quantization"
    echo "    - llama3.1:8b for supervisor"
    echo "    - Run one model at a time"

    # Update to int8 for lower memory
    sed -i 's/^WHISPER_COMPUTE_TYPE=.*/WHISPER_COMPUTE_TYPE=int8/' "$ENV_FILE"
    echo "  Updated WHISPER_COMPUTE_TYPE to int8 for better memory efficiency"
else
    echo -e "  ${YELLOW}Limited GPU memory${NC} - Use CPU mode or smaller models:"
    echo "    - Consider WHISPER_DEVICE=cpu"
    echo "    - Whisper base or small model"
fi

# Performance tips
echo ""
echo "→ Performance optimization tips:"
echo "  1. Close other GPU-intensive applications"
echo "  2. Monitor GPU usage: watch -n 1 nvidia-smi"
echo "  3. Check Docker GPU allocation: docker stats"
echo "  4. For best voice latency, use Whisper turbo or large-v3"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  GPU Detection Complete - System Ready for Voice AI        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. make up          # Start all services"
echo "  2. make voice-test  # Test voice interface"
echo "  3. make start-interview # Begin family interview"
echo ""
