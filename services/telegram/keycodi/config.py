"""
services/telegram/keycodi/config.py
Zentrale Konfiguration für den KeyCodi Telegram-Bot v3.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
    if uid.strip().isdigit()
}
NOTIFY_CHANNEL_ID: str = os.getenv("TELEGRAM_NOTIFY_CHANNEL_ID", "").strip()
NOTIFY_ON_START: bool = os.getenv("TELEGRAM_NOTIFY_ON_START", "false").lower() in {"1", "true", "yes", "ja"}
WEBHOOK_HOST: str = os.getenv("TELEGRAM_WEBHOOK_HOST", "").strip()
WEBHOOK_PATH: str = "/telegram/webhook"
PORT: int = int(os.getenv("TELEGRAM_SERVICE_PORT", "8005"))
TELEGRAM_API: str = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE_API: str = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
_telegram_web_base = (
    os.getenv("KIROBI_TELEGRAM_WEB_BASE_URL", "").strip()
    or os.getenv("KIROBI_TAILSCALE_HOST", "").strip()
    or os.getenv("TAILSCALE_HOSTNAME", "").strip()
    or os.getenv("KIROBI_HOSTNAME", "kirobi.local").strip()
)
if _telegram_web_base and not _telegram_web_base.startswith(("http://", "https://")):
    _telegram_web_base = f"http://{_telegram_web_base}"
KIROBI_TELEGRAM_WEB_BASE_URL: str = _telegram_web_base.rstrip("/")
_telegram_web_base = (
    os.getenv("KIROBI_TELEGRAM_WEB_BASE_URL", "").strip()
    or os.getenv("KIROBI_TAILSCALE_HOST", "").strip()
    or os.getenv("TAILSCALE_HOSTNAME", "").strip()
    or os.getenv("KIROBI_HOSTNAME", "kirobi.local").strip()
)
if _telegram_web_base and not _telegram_web_base.startswith(("http://", "https://")):
    _telegram_web_base = f"http://{_telegram_web_base}"
KIROBI_TELEGRAM_WEB_BASE_URL: str = _telegram_web_base.rstrip("/")

# ─── Kirobi API / Auth ───────────────────────────────────────────────────────
KIROBI_API_URL: str = os.getenv("KIROBI_API_URL", "http://api:8000").rstrip("/")
KIROBI_AUTH_URL: str = os.getenv("KIROBI_AUTH_URL", os.getenv("AUTH_SERVICE_URL", "http://auth:8000")).rstrip("/")
KIROBI_API_TOKEN: str = os.getenv("KIROBI_API_TOKEN", "").strip()
KIROBI_BOT_USER: str = (os.getenv("KIROBI_BOT_USER", "") or os.getenv("KIROBI_DEFAULT_USER", "sven")).strip()
KIROBI_BOT_PASS: str = (os.getenv("KIROBI_BOT_PASSWORD", "") or os.getenv("KIROBI_DEFAULT_PASSWORD", "")).strip()

# ─── Datenbank ───────────────────────────────────────────────────────────────
DATABASE_URL: str = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)

# ─── Ollama / LLM ────────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto").strip().lower()
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.1:8b")
OLLAMA_CODE_MODEL: str = os.getenv("OLLAMA_CODE_MODEL", "qwen2.5-coder:32b")
OLLAMA_NUM_PARALLEL: int = int(os.getenv("OLLAMA_NUM_PARALLEL", "4"))
GITHUB_MODELS_TOKEN: str = os.getenv("GITHUB_MODELS_TOKEN", "").strip()
GITHUB_MODELS_URL: str = os.getenv(
    "GITHUB_MODELS_URL",
    "https://models.github.ai/inference/chat/completions",
).rstrip("/")
GITHUB_CHAT_MODEL: str = os.getenv("GITHUB_CHAT_MODEL", "openai/gpt-4.1-mini").strip()
GITHUB_REASONING_MODEL: str = os.getenv("GITHUB_REASONING_MODEL", "openai/gpt-4.1").strip()
GITHUB_CODE_MODEL: str = os.getenv("GITHUB_CODE_MODEL", GITHUB_REASONING_MODEL).strip()
VOICE_SERVICE_URL: str = os.getenv("VOICE_SERVICE_URL", "http://voice-processing:8001").rstrip("/")

# ─── Hardware / Parallelisierung ─────────────────────────────────────────────
CPU_CORES: int = int(os.getenv("KIROBI_CPU_CORES", "0")) or __import__("os").cpu_count() or 4
MAX_PARALLEL_LOCAL_AGENTS: int = int(os.getenv("KIROBI_MAX_PARALLEL_LOCAL", str(max(4, CPU_CORES // 4))))
MAX_PARALLEL_CLOUD_MODELS: int = int(os.getenv("KIROBI_MAX_PARALLEL_CLOUD", "3"))

# ─── Cron / Reports ──────────────────────────────────────────────────────────
CRON_REPORT_INTERVAL_MIN: int = int(os.getenv("KIROBI_CRON_REPORT_INTERVAL", "30"))
KIROBI_TELEGRAM_PROGRESS_INTERVAL_SEC: int = int(
    os.getenv("KIROBI_TELEGRAM_PROGRESS_INTERVAL_SEC", "60")
)

# ─── Events-Log ──────────────────────────────────────────────────────────────
EVENTS_LOG_PATH: str = os.getenv("KIROBI_EVENTS_LOG", "kirobi-core/core-events.log")
