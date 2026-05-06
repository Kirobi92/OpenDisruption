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
#   --profile=NAME     compose profile: auto|minimal|cpu|nvidia|amd|voice-full|production|development
#   --target-dir=PATH  installation directory (default: $HOME/OpenDisruption)
#   --branch=NAME      git branch to clone (default: main)
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
readonly MIN_COMPOSE_VERSION="2.0"
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

usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; }

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
    "$@" 2>&1 | tee -a "$LOG_FILE"
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
  read -r -p "$(printf '%b' "${C_YELLOW}? ${prompt} [y/N] ${C_RESET}")" reply
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
detect_os() {
  OS_KERNEL="$(uname -s)"
  OS_ARCH="$(uname -m)"
  OS_NAME="unknown"; OS_VERSION="unknown"; OS_FAMILY="unknown"

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
  AGENT_ENV="human"
  [[ -n "${CURSOR_AGENT:-}" ]]                        && AGENT_ENV="cursor"
  [[ -n "${CLAUDE_CODE:-}" || -n "${CLAUDECODE:-}" ]] && AGENT_ENV="claude-code"
  [[ -n "${ANTHROPIC_AGENT:-}" ]]                     && AGENT_ENV="claude"
  [[ -n "${COPILOT_AGENT_ID:-}" ]]                    && AGENT_ENV="github-copilot"
  [[ -n "${OPENAI_AGENT:-}" ]]                        && AGENT_ENV="openai"
  [[ "${TERM_PROGRAM:-}" == "vscode" ]]               && AGENT_ENV="vscode"
  [[ -n "${CI:-}" ]]                                  && AGENT_ENV="ci/${AGENT_ENV}"
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
  for cmd in curl git docker make awk sed grep tar; do
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
      # Replace every "AENDERE_DIESEN_SCHLUESSEL" placeholder with a fresh secret.
      while IFS= read -r line; do
        if [[ "$line" =~ ^([A-Z0-9_]+)=.*AENDERE_DIESEN_SCHLUESSEL ]]; then
          local key="${BASH_REMATCH[1]}"
          local secret; secret="$(gen_secret 48)"
          # Use awk to replace the value safely (no regex headaches with /).
          awk -v k="$key" -v v="$secret" -F'=' \
            'BEGIN{OFS="="} $1==k {print k, v; next} {print}' \
            "$env_path" >"$env_path.tmp" && mv "$env_path.tmp" "$env_path"
          debug "generated secret for $key"
        fi
      done <"$env_path"
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
    run bash "$TARGET_DIR/infra/scripts/init-folders.sh"
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
#  Profile-specific compose override
# ----------------------------------------------------------------------------- #
write_profile_override() {
  hdr "Compose profile: $PROFILE"
  local override="$TARGET_DIR/docker-compose.override.yml"
  local template="$TARGET_DIR/config/templates/compose/profile-${PROFILE}.yml"

  if [[ -f "$template" ]]; then
    if (( DRY_RUN )); then
      _emit "${C_GREY}[dry-run]${C_RESET} would copy $template → $override"
    else
      cp "$template" "$override"
      ok "Wrote docker-compose.override.yml from profile template."
    fi
  else
    debug "No template for profile '$PROFILE' — relying on docker-compose.yml defaults."
  fi
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
  if [[ -x "$TARGET_DIR/infra/scripts/healthcheck.sh" ]]; then
    if ( cd "$TARGET_DIR" && bash infra/scripts/healthcheck.sh ) >>"$LOG_FILE" 2>&1; then
      ok "healthcheck.sh passed"; (( ++ok_count ))
    else
      warn "healthcheck.sh reported issues — see $LOG_FILE"; (( ++fail_count ))
    fi
  fi
  if ( cd "$TARGET_DIR" && docker compose ps --status=running --quiet ) | grep -q .; then
    ok "Containers reported as running"; (( ++ok_count ))
  else
    warn "No running containers found."; (( ++fail_count ))
  fi
  (( fail_count == 0 )) || warn "Validation finished with $fail_count warning(s)."
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
  validate
  summary
}

main "$@"
