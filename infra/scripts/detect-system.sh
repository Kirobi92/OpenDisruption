#!/usr/bin/env bash
# =============================================================================
# detect-system.sh — Hardware & environment detection for OpenDisruption
# =============================================================================
# Output:
#   default → human-readable summary
#   --json  → single JSON object on stdout (consumed by install.sh / agents)
#   --shell → eval-able KEY=value lines
# Flags: --quiet (suppress stderr), --json, --shell
# =============================================================================
set -Eeuo pipefail

OUTPUT="human"
QUIET=0
for a in "$@"; do
  case "$a" in
    --json)  OUTPUT="json" ;;
    --shell) OUTPUT="shell" ;;
    --quiet) QUIET=1 ;;
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'Unknown arg: %s\n' "$a" >&2; exit 1 ;;
  esac
done

log() { (( QUIET )) || printf '%s\n' "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# OS
KERNEL="$(uname -s)"; ARCH="$(uname -m)"
OS_NAME="unknown"; OS_VERSION="unknown"; OS_FAMILY="other"
case "$KERNEL" in
  Linux)
    OS_FAMILY="linux"
    if [[ -r /etc/os-release ]]; then
      # shellcheck disable=SC1091
      . /etc/os-release; OS_NAME="${ID:-linux}"; OS_VERSION="${VERSION_ID:-?}"
    fi ;;
  Darwin)  OS_FAMILY="darwin"; OS_NAME="macos"
    OS_VERSION="$(sw_vers -productVersion 2>/dev/null || echo unknown)" ;;
  MINGW*|MSYS*|CYGWIN*) OS_FAMILY="windows"; OS_NAME="windows"; OS_VERSION="$KERNEL" ;;
esac

# CPU / RAM
CPU_CORES="$( (nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null) || echo 1 )"
CPU_MODEL="unknown"
if [[ -r /proc/cpuinfo ]]; then
  CPU_MODEL="$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo | sed 's/^[[:space:]]*//')"
elif [[ "$OS_FAMILY" == "darwin" ]]; then
  CPU_MODEL="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo Apple)"
fi
RAM_GB=0
if [[ -r /proc/meminfo ]]; then
  RAM_GB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
elif [[ "$OS_FAMILY" == "darwin" ]]; then
  RAM_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1024 / 1024 / 1024 ))
fi

# GPU
GPU_VENDOR="none"; GPU_MODEL="n/a"; GPU_VRAM_GB=0; GPU_COUNT=0
if have nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then
  GPU_VENDOR="nvidia"
  GPU_MODEL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)"
  GPU_COUNT="$(nvidia-smi -L | wc -l | tr -d ' ')"
  GPU_VRAM_GB=$(( $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n1) / 1024 ))
elif have rocm-smi && rocm-smi --showproductname >/dev/null 2>&1; then
  GPU_VENDOR="amd"; GPU_MODEL="$(rocm-smi --showproductname 2>/dev/null | head -n1)"; GPU_COUNT=1
elif have lspci && lspci 2>/dev/null | grep -qi 'vga.*intel'; then
  GPU_VENDOR="intel"; GPU_MODEL="$(lspci 2>/dev/null | grep -i 'vga.*intel' | head -n1 | cut -d: -f3- | xargs)"; GPU_COUNT=1
elif [[ "$OS_FAMILY" == "darwin" && "$ARCH" == "arm64" ]]; then
  GPU_VENDOR="apple"; GPU_MODEL="Apple Silicon"; GPU_COUNT=1
fi

# Disk
HOME_DIR="${HOME:-/tmp}"
DISK_FREE_GB="$(df -Pk "$HOME_DIR" 2>/dev/null | awk 'NR==2 {print int($4/1024/1024)}' || echo 0)"

# Docker
DOCKER_VERSION="absent"; COMPOSE_VERSION="absent"; DOCKER_RUNNING="false"
if have docker; then
  DOCKER_VERSION="$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo unknown)"
  if docker info >/dev/null 2>&1; then DOCKER_RUNNING="true"; fi
  COMPOSE_VERSION="$(docker compose version --short 2>/dev/null || echo absent)"
fi

# Recommended profile
PROFILE="cpu"
case "$GPU_VENDOR" in nvidia) PROFILE="nvidia";; amd) PROFILE="amd";; esac
(( RAM_GB > 0 && RAM_GB < 8 )) && PROFILE="minimal"

# Agent env
AGENT_ENV="human"
[[ -n "${CURSOR_AGENT:-}" ]]                && AGENT_ENV="cursor"
[[ -n "${CLAUDE_CODE:-}${CLAUDECODE:-}" ]]  && AGENT_ENV="claude-code"
[[ -n "${COPILOT_AGENT_ID:-}" ]]            && AGENT_ENV="github-copilot"
[[ -n "${OPENAI_AGENT:-}" ]]                && AGENT_ENV="openai"
[[ "${TERM_PROGRAM:-}" == "vscode" ]]       && AGENT_ENV="vscode"
[[ -n "${CI:-}" ]]                          && AGENT_ENV="ci/${AGENT_ENV}"

case "$OUTPUT" in
  json)
    cat <<EOF
{"os":{"family":"$OS_FAMILY","name":"$OS_NAME","version":"$OS_VERSION","arch":"$ARCH"},"cpu":{"cores":$CPU_CORES,"model":"$CPU_MODEL"},"ram_gb":$RAM_GB,"gpu":{"vendor":"$GPU_VENDOR","model":"$GPU_MODEL","count":$GPU_COUNT,"vram_gb":$GPU_VRAM_GB},"disk_free_gb":$DISK_FREE_GB,"docker":{"version":"$DOCKER_VERSION","compose":"$COMPOSE_VERSION","running":$DOCKER_RUNNING},"recommended_profile":"$PROFILE","agent_env":"$AGENT_ENV"}
EOF
    ;;
  shell)
    cat <<EOF
OS_FAMILY="$OS_FAMILY"
OS_NAME="$OS_NAME"
OS_VERSION="$OS_VERSION"
ARCH="$ARCH"
CPU_CORES=$CPU_CORES
RAM_GB=$RAM_GB
GPU_VENDOR="$GPU_VENDOR"
GPU_MODEL="$GPU_MODEL"
GPU_VRAM_GB=$GPU_VRAM_GB
DISK_FREE_GB=$DISK_FREE_GB
DOCKER_VERSION="$DOCKER_VERSION"
COMPOSE_VERSION="$COMPOSE_VERSION"
DOCKER_RUNNING=$DOCKER_RUNNING
RECOMMENDED_PROFILE="$PROFILE"
AGENT_ENV="$AGENT_ENV"
EOF
    ;;
  *)
    cat <<EOF
OpenDisruption · system detection
─────────────────────────────────
  OS         : $OS_NAME $OS_VERSION ($OS_FAMILY/$ARCH)
  CPU        : $CPU_CORES cores · $CPU_MODEL
  RAM        : ${RAM_GB} GB
  GPU        : $GPU_VENDOR · $GPU_MODEL · ${GPU_VRAM_GB} GB VRAM · ×${GPU_COUNT}
  Disk free  : ${DISK_FREE_GB} GB at $HOME_DIR
  Docker     : $DOCKER_VERSION (compose: $COMPOSE_VERSION, running: $DOCKER_RUNNING)
  Agent env  : $AGENT_ENV
  → Recommended profile: $PROFILE
EOF
    ;;
esac
