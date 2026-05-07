#!/usr/bin/env bash
# =============================================================================
# OpenDisruption / Kirobi OS — One-Command Bootstrap Installer
# =============================================================================
# Repository : https://github.com/Kirobi92/OpenDisruption
# License    : See LICENSE.md
# Designed   : Agent-first. Idempotent. Safe-by-default.
#
# Quick usage (humans):
#     curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh | bash
#
# Quick usage (agents — fully unattended):
#     curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
#       | bash -s -- --auto --profile=auto --yes
#
# Flags:
#   --auto             non-interactive; pick safe defaults for every prompt
#   --yes              answer "yes" to every confirmation
#   --dry-run          print what would happen, change nothing
#   --verbose          print every command (set -x)
#   --quiet            suppress non-essential output
#   --profile=NAMES    compose profile(s), comma-separated for layering, e.g.
#                      auto | minimal | cpu | nvidia | amd | voice-full |
#                      production | development | "cpu,voice-full"
#   --target-dir=PATH  installation directory (default: $HOME/OpenDisruption)
#   --branch=NAME      git branch to clone (default: main)
#   --repo=URL         git repository URL (default: upstream OpenDisruption)
#   --no-clone         assume we are already inside the repo
#   --no-pull          do not pull docker images
#   --no-models        do not download Ollama models
#   --no-start         do not run `docker compose up`
#   --skip-checks      skip prerequisite verification (NOT recommended)
#   --uninstall        stop services and remove containers (data is preserved)
#   --version          print installer version and exit
#   --help             print this help
#
# Exit codes:
#   0  success
#   1  generic failure
#   2  missing prerequisite the user must install
#   3  unsupported platform
#   4  network failure
#   5  user aborted
#   6  validation / health check failed
# =============================================================================

set -Eeuo pipefail

# ----------------------------------------------------------------------------- #
#  Constants & metadata
# ----------------------------------------------------------------------------- #
readonly INSTALLER_VERSION="1.0.0"
readonly REPO_URL_DEFAULT="https://github.com/Kirobi92/OpenDisruption.git"
# shellcheck disable=SC2034  # exported for reference / extension scripts
readonly REPO_RAW_BASE="https://raw.githubusercontent.com/Kirobi92/OpenDisruption"
readonly MIN_DOCKER_VERSION="20.10"
readonly MIN_COMPOSE_VERSION="2.24"  # 2.24+ required for `!reset` directive used by voice-full
readonly MIN_BASH_MAJOR=4
readonly MIN_DISK_GB=20
readonly MIN_RAM_GB=8
readonly RECOMMENDED_RAM_GB=32

# ----------------------------------------------------------------------------- #
#  Defaults (overridable by flags / env)
# ----------------------------------------------------------------------------- #
AUTO=${AUTO:-0}
ASSUME_YES=${ASSUME_YES:-0}
DRY_RUN=${DRY_RUN:-0}
VERBOSE=${VERBOSE:-0}
QUIET=${QUIET:-0}
PROFILE=${PROFILE:-auto}
TARGET_DIR=${TARGET_DIR:-$HOME/OpenDisruption}
BRANCH=${BRANCH:-main}
DO_CLONE=1
DO_PULL=1
DO_MODELS=1
DO_START=1
SKIP_CHECKS=0
DO_UNINSTALL=0
REPO_URL=${REPO_URL:-$REPO_URL_DEFAULT}

# ----------------------------------------------------------------------------- #
#  Color & logging primitives (degrade gracefully when not a TTY)
# ----------------------------------------------------------------------------- #
if [[ -t 1 ]] && [[ "${NO_COLOR:-}" != "1" ]] && command -v tput >/dev/null 2>&1; then
  C_RESET=$(tput sgr0); C_BOLD=$(tput bold)
  C_RED=$(tput setaf 1); C_GREEN=$(tput setaf 2); C_YELLOW=$(tput setaf 3)
  C_BLUE=$(tput setaf 4); C_MAGENTA=$(tput setaf 5); C_CYAN=$(tput setaf 6)
  C_GREY=$(tput setaf 8 2>/dev/null || tput setaf 7)
else
  C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YELLOW=""
  C_BLUE=""; C_MAGENTA=""; C_CYAN=""; C_GREY=""
fi

LOG_FILE="${TMPDIR:-/tmp}/opendisruption-install-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"
: >"$LOG_FILE"

_log()    { printf '%s\n' "$*" >>"$LOG_FILE"; }
_emit()   { (( QUIET )) || printf '%b\n' "$*"; _log "$*"; }
say()     { _emit "${C_CYAN}▸${C_RESET} $*"; }
ok()      { _emit "${C_GREEN}✔${C_RESET} $*"; }
warn()    { _emit "${C_YELLOW}⚠${C_RESET} $*" >&2; }
err()     { _emit "${C_RED}✖${C_RESET} $*" >&2; }
hdr()     { _emit ""; _emit "${C_BOLD}${C_BLUE}── $* ──${C_RESET}"; }
debug()   { (( VERBOSE )) && _emit "${C_GREY}· $*${C_RESET}" || true; _log "DEBUG: $*"; }

banner() {
  (( QUIET )) && return 0
  cat <<EOF

${C_BOLD}${C_MAGENTA}╔══════════════════════════════════════════════════════════════╗
║   OpenDisruption / Kirobi OS — Bootstrap Installer v${INSTALLER_VERSION}     ║
║   Local-first · Agent-driven · Zone-based security           ║
╚══════════════════════════════════════════════════════════════╝${C_RESET}

EOF
}

usage() {
  # Embedded help text — works whether the script lives on disk (./install.sh)
  # or is being executed from stdin (curl … | bash), where $0 is "bash".
  cat <<'USAGE'
OpenDisruption / Kirobi OS — One-Command Bootstrap Installer

USAGE:
  bash install.sh [FLAGS]
  curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
    | bash -s -- [FLAGS]

FLAGS:
  --auto                Non-interactive; pick safe defaults for every prompt.
  --yes, -y             Answer "yes" to every confirmation.
  --dry-run             Print actions, change nothing.
  --verbose, -v         Echo every command (set -x).
  --quiet, -q           Suppress non-essential output.
  --profile=NAMES       Compose profile(s), comma-separated for layering.
                        Single:  auto | minimal | cpu | nvidia | amd |
                                 voice-full | production | development
                        Layered: e.g. "cpu,voice-full" or "nvidia,production".
                        "auto" picks one based on detected hardware.
  --target-dir=PATH     Installation directory (default: $HOME/OpenDisruption).
  --branch=NAME         Git branch to clone (default: main).
  --repo=URL            Git repository URL (default: upstream OpenDisruption).
  --no-clone            Assume we are already inside the repo.
  --no-pull             Do not pull docker images.
  --no-models           Do not download Ollama models.
  --no-start            Do not run `docker compose up`.
  --skip-checks         Skip prerequisite verification (NOT recommended).
  --uninstall           Stop services and remove containers (data preserved).
  --version             Print installer version and exit.
  --help, -h            Print this help.

EXIT CODES:
  0  success
  1  generic failure
  2  missing prerequisite the user must install
  3  unsupported platform
  4  network failure
  5  user aborted
  6  validation / health check failed
USAGE
}

# ----------------------------------------------------------------------------- #
#  Error handling
# ----------------------------------------------------------------------------- #
on_error() {
  local exit_code=$? line=${1:-?}
  err "Installer failed (exit ${exit_code}) at line ${line}."
  warn "Full log: ${LOG_FILE}"
  warn "Recovery: see AGENT-RECOVERY.md or run: bash $0 --help"
  exit "$exit_code"
}
trap 'on_error $LINENO' ERR

# ----------------------------------------------------------------------------- #
#  Helpers
# ----------------------------------------------------------------------------- #
run() {
  # Execute (or just print, in dry-run) a command. Logs always.
  _log "RUN: $*"
  if (( DRY_RUN )); then
    _emit "${C_GREY}[dry-run]${C_RESET} $*"
    return 0
  fi
  if (( VERBOSE )); then
    "$@" \
      > >(
        while IFS= read -r line || [[ -n "$line" ]]; do
          printf '%s\n' "$line"
          printf '%s\n' "$line" >>"$LOG_FILE"
        done
      ) \
      2> >(
        while IFS= read -r line || [[ -n "$line" ]]; do
          printf '%s\n' "$line" >&2
          printf '%s\n' "$line" >>"$LOG_FILE"
        done
      )
  else
    "$@" >>"$LOG_FILE" 2>&1
  fi
}

confirm() {
  local prompt="${1:-Proceed?}"
  if (( AUTO )) || (( ASSUME_YES )); then
    debug "auto-confirm: $prompt → yes"
    return 0
  fi
  if [[ ! -t 0 ]]; then
    warn "Non-interactive shell and no --auto/--yes — assuming NO for: $prompt"
    return 1
  fi
  local reply
  read -r -p "$(printf '%b' "${C_YELLOW}? ${prompt} [y/j/N] ${C_RESET}")" reply
  [[ "$reply" =~ ^[YyJj]$ ]]
}

ask() {
  # ask "Question" "default"
  local prompt="$1" default="${2:-}"
  if (( AUTO )) || [[ ! -t 0 ]]; then
    printf '%s\n' "$default"
    return 0
  fi
  local reply
  read -r -p "$(printf '%b' "${C_CYAN}? ${prompt}${default:+ [${default}]} ${C_RESET}")" reply
  printf '%s\n' "${reply:-$default}"
}

semver_ge() {
  # semver_ge "have" "want" — true iff have >= want
  printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# ----------------------------------------------------------------------------- #
#  Argument parsing
# ----------------------------------------------------------------------------- #
parse_args() {
  for arg in "$@"; do
    case "$arg" in
      --auto)            AUTO=1 ;;
      --yes|-y)          ASSUME_YES=1 ;;
      --dry-run)         DRY_RUN=1 ;;
      --verbose|-v)      VERBOSE=1 ;;
      --quiet|-q)        QUIET=1 ;;
      --no-clone)        DO_CLONE=0 ;;
      --no-pull)         DO_PULL=0 ;;
      --no-models)       DO_MODELS=0 ;;
      --no-start)        DO_START=0 ;;
      --skip-checks)     SKIP_CHECKS=1 ;;
      --uninstall)       DO_UNINSTALL=1 ;;
      --profile=*)       PROFILE="${arg#*=}" ;;
      --target-dir=*)    TARGET_DIR="${arg#*=}" ;;
      --branch=*)        BRANCH="${arg#*=}" ;;
      --repo=*)          REPO_URL="${arg#*=}" ;;
      --version)         printf 'OpenDisruption installer v%s\n' "$INSTALLER_VERSION"; exit 0 ;;
      --help|-h)         usage; exit 0 ;;
      *) err "Unknown argument: $arg"; usage; exit 1 ;;
    esac
  done

  (( VERBOSE )) && set -x || true
}

# ----------------------------------------------------------------------------- #
#  Detection
# ----------------------------------------------------------------------------- #
# When the helper scripts already exist on disk (i.e. the repo is checked out)
# we delegate to them so that there is exactly *one* implementation of the
# detection contract. Before the clone phase they are not yet available, so
# we keep an inline fallback.
detect_with_helper() {
  local helper="$TARGET_DIR/infra/scripts/detect-system.sh"
  [[ -x "$helper" ]] || return 1
  # shellcheck disable=SC1090
  eval "$("$helper" --shell --quiet 2>/dev/null)" || return 1
  OS_FAMILY="${OS_FAMILY:-unknown}"; OS_NAME="${OS_NAME:-unknown}"
  OS_VERSION="${OS_VERSION:-unknown}"; OS_ARCH="${ARCH:-unknown}"
  CPU_CORES="${CPU_CORES:-1}"; RAM_GB="${RAM_GB:-0}"
  GPU_VENDOR="${GPU_VENDOR:-none}"; GPU_MODEL="${GPU_MODEL:-n/a}"
  GPU_VRAM_GB="${GPU_VRAM_GB:-0}"; DISK_FREE_GB="${DISK_FREE_GB:-0}"
  debug "detection delegated to detect-system.sh"
  return 0
}

detect_os() {
  local installer_dir detect_script detect_json detect_fields

  installer_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  detect_script="$installer_dir/infra/scripts/detect-system.sh"

  OS_KERNEL="$(uname -s)"
  OS_ARCH="$(uname -m)"
  OS_NAME="unknown"; OS_VERSION="unknown"; OS_FAMILY="unknown"

  if [[ -x "$detect_script" ]]; then
    debug "Using shared system detection: $detect_script --json"
    if detect_json="$("$detect_script" --json 2>/dev/null)" && [[ -n "$detect_json" ]] && command -v python3 >/dev/null 2>&1; then
      if detect_fields="$(python3 -c '
import json, platform, sys
try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(1)
os_data = data.get("os", {})
values = [
    str(data.get("kernel", "") or platform.system() or "unknown"),
    str(data.get("arch", "") or os_data.get("arch", "")),
    str(data.get("name", "") or os_data.get("name", "")),
    str(data.get("version", "") or os_data.get("version", "")),
    str(data.get("family", "") or os_data.get("family", "")),
]
sys.stdout.write("\t".join(values))
' <<<"$detect_json" 2>/dev/null)"; then
        IFS=$'\t' read -r detected_kernel detected_arch detected_name detected_version detected_family <<<"$detect_fields"

        [[ -n "${detected_kernel:-}" ]] && OS_KERNEL="$detected_kernel"
        [[ -n "${detected_arch:-}" ]] && OS_ARCH="$detected_arch"
        [[ -n "${detected_name:-}" ]] && OS_NAME="$detected_name"
        [[ -n "${detected_version:-}" ]] && OS_VERSION="$detected_version"
        [[ -n "${detected_family:-}" ]] && OS_FAMILY="$detected_family"

        debug "OS: $OS_NAME $OS_VERSION ($OS_FAMILY/$OS_KERNEL/$OS_ARCH)"
        return
      fi
    fi
    warn "Shared system detection failed, falling back to built-in detection"
  fi

  case "$OS_KERNEL" in
    Linux)
      OS_FAMILY="linux"
      if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        OS_NAME="${ID:-linux}"
        OS_VERSION="${VERSION_ID:-?}"
      fi
      ;;
    Darwin)
      OS_FAMILY="darwin"; OS_NAME="macos"
      OS_VERSION="$(sw_vers -productVersion 2>/dev/null || echo unknown)"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      OS_FAMILY="windows"; OS_NAME="windows"; OS_VERSION="$OS_KERNEL"
      ;;
    *) OS_FAMILY="other" ;;
  esac
  debug "OS: $OS_NAME $OS_VERSION ($OS_FAMILY/$OS_KERNEL/$OS_ARCH)"
}

detect_hardware() {
  # If the helper is on disk (after clone) it is the source of truth.
  if detect_with_helper; then return; fi

  CPU_CORES="$( (nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null) || echo 1 )"
  if [[ "$OS_FAMILY" == "linux" ]] && [[ -r /proc/meminfo ]]; then
    RAM_KB="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
    RAM_GB=$(( RAM_KB / 1024 / 1024 ))
  elif [[ "$OS_FAMILY" == "darwin" ]]; then
    RAM_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1024 / 1024 / 1024 ))
  else
    RAM_GB=0
  fi

  GPU_VENDOR="none"; GPU_MODEL="n/a"; GPU_VRAM_GB=0
  if have_cmd nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then
    GPU_VENDOR="nvidia"
    GPU_MODEL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || echo NVIDIA)"
    GPU_VRAM_MB="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n1 || echo 0)"
    GPU_VRAM_GB=$(( GPU_VRAM_MB / 1024 ))
  elif have_cmd rocm-smi && rocm-smi --showproductname >/dev/null 2>&1; then
    GPU_VENDOR="amd"; GPU_MODEL="$(rocm-smi --showproductname 2>/dev/null | head -n1 || echo AMD)"
  elif [[ "$OS_FAMILY" == "linux" ]] && have_cmd lspci && lspci 2>/dev/null | grep -qi 'vga.*intel'; then
    GPU_VENDOR="intel"; GPU_MODEL="$(lspci 2>/dev/null | grep -i 'vga.*intel' | head -n1 | cut -d: -f3- | xargs || echo Intel)"
  elif [[ "$OS_FAMILY" == "darwin" ]] && [[ "$OS_ARCH" == "arm64" ]]; then
    GPU_VENDOR="apple"; GPU_MODEL="Apple Silicon"
  fi

  DISK_FREE_GB="$(df -Pk "$(dirname "$TARGET_DIR")" 2>/dev/null | awk 'NR==2 {print int($4/1024/1024)}' || echo 0)"
  debug "Hardware: ${CPU_CORES} cores · ${RAM_GB} GB RAM · GPU=${GPU_VENDOR}(${GPU_MODEL}, ${GPU_VRAM_GB} GB) · disk=${DISK_FREE_GB} GB free"
}

detect_agent_env() {
  # Prefer the standalone helper (single source of truth) when available.
  local helper="$TARGET_DIR/infra/scripts/agent-detect.sh"
  if [[ -x "$helper" ]]; then
    AGENT_ENV="$("$helper" 2>/dev/null || echo human)"
  else
    AGENT_ENV="human"
    [[ -n "${CURSOR_AGENT:-}" ]]                        && AGENT_ENV="cursor"
    [[ -n "${CLAUDE_CODE:-}" || -n "${CLAUDECODE:-}" ]] && AGENT_ENV="claude-code"
    [[ -n "${ANTHROPIC_AGENT:-}" ]]                     && AGENT_ENV="claude"
    [[ -n "${COPILOT_AGENT_ID:-}" ]]                    && AGENT_ENV="github-copilot"
    [[ -n "${OPENAI_AGENT:-}" ]]                        && AGENT_ENV="openai"
    [[ "${TERM_PROGRAM:-}" == "vscode" ]]               && AGENT_ENV="vscode"
    [[ -n "${CI:-}" ]]                                  && AGENT_ENV="ci/${AGENT_ENV}"
  fi
  debug "Agent env: $AGENT_ENV"

  # When running inside an automation environment, default to --auto unless a
  # human explicitly disabled it.
  if [[ "$AGENT_ENV" != "human" && "$AGENT_ENV" != "vscode" ]] && [[ ! -t 0 ]]; then
    AUTO=1
  fi
}

# ----------------------------------------------------------------------------- #
#  Profile resolution
# ----------------------------------------------------------------------------- #
resolve_profile() {
  if [[ "$PROFILE" != "auto" ]]; then
    debug "Profile pinned: $PROFILE"
    return
  fi
  case "$GPU_VENDOR" in
    nvidia) PROFILE="nvidia" ;;
    amd)    PROFILE="amd" ;;
    apple)  PROFILE="cpu" ;;
    *)      PROFILE="cpu" ;;
  esac
  if (( RAM_GB < MIN_RAM_GB )); then
    warn "RAM ${RAM_GB} GB < ${MIN_RAM_GB} GB recommended — falling back to 'minimal' profile."
    PROFILE="minimal"
  fi
  ok "Auto-selected profile: ${C_BOLD}${PROFILE}${C_RESET}"
}

# ----------------------------------------------------------------------------- #
#  Prerequisite checks
# ----------------------------------------------------------------------------- #
need_install_hint() {
  case "$1" in
    docker)
      case "$OS_NAME" in
        ubuntu|debian|pop) echo "curl -fsSL https://get.docker.com | sh" ;;
        fedora|rhel|centos) echo "sudo dnf install -y docker docker-compose-plugin" ;;
        arch|manjaro)      echo "sudo pacman -S docker docker-compose" ;;
        macos)             echo "Install Docker Desktop: https://www.docker.com/products/docker-desktop" ;;
        *)                 echo "https://docs.docker.com/engine/install/" ;;
      esac
      ;;
    git)  echo "Install git via your package manager (apt/dnf/brew/pacman)." ;;
    curl) echo "Install curl via your package manager." ;;
    make) echo "Install make: build-essential (Debian) / xcode-select --install (macOS)." ;;
    *)    echo "Install '$1' via your package manager." ;;
  esac
}

check_prerequisites() {
  hdr "Checking prerequisites"

  if (( BASH_VERSINFO[0] < MIN_BASH_MAJOR )); then
    err "bash >= ${MIN_BASH_MAJOR} required (found ${BASH_VERSION})."
    exit 2
  fi

  case "$OS_FAMILY" in
    linux|darwin) ok "Supported OS: $OS_NAME $OS_VERSION ($OS_ARCH)" ;;
    windows) err "Windows requires WSL2. Please run this installer from inside WSL2."; exit 3 ;;
    *) err "Unsupported OS family: $OS_FAMILY"; exit 3 ;;
  esac

  local missing=()
  for cmd in curl git docker make awk sed grep tar tee; do
    if have_cmd "$cmd"; then
      debug "found: $cmd"
    else
      missing+=("$cmd")
      err "missing: $cmd  → $(need_install_hint "$cmd")"
    fi
  done

  if (( ${#missing[@]} )); then
    err "Install the missing tools and re-run."
    exit 2
  fi

  # Docker version
  local docker_ver
  docker_ver="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo 0.0.0)"
  if [[ "$docker_ver" == "0.0.0" ]]; then
    err "Docker daemon is not reachable. Start it with: sudo systemctl start docker (Linux) or open Docker Desktop."
    exit 2
  fi
  if ! semver_ge "$docker_ver" "$MIN_DOCKER_VERSION"; then
    err "Docker $docker_ver is too old (>= $MIN_DOCKER_VERSION required)."
    exit 2
  fi
  ok "Docker $docker_ver"

  if ! docker compose version >/dev/null 2>&1; then
    err "'docker compose' (v2 plugin) is required. Old 'docker-compose' is not supported."
    exit 2
  fi
  local compose_ver
  compose_ver="$(docker compose version --short 2>/dev/null || echo 0.0.0)"
  if ! semver_ge "$compose_ver" "$MIN_COMPOSE_VERSION"; then
    err "docker compose $compose_ver is too old (>= $MIN_COMPOSE_VERSION required)."
    exit 2
  fi
  ok "docker compose $compose_ver"

  # Disk
  if (( DISK_FREE_GB > 0 )) && (( DISK_FREE_GB < MIN_DISK_GB )); then
    warn "Only ${DISK_FREE_GB} GB free at $(dirname "$TARGET_DIR") (>= ${MIN_DISK_GB} GB recommended)."
    confirm "Continue anyway?" || { err "Aborted by user."; exit 5; }
  fi

  # RAM
  if (( RAM_GB > 0 )) && (( RAM_GB < MIN_RAM_GB )); then
    warn "Only ${RAM_GB} GB RAM detected (>= ${MIN_RAM_GB} GB minimum, ${RECOMMENDED_RAM_GB} GB recommended)."
  fi

  ok "All prerequisites satisfied."
}

# ----------------------------------------------------------------------------- #
#  Clone / update repository
# ----------------------------------------------------------------------------- #
clone_or_update_repo() {
  hdr "Source code"
  if (( DO_CLONE == 0 )); then
    if [[ ! -f "$PWD/install.sh" ]]; then
      err "--no-clone given but $PWD does not look like the repo (no install.sh)."
      exit 1
    fi
    TARGET_DIR="$PWD"
    ok "Using current directory: $TARGET_DIR"
    return
  fi

  if [[ -d "$TARGET_DIR/.git" ]]; then
    say "Repository already exists — fetching updates ($BRANCH)"
    run git -C "$TARGET_DIR" fetch --tags --prune origin
    run git -C "$TARGET_DIR" checkout "$BRANCH"
    run git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH" || warn "Could not fast-forward — continuing with existing checkout."
  else
    if [[ -e "$TARGET_DIR" ]]; then
      err "$TARGET_DIR exists and is not a git repository. Move it aside or pass --target-dir=..."
      exit 1
    fi
    say "Cloning $REPO_URL ($BRANCH) → $TARGET_DIR"
    run git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$TARGET_DIR"
  fi
  ok "Source ready at $TARGET_DIR"
}

# ----------------------------------------------------------------------------- #
#  .env generation
# ----------------------------------------------------------------------------- #
gen_secret() {
  # Returns a random hex string of length $1 (default 48). Hex keeps full
  # entropy and is shell-safe (no '+', '/', '=', or newlines).
  local len="${1:-48}"
  local bytes=$(( (len + 1) / 2 ))
  if have_cmd openssl; then
    openssl rand -hex "$bytes" | cut -c1-"$len"
  else
    LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c "$len"
  fi
}

setup_env_file() {
  hdr "Environment configuration"
  local env_path="$TARGET_DIR/.env"
  local example="$TARGET_DIR/.env.example"

  if [[ ! -f "$example" ]]; then
    err ".env.example missing in $TARGET_DIR — repo looks corrupt."
    exit 1
  fi

  if [[ -f "$env_path" ]]; then
    ok ".env already exists — leaving it untouched (idempotent)."
  else
    if (( DRY_RUN )); then
      _emit "${C_GREY}[dry-run]${C_RESET} would copy .env.example → .env and inject secrets"
    else
      cp "$example" "$env_path"
      # Replace every value that *is* an AENDERE_* placeholder, plus the
      # literal "changeme" / "changeme-in-production" defaults, with a freshly
      # generated 48-char hex secret. The original placeholder string is then
      # propagated across the rest of the file, so dependent values like
      # DATABASE_URL=postgresql://…:<PASSWORD>@… stay coherent.
      local key value secret old_placeholder
      local -a env_lines=()
      local -A replaced_placeholders=()
      mapfile -t env_lines <"$env_path"
      for line in "${env_lines[@]}"; do
        # KEY=VALUE only — comments and blanks fall through.
        [[ "$line" =~ ^([A-Z][A-Z0-9_]*)=(.*)$ ]] || continue
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"

        # We only treat a line as a "secret slot" when the value IS a
        # placeholder, not when it merely embeds one (e.g. DATABASE_URL).
        # Embedded placeholders are handled by the propagation below.
        if [[ "$value" =~ ^AENDERE_[A-Za-z0-9_]+$ ]]; then
          old_placeholder="$value"
          [[ -n "${replaced_placeholders[$old_placeholder]:-}" ]] && continue
          replaced_placeholders[$old_placeholder]=1
          secret="$(gen_secret 48)"
          # Propagate everywhere the placeholder appears (covers this line
          # AND any dependent URL / DSN that embeds the same token).
          awk -v old="$old_placeholder" -v new="$secret" '
            # For each line, replace all occurrences of the exact placeholder.
            # This keeps derived values coherent, e.g. if POSTGRES_PASSWORD is
            # generated from AENDERE_DIESES_PASSWORT_SOFORT, the same generated
            # value is also inserted into DATABASE_URL where that placeholder is
            # embedded inside a larger URL.
            { i=index($0, old)
              while (i>0) { $0 = substr($0,1,i-1) new substr($0,i+length(old)); i = index($0, old) }
              print }' \
            "$env_path" >"$env_path.tmp" && mv "$env_path.tmp" "$env_path"
          debug "generated secret for $key (propagated across .env)"
        elif [[ "$value" == "changeme" || "$value" == "changeme-in-production" ]]; then
          # Simple literal defaults do not need propagation: only replace this
          # exact KEY=value line.
          secret="$(gen_secret 48)"
          awk -v k="$key" -v v="$secret" -F'=' \
            'BEGIN{OFS="="} $1==k {sub(/^[^=]*=/, ""); print k, v; next} {print}' \
            "$env_path" >"$env_path.tmp" && mv "$env_path.tmp" "$env_path"
          debug "replaced 'changeme' default for $key"
        fi
      done

      # Sanity check: nothing AENDERE_* left, otherwise warn loudly.
      if grep -qE '=.*AENDERE_' "$env_path"; then
        warn ".env still contains AENDERE_* placeholders — please review:"
        grep -nE '=.*AENDERE_' "$env_path" | sed 's/^/  /' >&2 || true
      fi
      chmod 600 "$env_path"
      ok ".env generated with fresh secrets (chmod 600)."
    fi
  fi

  # Persist installation-time facts so other tools (kirobi_core, agents) can reuse them.
  local facts_dir="$TARGET_DIR/.kirobi"
  local facts="$facts_dir/install.json"
  if (( DRY_RUN == 0 )); then
    mkdir -p "$facts_dir"
    cat >"$facts" <<EOF
{
  "installer_version": "$INSTALLER_VERSION",
  "timestamp_utc": "$(date -u +%FT%TZ)",
  "os": {"family": "$OS_FAMILY", "name": "$OS_NAME", "version": "$OS_VERSION", "arch": "$OS_ARCH"},
  "hardware": {"cpu_cores": $CPU_CORES, "ram_gb": $RAM_GB, "disk_free_gb": $DISK_FREE_GB,
               "gpu_vendor": "$GPU_VENDOR", "gpu_model": "$GPU_MODEL", "gpu_vram_gb": $GPU_VRAM_GB},
  "agent_env": "$AGENT_ENV",
  "profile": "$PROFILE",
  "target_dir": "$TARGET_DIR",
  "branch": "$BRANCH"
}
EOF
    chmod 600 "$facts"
    ok "Saved install facts → ${facts/#$HOME/~}"
  fi
}

# ----------------------------------------------------------------------------- #
#  Folder & permission setup
# ----------------------------------------------------------------------------- #
setup_folders() {
  hdr "Initialising folders"
  if [[ -x "$TARGET_DIR/infra/scripts/init-folders.sh" ]]; then
    # init-folders.sh may try to create paths under /var that require root.
    # We don't want to abort the whole installer for that — warn instead.
    if ! run bash "$TARGET_DIR/infra/scripts/init-folders.sh"; then
      warn "init-folders.sh exited non-zero (often a sudo/permission issue) — continuing."
    fi
  fi
  # Ensure the five security zones exist with the right perms.
  for zone in sacred extracts/family-private quarantine; do
    if (( DRY_RUN )); then
      _emit "${C_GREY}[dry-run]${C_RESET} chmod 700 $TARGET_DIR/$zone"
    else
      mkdir -p "$TARGET_DIR/$zone"
      chmod 700 "$TARGET_DIR/$zone" || true
    fi
  done
  ok "Zone folders ready (sacred/extracts-family-private/quarantine = 0700)."
}

# ----------------------------------------------------------------------------- #
#  Profile-specific compose override (supports layering: --profile=cpu,voice-full)
# ----------------------------------------------------------------------------- #
# Compose merges multiple `-f` files cleanly (it's the official layering
# mechanism), but a naive `cat` of two YAML files yields invalid YAML
# (duplicate top-level `services:` keys). So:
#   • A single profile  → write `docker-compose.override.yml` as before
#                         (docker compose picks it up automatically).
#   • Multiple profiles → write a header into `docker-compose.override.yml`
#                         AND set `COMPOSE_FILE=...` in `.env`, so every
#                         subsequent `docker compose …` call layers them in
#                         the right order.
write_profile_override() {
  hdr "Compose profile: $PROFILE"
  local override="$TARGET_DIR/docker-compose.override.yml"
  local templates_dir="$TARGET_DIR/config/templates/compose"
  local env_path="$TARGET_DIR/.env"

  IFS=',' read -r -a profile_list <<<"$PROFILE"
  local templates=() missing=()
  for p in "${profile_list[@]}"; do
    p="${p// /}"
    [[ -z "$p" ]] && continue
    local t="$templates_dir/profile-${p}.yml"
    if [[ -f "$t" ]]; then
      templates+=("$t")
    else
      missing+=("$p")
    fi
  done

  if (( ${#missing[@]} )); then
    warn "No template for profile(s): ${missing[*]} — relying on docker-compose.yml defaults for those."
  fi

  if (( ${#templates[@]} == 0 )); then
    debug "Nothing to write — no matching templates."
    return
  fi

  if (( ${#templates[@]} == 1 )); then
    if (( DRY_RUN )); then
      _emit "${C_GREY}[dry-run]${C_RESET} would copy ${templates[0]} → $override"
      return
    fi
    cp "${templates[0]}" "$override"
    chmod 644 "$override"
    ok "Wrote docker-compose.override.yml from profile template."
    return
  fi

  # Layered case: copy the FIRST template to docker-compose.override.yml
  # (docker compose's default override slot) and ask compose to additionally
  # apply the rest via COMPOSE_FILE.
  if (( DRY_RUN )); then
    _emit "${C_GREY}[dry-run]${C_RESET} would copy ${templates[0]} → $override"
    _emit "${C_GREY}[dry-run]${C_RESET} would set COMPOSE_FILE in .env to layer ${#templates[@]} files"
    return
  fi
  cp "${templates[0]}" "$override"
  chmod 644 "$override"

  # Build colon-separated list relative to TARGET_DIR.
  local -a parts=( "docker-compose.yml" "docker-compose.override.yml" )
  local i
  for ((i=1; i<${#templates[@]}; i++)); do
    # Template paths are absolute under TARGET_DIR; strip the prefix so the
    # COMPOSE_FILE list works regardless of the user's cwd-via-make.
    parts+=( "${templates[i]#"$TARGET_DIR/"}" )
  done
  local compose_files; compose_files="$(IFS=: ; echo "${parts[*]}")"

  if [[ -f "$env_path" ]]; then
    # Replace any existing COMPOSE_FILE= line, otherwise append.
    if grep -q '^COMPOSE_FILE=' "$env_path"; then
      # Anchor the match at the start of the line so a stray '=' inside an
      # unrelated value can never collide with the rewrite.
      awk -v v="$compose_files" '
        /^COMPOSE_FILE=/ { print "COMPOSE_FILE=" v; next }
        { print }' \
        "$env_path" >"$env_path.tmp" && mv "$env_path.tmp" "$env_path"
    else
      printf '\n# Auto-set by install.sh for layered profile (%s)\nCOMPOSE_FILE=%s\n' \
        "$PROFILE" "$compose_files" >>"$env_path"
    fi
    chmod 600 "$env_path"
  fi
  ok "Wrote layered profile (${#templates[@]} files) — COMPOSE_FILE pinned in .env."
}

# ----------------------------------------------------------------------------- #
#  Pull, start, models
# ----------------------------------------------------------------------------- #
pull_images() {
  (( DO_PULL )) || { ok "Skipping image pull (--no-pull)"; return; }
  hdr "Pulling Docker images"
  ( cd "$TARGET_DIR" && run docker compose pull )
}

start_services() {
  (( DO_START )) || { ok "Skipping service start (--no-start)"; return; }
  hdr "Starting services"
  ( cd "$TARGET_DIR" && run docker compose up -d )
  ok "Services started in detached mode."
}

pull_models() {
  (( DO_MODELS )) || { ok "Skipping model download (--no-models)"; return; }
  if [[ -x "$TARGET_DIR/infra/scripts/pull-models.sh" ]]; then
    hdr "Downloading Ollama models (this can take a while)"
    ( cd "$TARGET_DIR" && run bash infra/scripts/pull-models.sh ) || warn "Model download reported a problem — see log."
  fi
}

# ----------------------------------------------------------------------------- #
#  Validation
# ----------------------------------------------------------------------------- #
validate() {
  hdr "Validation"
  local ok_count=0 fail_count=0

  # 1. .env sanity (placeholders, weak secrets, perms). Skip when .env was
  #    not actually written (e.g. dry-run, or --no-clone in a fresh checkout).
  if [[ -f "$TARGET_DIR/.env" ]] && [[ -x "$TARGET_DIR/infra/scripts/validate-env.sh" ]]; then
    local rc=0
    if ( cd "$TARGET_DIR" && bash infra/scripts/validate-env.sh --quiet ) >>"$LOG_FILE" 2>&1; then
      ok ".env validation passed"; (( ++ok_count ))
    else
      rc=$?
      if (( rc == 2 )); then
        warn ".env validation: warnings only (exit 2)"; (( ++ok_count ))
      else
        err  ".env validation FAILED (exit $rc) — see $LOG_FILE"
        (( ++fail_count ))
      fi
    fi
  fi

  if (( DO_START )) && (( DRY_RUN == 0 )); then
    if [[ -x "$TARGET_DIR/infra/scripts/healthcheck.sh" ]]; then
      if ( cd "$TARGET_DIR" && bash infra/scripts/healthcheck.sh ) >>"$LOG_FILE" 2>&1; then
        ok "healthcheck.sh passed"; (( ++ok_count ))
      else
        err "healthcheck.sh reported failures — see $LOG_FILE"; (( ++fail_count ))
      fi
    fi
    if ( cd "$TARGET_DIR" && docker compose ps --status=running --quiet 2>/dev/null ) | grep -q .; then
      ok "Containers reported as running"; (( ++ok_count ))
    else
      err "No running containers found."; (( ++fail_count ))
    fi
  fi

  if (( fail_count > 0 )); then
    err "Validation finished with $fail_count failure(s) (and $ok_count passing check(s))."
    return 6
  fi
  ok "Validation passed ($ok_count check(s))."
  return 0
}

# ----------------------------------------------------------------------------- #
#  Uninstall (containers only — data is preserved)
# ----------------------------------------------------------------------------- #
uninstall() {
  hdr "Uninstall"
  warn "This stops & removes containers. Volumes (your data) are NOT deleted."
  confirm "Proceed?" || { err "Aborted."; exit 5; }
  ( cd "$TARGET_DIR" && run docker compose down --remove-orphans )
  ok "Containers removed. To purge volumes: docker compose down -v"
}

# ----------------------------------------------------------------------------- #
#  Summary
# ----------------------------------------------------------------------------- #
summary() {
  cat <<EOF

${C_BOLD}${C_GREEN}╔══════════════════════════════════════════════════════════════╗
║                  Installation complete                       ║
╚══════════════════════════════════════════════════════════════╝${C_RESET}

  ${C_BOLD}Repository :${C_RESET} $TARGET_DIR
  ${C_BOLD}Profile    :${C_RESET} $PROFILE
  ${C_BOLD}Hardware   :${C_RESET} ${CPU_CORES} cores · ${RAM_GB} GB RAM · GPU=${GPU_VENDOR}
  ${C_BOLD}Log file   :${C_RESET} $LOG_FILE

  Next steps:
    cd $TARGET_DIR
    make status        # check service health
    make logs          # follow logs
    make help          # see all commands

  Web UIs (default ports, see .env to customise):
    Open WebUI : http://localhost:3000
    Flowise    : http://localhost:3001
    Family PWA : http://localhost:3002 (or http://kirobi.local via Caddy)

  Docs:
    AGENT-INSTALLATION.md     — quickstart for humans & agents
    AGENT-SYSTEM-PROMPT.md    — drop into your coding agent
    AGENT-DECISION-MATRIX.md  — autonomy rules
    AGENT-RECOVERY.md         — what to do when things break

  ${C_GREY}Have fun, and remember: SACRED data never leaves the box.${C_RESET}

EOF
}

# ----------------------------------------------------------------------------- #
#  Main
# ----------------------------------------------------------------------------- #
main() {
  parse_args "$@"
  banner
  detect_os
  detect_hardware
  detect_agent_env
  resolve_profile

  if (( DO_UNINSTALL )); then
    [[ -d "$TARGET_DIR" ]] || { err "Nothing installed at $TARGET_DIR"; exit 1; }
    uninstall
    exit 0
  fi

  (( SKIP_CHECKS )) || check_prerequisites
  clone_or_update_repo
  setup_env_file
  setup_folders
  write_profile_override
  pull_images
  start_services
  pull_models
  if ! validate; then
    err "Bootstrap completed with validation failures — review the log: $LOG_FILE"
    summary
    exit 6
  fi
  summary
}

main "$@"
