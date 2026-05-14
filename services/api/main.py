from __future__ import annotations

"""
Kirobi Main API Service
Zone: WORKSPACE
Purpose: Main API for family interactions with Kirobi
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field
import asyncpg
import httpx
from dotenv import load_dotenv
import aiofiles
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

try:
    from kirobi_core.analytics_client import track as _analytics_track
except Exception:  # noqa: BLE001
    async def _analytics_track(*_args, **_kwargs) -> None:  # type: ignore[misc]
        pass

load_dotenv()

# Docker-internal services listen on container port 8000 even when the host port
# differs. Normalize env-provided URLs so service-to-service calls stay reachable.
_INTERNAL_SERVICE_PORTS = {
    "api": 8000,
    "auth": 8000,
    "analytics": 8010,
    "embeddings": 8000,
    "ingest": 8000,
    "model-routing": 8009,  # external=8009, internal=8009 — no-op, prevents wrong rewrite
    "retrieval": 8000,
}


def _service_url(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    target_port = _INTERNAL_SERVICE_PORTS.get(host)
    if not target_port or parsed.port in (None, target_port):
        return value.rstrip("/")
    netloc = f"{host}:{target_port}"
    return urlunparse(parsed._replace(netloc=netloc)).rstrip("/")


# Configuration
_PG_PW = os.environ.get("POSTGRES_PASSWORD", "")
if not _PG_PW or _PG_PW == "changeme":
    raise RuntimeError("POSTGRES_PASSWORD missing or insecure default ('changeme'). Set it in .env.")
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:{_PG_PW}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'kirobi')}"
AUTH_SERVICE_URL = _service_url(os.getenv("AUTH_SERVICE_URL", "http://auth:8000"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
RETRIEVAL_SERVICE_URL = _service_url(os.getenv("RETRIEVAL_SERVICE_URL", "http://retrieval:8006"))
MODEL_ROUTING_SERVICE_URL = _service_url(os.getenv("MODEL_ROUTING_SERVICE_URL", "http://model-routing:8009"))
VOICE_SERVICE_URL = _service_url(os.getenv("VOICE_SERVICE_URL", "http://voice-processing:8001"))
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
OLLAMA_FALLBACK_MODEL = "llama3.1:8b"
MVP_ALLOWED_ZONES = ("PUBLIC", "WORKSPACE", "FAMILY_PRIVATE")
MVP_REFUSED_ZONES = {"SACRED", "QUARANTINE"}
# Verzeichnis wird lazy beim ersten Upload erstellt, nicht beim Import

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


API_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    title       TEXT,
    zone        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived    BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id         TEXT,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    model_used      TEXT,
    tokens_used     INTEGER,
    attachments     JSONB NOT NULL DEFAULT '[]'::JSONB,
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS file_uploads (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    filename            TEXT NOT NULL,
    original_filename   TEXT NOT NULL,
    file_path           TEXT NOT NULL,
    file_size           BIGINT NOT NULL,
    mime_type           TEXT,
    zone                TEXT NOT NULL,
    processed           BOOLEAN NOT NULL DEFAULT FALSE,
    metadata            JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS conversations_user_archived_idx
    ON conversations(user_id, archived);
CREATE INDEX IF NOT EXISTS conversations_updated_at_idx
    ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS messages_conversation_created_idx
    ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS file_uploads_user_created_idx
    ON file_uploads(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS file_uploads_zone_idx
    ON file_uploads(zone);
"""


async def _ensure_schema() -> None:
    """Create API-owned tables on first boot.

    Auth owns users and zone_permissions. The API only bootstraps its own
    storage so the chat/upload flow can come up on a fresh database.
    """
    async with db_pool.acquire() as conn:
        await conn.execute(API_SCHEMA)


# Pydantic Models
class User(BaseModel):
    id: str
    username: str
    display_name: str
    role: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    zone: str = "FAMILY_PRIVATE"


class Conversation(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    zone: str
    created_at: datetime
    updated_at: datetime
    archived: bool


class MessageCreate(BaseModel):
    content: str
    attachments: Optional[List[str]] = []
    model: Optional[str] = None
    agent: Optional[str] = None
    reasoning_mode: str = "normal"
    source_modes: List[str] = Field(default_factory=lambda: ["local"])
    web_search: bool = False
    deep_research: bool = False
    show_reasoning: bool = True
    system_prompt_extra: Optional[str] = None


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Compatibility request for lightweight clients.

    Voice/Desktop clients use this endpoint without owning a persisted
    conversation yet. It is intentionally WORKSPACE-only and does not fetch
    FAMILY_PRIVATE/SACRED context.
    """
    message: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    message: str
    response: str
    content: str
    model_used: str
    zone: str = "WORKSPACE"


class Message(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    conversation_id: str
    user_id: Optional[str]
    role: str
    content: str
    model_used: Optional[str]
    tokens_used: Optional[int]
    attachments: List = []
    metadata: dict = {}
    created_at: datetime


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    zone: str
    processed: bool = False
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class DashboardTask(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    agent: Optional[str] = None
    zone: str = "WORKSPACE"
    last_error: Optional[str] = None
    operator_hint: str = ""


class DashboardTasksResponse(BaseModel):
    tasks: List[DashboardTask]


class ControlEvent(BaseModel):
    timestamp: datetime
    event_type: str
    severity: str
    message: str


class ControlActionItem(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    agent: Optional[str] = None
    zone: str = "WORKSPACE"
    last_error: Optional[str] = None
    operator_hint: str


class OperatorControlStatus(BaseModel):
    supervisorAvailable: bool
    autonomousMode: str
    humanGateZones: List[str] = Field(default_factory=list)
    queueDepth: int
    pendingTasks: int
    activeTasks: int
    completedTasks: int
    blockedTasks: int
    deadLetterTasks: int
    attentionRequired: int
    lastEventAt: Optional[datetime] = None
    lastHealthCheckAt: Optional[datetime] = None
    health: dict[str, str] = Field(default_factory=dict)
    recentEvents: List[ControlEvent] = Field(default_factory=list)
    attentionTasks: List[ControlActionItem] = Field(default_factory=list)
    operatorGuidance: List[str] = Field(default_factory=list)


class UISearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    zone: Optional[str] = Field(default=None, max_length=32)
    limit: int = Field(default=10, ge=1, le=50)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    family_private_approved: bool = False


class UISearchResult(BaseModel):
    id: str
    score: float
    source: str
    zone: str
    snippet: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None


class UISearchResponse(BaseModel):
    query: str
    zone: str
    total: int
    collection: str
    local_only: bool = True
    approval_required: bool = False
    family_private_approved: bool = False
    refusal_semantics: str = "zone-aware"
    results: List[UISearchResult]


class TextUploadCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    title: Optional[str] = Field(default=None, max_length=200)
    zone: str = Field(default="WORKSPACE", max_length=32)
    human_approved: bool = False
    approval_note: Optional[str] = Field(default=None, max_length=500)


class ChatRuntimeOptions(BaseModel):
    available_models: List[str]
    default_model: str
    current_defaults: dict = Field(default_factory=dict)
    agent_options: List[dict] = Field(default_factory=list)
    reasoning_modes: List[dict] = Field(default_factory=list)
    source_modes: List[dict] = Field(default_factory=list)
    voice: dict = Field(default_factory=dict)


class DashboardActivityItem(BaseModel):
    id: str
    surface: str
    kind: str
    actor: str
    summary: str
    zone: Optional[str] = None
    created_at: datetime


class DashboardActivityResponse(BaseModel):
    items: List[DashboardActivityItem]


def _json_field(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, type(fallback)):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return fallback
        return parsed if isinstance(parsed, type(fallback)) else fallback
    return fallback


def _message_from_row(row: asyncpg.Record) -> Message:
    data = dict(row)
    data["attachments"] = _json_field(data.get("attachments"), [])
    data["metadata"] = _json_field(data.get("metadata"), {})
    return Message(**data)


def _upload_from_row(row: asyncpg.Record) -> "FileUploadResponse":
    data = dict(row)
    data["metadata"] = _json_field(data.get("metadata"), {})
    return FileUploadResponse(**data)


def _upload_policy_metadata(
    zone: str,
    *,
    human_approved: bool = False,
    approval_note: Optional[str] = None,
) -> dict:
    clean_note = (approval_note or "").strip() or None
    metadata = {
        "zone_policy": zone,
        "storage_mode": "local-first-file-backed",
        "local_only": True,
        "approval_required": zone == "FAMILY_PRIVATE",
        "human_approved": False,
        "approval_note": clean_note,
        "refusal_semantics": "zone-aware",
    }
    if zone in {"PUBLIC", "WORKSPACE"}:
        return metadata
    if zone == "FAMILY_PRIVATE":
        if not human_approved or not clean_note:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "FAMILY_PRIVATE uploads require explicit local human approval "
                    "and a non-empty approval_note."
                ),
            )
        metadata["human_approved"] = True
        metadata["refusal_semantics"] = "family-private-requires-human-approval"
        return metadata
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{zone} is protected and not available in the MVP surface")


def _safe_upload_path(path_value: str) -> Path:
    path = Path(path_value).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if path != upload_root and upload_root not in path.parents:
        raise HTTPException(status_code=403, detail="Upload path outside configured upload directory")
    return path


def _search_title(source: str) -> str:
    name = Path(source).name
    return name or source


def _reasoning_mode_label(mode: str) -> str:
    return {
        "off": "Denken aus",
        "weak": "schwach",
        "normal": "normal",
        "deep": "tiefgründig",
        "ultra-deep": "ULTRA-DEEP",
    }.get(mode, mode)


def _agent_prompt(agent: Optional[str]) -> str:
    normalized = (agent or "kirobi").strip().lower()
    prompts = {
        "kirobi": "Du bist Kirobi, der lokale Hauptassistent.",
        "hermes": "Du agierst im Stil von Hermes: analytisch, planend und strukturierend.",
        "opencode": "Du agierst im Stil von Opencode: coding-orientiert, präzise, umsetzungsnah.",
        "researcher": "Du agierst wie ein lokaler Research-Agent: quellenbewusst, syntheseorientiert.",
        "strategist": "Du agierst wie ein Strategist-Agent: priorisiert, abwägend, fokussiert auf Entscheidungen.",
        "keycodi": "Du bist KeyCodi, der Master-Code-Orchestrator. Plane Missionen mit AQAL-Bewusstsein, sequenziere Phasen sauber.",
        "kirobi-architect": "Du bist Kirobi-Architect. Entwirf Systeme, Diagramme und Datenflüsse — keine Implementierung, nur Designentscheidungen.",
        "kirobi-coder": "Du bist Kirobi-Coder. Implementiere präzise, idiomatisch, mit Tests. Nutze die Repo-Konventionen (CLAUDE.md, AGENTS.md).",
        "kirobi-ops": "Du bist Kirobi-Ops. Verantworte Compose, Caddy, Backups, Healthchecks. Sicherheit > Geschwindigkeit.",
        "kirobi-frontend": "Du bist Kirobi-Frontend. Next.js + SvelteKit, Tailwind, shadcn — Aurora/Void-Theme, Performance 60fps.",
        "kirobi-docs": "Du bist Kirobi-Docs. Schreibe deutsch, mit Frontmatter (zone, version), klar und knapp.",
        "kirobi-reviewer": "Du bist Kirobi-Reviewer. Code-Reviews mit hohem Signal: Bugs, Security, Logikfehler — kein Style-Bikeshedding.",
        "code-reviewer": "Du bist ein Code-Reviewer. Surgical reviews: bugs, security, race conditions, leaks. Ignore style.",
        "security-auditor": "Du bist Security-Auditor. Threat-Modeling, Secret-Scan, Zone-Compliance, Prompt-Injection-Defense.",
        "test-engineer": "Du bist Test-Engineer. TDD: schreibe failing tests zuerst, dann minimal-pass-Implementierung.",
        # Persönliche Agenten — via personal-agents Service (Port 8017)
        "sven": "Du bist Kirobi — Svens persönlicher Assistent. Antworte NUR auf Basis gespeicherter Fakten. Bei unbekannten Fakten: nachfragen statt erfinden.",
        "samira": "Du bist Kirobi — Samiras persönliche Assistentin. Warm, einfühlsam, direkt. Antworte NUR auf Basis gespeicherter Fakten. Bei unbekannten Fakten: nachfragen.",
        "sineo": "Du bist Kirobi — Sineos persönlicher Begleiter. Motivierend, auf Augenhöhe (14-Jähriger), Creator-Coach. Antworte NUR auf Basis gespeicherter Fakten. Bei unbekannten Fakten: nachfragen.",
    }
    return prompts.get(normalized, prompts["kirobi"])


async def _chat_runtime_options_payload() -> ChatRuntimeOptions:
    models = [OLLAMA_FALLBACK_MODEL]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MODEL_ROUTING_SERVICE_URL}/models")
            if response.status_code == 200:
                payload = response.json()
                models = payload.get("models") or models
    except Exception:
        pass

    voice_payload = {"available": False}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{VOICE_SERVICE_URL}/models/info")
            if response.status_code == 200:
                voice_payload = {"available": True, **response.json()}
    except Exception:
        pass

    return ChatRuntimeOptions(
        available_models=models,
        default_model=models[0] if models else OLLAMA_FALLBACK_MODEL,
        current_defaults={
            "chat": "llama3.1:8b",
            "admin_chat": "llama3.1:70b",
            "reasoning": "deepseek-r1:7b",
            "code": "qwen2.5-coder:7b",
        },
        agent_options=[
            {"id": "kirobi", "label": "Kirobi", "description": "Allround lokaler Hauptassistent", "category": "core", "default_model": "llama3.1:8b"},
            {"id": "keycodi", "label": "KeyCodi", "description": "Master-Code-Orchestrator (AQAL-Phasen)", "category": "orchestrator", "default_model": "llama3.1:8b"},
            {"id": "hermes", "label": "Hermes", "description": "Analyse, Struktur, Reasoning", "category": "core", "default_model": "llama3.1:8b"},
            {"id": "opencode", "label": "Opencode", "description": "Coding-Workbench", "category": "coding", "default_model": "qwen2.5-coder:7b"},
            {"id": "researcher", "label": "Researcher", "description": "Quellen + Synthese", "category": "research", "default_model": "llama3.1:8b"},
            {"id": "strategist", "label": "Strategist", "description": "Planung & Priorisierung", "category": "core", "default_model": "llama3.1:8b"},
            {"id": "kirobi-architect", "label": "Architect", "description": "System- & Datenfluss-Design", "category": "design", "default_model": "llama3.1:8b"},
            {"id": "kirobi-coder", "label": "Coder", "description": "Implementierung mit Tests", "category": "coding", "default_model": "qwen2.5-coder:7b"},
            {"id": "kirobi-ops", "label": "Ops", "description": "Compose, Caddy, Backups, Health", "category": "ops", "default_model": "llama3.1:8b"},
            {"id": "kirobi-frontend", "label": "Frontend", "description": "Next/SvelteKit, Tailwind, 60fps", "category": "coding", "default_model": "qwen2.5-coder:7b"},
            {"id": "kirobi-docs", "label": "Docs", "description": "Deutsche Dokumentation, Frontmatter", "category": "docs", "default_model": "mistral:7b"},
            {"id": "kirobi-reviewer", "label": "Reviewer", "description": "Surgical Code-Review", "category": "review", "default_model": "qwen2.5-coder:7b"},
            {"id": "code-reviewer", "label": "Code-Reviewer", "description": "Bugs · Security · Logikfehler", "category": "review", "default_model": "qwen2.5-coder:7b"},
            {"id": "security-auditor", "label": "Security-Auditor", "description": "Threat-Modeling, Zone-Compliance", "category": "security", "default_model": "llama3.1:8b"},
            {"id": "test-engineer", "label": "Test-Engineer", "description": "TDD mit failing-tests-first", "category": "testing", "default_model": "qwen2.5-coder:7b"},
            # Persönliche Agenten (personal-agents Service, Port 8017)
            {"id": "sven", "label": "Kirobi (Sven)", "description": "Svens persönlicher Assistent — faktenbasiert, kein Halluzinieren", "category": "personal", "default_model": "qwen2.5:14b"},
            {"id": "samira", "label": "Kirobi (Samira)", "description": "Samiras persönliche Assistentin — warm, einfühlsam, faktenbasiert", "category": "personal", "default_model": "qwen2.5:14b"},
            {"id": "sineo", "label": "Kirobi (Sineo)", "description": "Sineos persönlicher Begleiter — motivierend, Creator-Coach, faktenbasiert", "category": "personal", "default_model": "qwen2.5:14b"},
        ],
        reasoning_modes=[
            {"id": "off", "label": "aus"},
            {"id": "weak", "label": "schwach"},
            {"id": "normal", "label": "normal"},
            {"id": "deep", "label": "tiefgründig"},
            {"id": "ultra-deep", "label": "ULTRA-DEEP"},
        ],
        source_modes=[
            {"id": "local", "label": "Local RAG", "active": True},
            {"id": "websearch", "label": "Websearch intent", "active": False},
            {"id": "deep-research", "label": "Deep Research intent", "active": False},
        ],
        voice=voice_payload,
    )


async def _select_chat_model(requested_model: Optional[str], *, reasoning_mode: str, deep_research: bool, agent: Optional[str]) -> tuple[str, str]:
    if requested_model:
        return requested_model, "manuell gewählt"

    agent_lower = (agent or "").lower()
    coding_agents = {"opencode", "kirobi-coder", "kirobi-frontend", "kirobi-reviewer", "code-reviewer", "test-engineer"}
    reasoning_agents = {"hermes", "researcher", "strategist", "keycodi", "kirobi-architect", "security-auditor"}
    if agent_lower in coding_agents:
        task_type = "code"
    elif reasoning_mode in {"deep", "ultra-deep"} or deep_research or agent_lower in reasoning_agents:
        task_type = "reasoning"
    else:
        task_type = "chat"
    prefer_fast = reasoning_mode in {"off", "weak"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{MODEL_ROUTING_SERVICE_URL}/route",
                json={
                    "task_type": task_type,
                    "context_length": 0,
                    "prefer_fast": prefer_fast,
                    "agent": agent,
                },
            )
            if response.status_code == 200:
                payload = response.json()
                return payload.get("model", OLLAMA_FALLBACK_MODEL), payload.get("reason", "routing")
    except Exception:
        pass

    return OLLAMA_FALLBACK_MODEL, "Fallback auf lokales Chat-Modell"


def _build_visible_reasoning_summary(
    *,
    agent: Optional[str],
    reasoning_mode: str,
    source_modes: List[str],
    web_search: bool,
    deep_research: bool,
    used_rag_context: bool,
    selected_model_reason: str,
    show_reasoning: bool,
) -> dict:
    source_trace = ["local-rag" if used_rag_context else "local-no-rag"]
    if web_search:
        source_trace.append("websearch-requested-not-yet-executed")
    if deep_research:
        source_trace.append("deep-research-requested-not-yet-executed")

    return {
        "agent": (agent or "kirobi").lower(),
        "reasoning_mode": reasoning_mode,
        "reasoning_label": _reasoning_mode_label(reasoning_mode),
        "show_reasoning": show_reasoning,
        "visible_reasoning_summary": [
            f"Agent-Persona: {(agent or 'kirobi').lower()}",
            f"Denkmodus: {_reasoning_mode_label(reasoning_mode)}",
            f"Quellenmodus: {', '.join(source_modes) if source_modes else 'local'}",
            f"Routing: {selected_model_reason}",
            "Hinweis: Es wird nur eine sichtbare Kurzspur gezeigt, keine rohe versteckte Chain-of-Thought.",
        ],
        "source_trace": source_trace,
    }


def _task_zone(metadata_value) -> str:
    metadata = _json_field(metadata_value, {})
    for key in ("zone", "input_zone", "output_zone"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value.upper()
    return "WORKSPACE"


def _operator_hint(status_value: str, last_error: Optional[str] = None) -> str:
    status = (status_value or "").lower()
    if status == "blocked":
        return last_error or "Human gate erforderlich: bitte Zone, Pfad oder Freigabe prüfen."
    if status == "dead_letter":
        return last_error or "Retry-Limit erreicht: Fehler triagieren und Task manuell neu einplanen."
    if status == "in_progress":
        return "Läuft lokal im Supervisor."
    if status == "completed":
        return "Lokal erfolgreich abgeschlossen."
    if status == "failed":
        return last_error or "Fehlgeschlagen: Ursache prüfen."
    return "Wartet auf lokale Supervisor-Ausführung."


def _upstream_detail(response: httpx.Response, fallback: str) -> str:
    try:
        data = response.json()
    except ValueError:
        return fallback
    return data.get("detail") or data.get("error") or fallback


def _normalize_zone(zone: Optional[str], *, default: Optional[str] = None) -> Optional[str]:
    normalized = (zone or default or "").strip().upper() or None
    if normalized is None:
        return None
    if normalized in MVP_REFUSED_ZONES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{normalized} is protected and not available in the MVP surface",
        )
    if normalized not in MVP_ALLOWED_ZONES:
        raise HTTPException(status_code=400, detail=f"Unsupported zone: {normalized}")
    return normalized


async def _resolve_zones_for_user(user_id: str, zone: Optional[str], permission_type: str = "read") -> List[str]:
    requested_zone = _normalize_zone(zone)
    async with db_pool.acquire() as conn:
        if requested_zone:
            row = await conn.fetchrow(
                "SELECT can_read, can_write FROM zone_permissions WHERE user_id = $1 AND zone = $2",
                user_id,
                requested_zone,
            )
            allowed = bool(row and row["can_read" if permission_type == "read" else "can_write"])
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No {permission_type} permission for zone {requested_zone}",
                )
            return [requested_zone]

        rows = await conn.fetch(
            "SELECT zone, can_read, can_write FROM zone_permissions WHERE user_id = $1",
            user_id,
        )

    column = "can_read" if permission_type == "read" else "can_write"
    allowed_zones = [
        row["zone"]
        for row in rows
        if row["zone"] in MVP_ALLOWED_ZONES and row[column]
    ]
    return allowed_zones or ["WORKSPACE"]


def _extract_text_payload(content: bytes, filename: str, mime_type: Optional[str]) -> tuple[Optional[str], str]:
    suffix = Path(filename).suffix.lower()
    is_text_like = (
        (mime_type or "").startswith("text/")
        or suffix in {".txt", ".md", ".markdown", ".json", ".csv", ".yaml", ".yml"}
    )
    if not is_text_like:
        return None, "metadata-only"

    text_content = content.decode("utf-8", errors="ignore").strip()
    if not text_content:
        return None, "metadata-only"
    return text_content[:20000], "local-search-ready"


def _upload_metadata(
    *,
    kind: str,
    original_filename: str,
    content_text: Optional[str],
    status_label: str,
    extra: Optional[dict] = None,
) -> dict:
    preview = (content_text or "").strip().replace("\n", " ")[:220]
    metadata = {
        "kind": kind,
        "ingest_status": status_label,
        "searchable": bool(content_text),
        "preview": preview,
        "title": original_filename,
    }
    if content_text:
        metadata["text_content"] = content_text
        metadata["char_count"] = len(content_text)
    if extra:
        metadata.update(extra)
    return metadata


async def _search_local_uploads(query: str, user_id: str, zones: List[str], limit: int) -> List[UISearchResult]:
    if not zones:
        return []

    pattern = f"%{query.strip()}%"
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, original_filename, file_path, zone, created_at, metadata
            FROM file_uploads
            WHERE user_id = $1
              AND zone = ANY($2::text[])
              AND (
                    original_filename ILIKE $3
                 OR COALESCE(metadata->>'title', '') ILIKE $3
                 OR COALESCE(metadata->>'preview', '') ILIKE $3
                 OR COALESCE(metadata->>'text_content', '') ILIKE $3
              )
            ORDER BY created_at DESC
            LIMIT $4
            """,
            user_id,
            zones,
            pattern,
            limit,
        )

    results: List[UISearchResult] = []
    lowered = query.lower()
    for row in rows:
        metadata = _json_field(row.get("metadata"), {})
        text_blob = " ".join(
            [
                row.get("original_filename", ""),
                metadata.get("title", ""),
                metadata.get("preview", ""),
                metadata.get("text_content", ""),
            ]
        ).lower()
        score = 0.65
        if lowered and lowered in text_blob:
            score = 0.82
        snippet = metadata.get("preview") or metadata.get("text_content") or row["original_filename"]
        results.append(
            UISearchResult(
                id=f"upload:{row['id']}",
                score=score,
                source=row["file_path"],
                zone=row["zone"],
                snippet=snippet[:280],
                title=metadata.get("title") or row["original_filename"],
                created_at=row["created_at"],
            )
        )
    return results


def _merge_search_results(*result_sets: List[UISearchResult], limit: int) -> List[UISearchResult]:
    merged: dict[str, UISearchResult] = {}
    for result_set in result_sets:
        for item in result_set:
            key = f"{item.zone}:{item.source}:{item.id}"
            current = merged.get(key)
            if current is None or item.score > current.score:
                merged[key] = item
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:limit]


def _is_mock_pool(pool: object) -> bool:
    return bool(getattr(pool, "_is_mock_object", False))


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    if not _is_mock_pool(db_pool):
        await _ensure_schema()
    yield
    # Shutdown
    await db_pool.close()


# FastAPI app
app = FastAPI(
    title="Kirobi API Service",
    description="Main API service for Kirobi family interactions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# `allow_origins=["*"]` together with `allow_credentials=True` is invalid per
# the CORS spec — browsers reject the preflight. We mirror the auth service
# logic and resolve a concrete origin list from KIROBI_PUBLIC_ORIGINS, falling
# back to a regex that covers localhost, *.local, RFC1918 LAN addresses and
# Tailscale's 100.64.0.0/10 CGNAT range.
def _cors_kwargs() -> dict:
    raw = os.getenv("KIROBI_PUBLIC_ORIGINS", "").strip()
    if raw:
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        return {"allow_origins": origins}
    pattern = (
        r"^https?://("
        r"localhost(:\d+)?|127\.0\.0\.1(:\d+)?|"
        r"[a-zA-Z0-9-]+\.local(:\d+)?|"
        r"10\.\d+\.\d+\.\d+(:\d+)?|"
        r"192\.168\.\d+\.\d+(:\d+)?|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?|"
        r"100\.(6[4-9]|[7-9]\d|1[0-1]\d|12[0-7])\.\d+\.\d+(:\d+)?"
        r")$"
    )
    return {"allow_origin_regex": pattern}


app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    max_age=3600,
)


# Dependency to get current user from auth service
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                return User(**user_data)
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")


async def check_zone_permission(user_id: str, zone: str, permission_type: str = "read") -> bool:
    """Check if user has permission for a specific zone"""
    # Whitelist to prevent SQL injection via permission_type
    if permission_type not in ("read", "write"):
        raise HTTPException(status_code=400, detail=f"Invalid permission_type: {permission_type}")
    column = "can_read" if permission_type == "read" else "can_write"
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            f"SELECT {column} FROM zone_permissions WHERE user_id = $1 AND zone = $2",
            user_id,
            zone
        )
        return bool(result and result[column])


async def _get_rag_context(
    query: str,
    user_id: str,
    zone: str = "WORKSPACE",
    *,
    family_private_approved: bool = False,
) -> str:
    """Holt Retrieval-Kontext und ergänzt lokales Upload-Wissen als Fallback."""
    parts: List[str] = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{RETRIEVAL_SERVICE_URL}/rag",
                json={
                    "query": query,
                    "zone": zone,
                    "limit": 3,
                    "family_private_approved": family_private_approved,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                context = data.get("context", "")
                if context:
                    parts.append(context)
    except Exception:
        pass

    local_results = await _search_local_uploads(query, user_id, [zone], limit=3)
    if local_results:
        local_context = "\n".join(
            f"- {item.title or item.source} [{item.zone}]: {item.snippet}"
            for item in local_results
        )
        parts.append(f"Lokale Upload-Treffer:\n{local_context}")

    return "\n\n".join(part for part in parts if part)


async def call_ollama(prompt: str, model: str = "llama3.1:8b", system_prompt: Optional[str] = None) -> str:
    """Call Ollama for LLM response"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async def _chat_once(model_name: str) -> httpx.Response:
                return await client.post(
                    f"{OLLAMA_HOST}/api/chat",
                    json={
                        "model": model_name,
                        "messages": messages,
                        "stream": False
                    }
                )

            response = await _chat_once(model)
            if response.status_code == 404 and model != OLLAMA_FALLBACK_MODEL:
                response = await _chat_once(OLLAMA_FALLBACK_MODEL)

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            return f"Error calling Ollama: {response.status_code}"
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"


async def call_ollama_stream(prompt: str, model: str = "llama3.1:8b", system_prompt: Optional[str] = None):
    """Stream Ollama chat tokens as they're produced. Yields plain text deltas."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload_for = lambda m: {"model": m, "messages": messages, "stream": True}

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
        async def _stream(model_name: str):
            async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload_for(model_name)) as resp:
                if resp.status_code != 200:
                    yield f"[Ollama error {resp.status_code}]"
                    return
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        yield delta
                    if chunk.get("done"):
                        return

        gen = _stream(model)
        first = True
        try:
            async for delta in gen:
                if first and delta.startswith("[Ollama error 404]") and model != OLLAMA_FALLBACK_MODEL:
                    async for delta2 in _stream(OLLAMA_FALLBACK_MODEL):
                        yield delta2
                    return
                first = False
                yield delta
        except Exception as exc:  # noqa: BLE001
            yield f"[Stream error: {exc}]"


def _extract_chat_prompt(request: ChatRequest) -> str:
    """Extract the latest user prompt from compatibility chat payloads."""
    if request.message and request.message.strip():
        return request.message.strip()

    if request.messages:
        for message in reversed(request.messages):
            if message.role == "user" and message.content.strip():
                return message.content.strip()

    raise HTTPException(status_code=422, detail="message or messages with user content required")


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "api"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/health/db")
async def health_db():
    """Dedicated DB health endpoint for dashboard/system probes."""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "db"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "service": "db", "error": str(exc)},
        )


@app.get("/health/qdrant")
async def health_qdrant():
    """Dedicated Qdrant health endpoint for dashboard/system probes."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections")
        if response.status_code == 200:
            return {"status": "healthy", "service": "qdrant"}
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "qdrant",
                "error": f"HTTP {response.status_code}",
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "service": "qdrant", "error": str(exc)},
        )


@app.post("/rag/search", response_model=UISearchResponse)
async def rag_search(
    request: UISearchRequest,
    current_user: User = Depends(get_current_user),
) -> UISearchResponse:
    """Compatibility search endpoint for the PWA search page."""
    requested_zone = _normalize_zone(request.zone)
    if requested_zone == "FAMILY_PRIVATE" and not request.family_private_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FAMILY_PRIVATE search requires explicit local human approval.",
        )
    zones = await _resolve_zones_for_user(current_user.id, request.zone, permission_type="read")
    if requested_zone is None:
        zones = [zone for zone in zones if zone != "FAMILY_PRIVATE"]
    retrieval_results: List[UISearchResult] = []
    retrieval_collection = "local-uploads"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for zone in zones:
                response = await client.post(
                    f"{RETRIEVAL_SERVICE_URL}/search",
                    json={
                        "query": request.query,
                        "zone": zone,
                        "limit": request.limit,
                        "score_threshold": request.score_threshold,
                        "family_private_approved": request.family_private_approved if zone == "FAMILY_PRIVATE" else False,
                    },
                )
                if response.status_code != 200:
                    if response.status_code < 500 and request.zone:
                        detail = _upstream_detail(response, "Search failed")
                        raise HTTPException(status_code=response.status_code, detail=detail)
                    continue

                payload = response.json()
                retrieval_collection = payload.get("collection", retrieval_collection)
                retrieval_results.extend(
                    UISearchResult(
                        id=str(item["id"]),
                        score=item["score"],
                        source=item.get("source") or "unknown",
                        zone=item.get("zone") or zone,
                        snippet=item.get("text", ""),
                        title=_search_title(item.get("source") or "unknown"),
                    )
                    for item in payload.get("results", [])
                )
    except HTTPException:
        raise
    except Exception:
        pass

    local_results = await _search_local_uploads(request.query, current_user.id, zones, request.limit)
    merged = _merge_search_results(retrieval_results, local_results, limit=request.limit)
    response_zone = requested_zone or ("MULTI" if len(zones) > 1 else (zones[0] if zones else "WORKSPACE"))
    collection = "multi-zone" if len(zones) > 1 else retrieval_collection
    return UISearchResponse(
        query=request.query,
        zone=response_zone,
        total=len(merged),
        collection=collection,
        local_only=True,
        approval_required=response_zone == "FAMILY_PRIVATE",
        family_private_approved=request.family_private_approved,
        refusal_semantics=(
            "family-private-requires-human-approval"
            if response_zone == "FAMILY_PRIVATE"
            else "zone-aware"
        ),
        results=merged,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_compat(request: ChatRequest):
    """Lightweight WORKSPACE chat endpoint for Voice/Desktop clients.

    This endpoint deliberately avoids persisted family conversations and private
    RAG zones. It gives local apps a stable `/chat` contract while the richer
    conversation API remains the source of truth for authenticated history.
    """
    prompt = _extract_chat_prompt(request)
    model = request.model or OLLAMA_FALLBACK_MODEL
    system_prompt = """Du bist KeyCodi im OpenDisruption-Ökosystem.

Antworte direkt, warm und präzise auf Deutsch. Nutze ausschließlich lokalen
WORKSPACE-Kontext aus dieser Anfrage. Greife nicht auf FAMILY_PRIVATE oder
SACRED Inhalte zu und erfinde keine privaten Details.

⚠️ ANTI-HALLUZINATION — STRIKT EINHALTEN:
- Sage NIEMALS etwas über Personen (Alter, Hobbys, Beruf, etc.) wenn du es nicht sicher weißt
- Wenn du etwas nicht weißt: "Das weiß ich nicht" — KEINE Vermutung, KEINE Schätzung
- Unsichere Aussagen mit [UNSICHER] kennzeichnen"""

    response = await call_ollama(prompt, model=model, system_prompt=system_prompt)
    await _analytics_track("chat_compat", zone="WORKSPACE", model=model)
    return ChatResponse(
        message=response,
        response=response,
        content=response,
        model_used=model,
    )


@app.get("/chat/runtime/options", response_model=ChatRuntimeOptions)
async def chat_runtime_options(
    _current_user: User = Depends(get_current_user),
) -> ChatRuntimeOptions:
    return await _chat_runtime_options_payload()


@app.get("/conversations", response_model=List[Conversation])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    archived: bool = False,
    limit: int = 100
):
    """List all conversations for current user"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, title, zone, created_at, updated_at, archived
            FROM conversations
            WHERE user_id = $1 AND archived = $2
            ORDER BY updated_at DESC
            LIMIT $3
            """,
            current_user.id,
            archived,
            limit,
        )
        return [Conversation(**dict(row)) for row in rows]


@app.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    conversation_data.zone = _normalize_zone(conversation_data.zone, default="FAMILY_PRIVATE")
    # Check zone permission
    if not await check_zone_permission(current_user.id, conversation_data.zone, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No write permission for zone {conversation_data.zone}"
        )

    conversation_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, title, zone)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id,
            current_user.id,
            conversation_data.title,
            conversation_data.zone
        )

        row = await conn.fetchrow(
            "SELECT id, user_id, title, zone, created_at, updated_at, archived FROM conversations WHERE id = $1",
            conversation_id
        )
        return Conversation(**dict(row))


@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, title, zone, created_at, updated_at, archived
            FROM conversations
            WHERE id = $1 AND user_id = $2
            """,
            conversation_id,
            current_user.id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return Conversation(**dict(row))


@app.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """List messages in a conversation"""
    # Verify conversation ownership
    conversation = await get_conversation(conversation_id, current_user)

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, conversation_id, user_id, role, content, model_used, tokens_used, attachments, metadata, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            conversation_id,
            limit
        )
        return [_message_from_row(row) for row in rows]


@app.post("/conversations/{conversation_id}/messages", response_model=Message)
async def create_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message in a conversation and get AI response"""
    # Verify conversation ownership
    conversation = await get_conversation(conversation_id, current_user)

    # Save user message
    message_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        user_message_metadata = {
            "agent": (message_data.agent or "kirobi").lower(),
            "reasoning_mode": message_data.reasoning_mode,
            "source_modes": message_data.source_modes,
            "web_search": message_data.web_search,
            "deep_research": message_data.deep_research,
            "show_reasoning": message_data.show_reasoning,
        }
        serialized_metadata = json.dumps(user_message_metadata)
        serialized_attachments = json.dumps(message_data.attachments or [])
        if message_data.attachments:
            await conn.execute(
                """
                INSERT INTO messages (id, conversation_id, user_id, role, content, attachments, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                message_id,
                conversation_id,
                current_user.id,
                "user",
                message_data.content,
                serialized_attachments,
                serialized_metadata,
            )
        else:
            await conn.execute(
                """
                INSERT INTO messages (id, conversation_id, user_id, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                message_id,
                conversation_id,
                current_user.id,
                "user",
                message_data.content,
                serialized_metadata,
            )

        # Get conversation history for context
        history = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT 20
            """,
            conversation_id
        )

    # Load user profile for personalized response
    profile_path = f"/canon/family/{current_user.username}-profile.md"
    system_prompt = f"""Du bist Kirobi, ein persönlicher KI-Assistent für die Familie Darusi.

Du sprichst mit: {current_user.display_name} ({current_user.username})
Zone: {conversation.zone}

Sei persönlich, hilfsbereit und respektiere die Privatsphäre der Familie.
Antworte auf Deutsch und passe deinen Tonfall an den Nutzer an."""
    system_prompt = f"{_agent_prompt(message_data.agent)}\nDenkmodus: {_reasoning_mode_label(message_data.reasoning_mode)}.\nQuellenmodus: {', '.join(message_data.source_modes) if message_data.source_modes else 'local'}.\n{system_prompt}"
    if message_data.system_prompt_extra:
        system_prompt = f"{system_prompt}\n\nZusaetzliche Stilvorgabe:\n{message_data.system_prompt_extra}"

    # RAG-Kontext aus Wissensbasis holen (Zone: WORKSPACE für allgemeine Anfragen)
    rag_zone = conversation.zone if conversation.zone in ("PUBLIC", "WORKSPACE", "FAMILY_PRIVATE") else "WORKSPACE"
    rag_context = await _get_rag_context(
        message_data.content,
        current_user.id,
        zone=rag_zone,
        family_private_approved=conversation.zone == "FAMILY_PRIVATE",
    )
    if rag_context:
        system_prompt = f"Relevanter Kontext aus der Wissensbasis:\n{rag_context}\n\n{system_prompt}"

    # Call Ollama for response
    default_model = "llama3.1:70b" if current_user.role == "admin" else "llama3.1:8b"
    model, model_reason = await _select_chat_model(
        message_data.model,
        reasoning_mode=message_data.reasoning_mode,
        deep_research=message_data.deep_research,
        agent=message_data.agent,
    )
    if not model:
        model = default_model

    ai_response = await call_ollama(message_data.content, model=model, system_prompt=system_prompt)
    assistant_metadata = _build_visible_reasoning_summary(
        agent=message_data.agent,
        reasoning_mode=message_data.reasoning_mode,
        source_modes=message_data.source_modes,
        web_search=message_data.web_search,
        deep_research=message_data.deep_research,
        used_rag_context=bool(rag_context),
        selected_model_reason=model_reason,
        show_reasoning=message_data.show_reasoning,
    )

    # Save AI response
    ai_message_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, model_used, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            ai_message_id,
            conversation_id,
            "assistant",
            ai_response,
            model,
            json.dumps(assistant_metadata),
        )
        asyncio.create_task(_analytics_track("conversation", zone=conversation.zone, model=model))

        # Update conversation timestamp
        await conn.execute(
            "UPDATE conversations SET updated_at = NOW() WHERE id = $1",
            conversation_id
        )

        # Return AI message
        row = await conn.fetchrow(
            """
            SELECT id, conversation_id, user_id, role, content, model_used, tokens_used, attachments, metadata, created_at
            FROM messages WHERE id = $1
            """,
            ai_message_id
        )
        return _message_from_row(row)


@app.post("/conversations/{conversation_id}/messages/stream")
async def create_message_stream(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    """Stream a chat reply token-by-token via SSE.

    Persists the user message immediately and the assistant message at the end.
    Each SSE event is JSON-encoded with one of these shapes:
      data: {"event":"start","model":"..."}
      data: {"event":"delta","text":"..."}
      data: {"event":"done","message_id":"...","model":"...","content":"..."}
      data: {"event":"error","detail":"..."}
    """
    conversation = await get_conversation(conversation_id, current_user)

    # Persist user message + load history (mirrors create_message)
    user_message_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        user_message_metadata = {
            "agent": (message_data.agent or "kirobi").lower(),
            "reasoning_mode": message_data.reasoning_mode,
            "source_modes": message_data.source_modes,
            "web_search": message_data.web_search,
            "deep_research": message_data.deep_research,
            "show_reasoning": message_data.show_reasoning,
            "stream": True,
        }
        await conn.execute(
            """
            INSERT INTO messages (id, conversation_id, user_id, role, content, attachments, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_message_id,
            conversation_id,
            current_user.id,
            "user",
            message_data.content,
            json.dumps(message_data.attachments or []),
            json.dumps(user_message_metadata),
        )

    # Build system prompt (same logic as create_message)
    system_prompt = f"""Du bist Kirobi, ein persönlicher KI-Assistent für die Familie Darusi.

Du sprichst mit: {current_user.display_name} ({current_user.username})
Zone: {conversation.zone}

Sei persönlich, hilfsbereit und respektiere die Privatsphäre der Familie.
Antworte auf Deutsch und passe deinen Tonfall an den Nutzer an."""
    system_prompt = (
        f"{_agent_prompt(message_data.agent)}\n"
        f"Denkmodus: {_reasoning_mode_label(message_data.reasoning_mode)}.\n"
        f"Quellenmodus: {', '.join(message_data.source_modes) if message_data.source_modes else 'local'}.\n"
        f"{system_prompt}"
    )
    if message_data.system_prompt_extra:
        system_prompt = f"{system_prompt}\n\nZusaetzliche Stilvorgabe:\n{message_data.system_prompt_extra}"

    rag_zone = conversation.zone if conversation.zone in ("PUBLIC", "WORKSPACE", "FAMILY_PRIVATE") else "WORKSPACE"
    rag_context = await _get_rag_context(
        message_data.content,
        current_user.id,
        zone=rag_zone,
        family_private_approved=conversation.zone == "FAMILY_PRIVATE",
    )
    if rag_context:
        system_prompt = f"Relevanter Kontext aus der Wissensbasis:\n{rag_context}\n\n{system_prompt}"

    default_model = "llama3.1:70b" if current_user.role == "admin" else "llama3.1:8b"
    model, model_reason = await _select_chat_model(
        message_data.model,
        reasoning_mode=message_data.reasoning_mode,
        deep_research=message_data.deep_research,
        agent=message_data.agent,
    )
    if not model:
        model = default_model

    async def event_stream():
        accumulated_parts: List[str] = []
        try:
            yield f"data: {json.dumps({'event': 'start', 'model': model})}\n\n"
            async for delta in call_ollama_stream(message_data.content, model=model, system_prompt=system_prompt):
                accumulated_parts.append(delta)
                yield f"data: {json.dumps({'event': 'delta', 'text': delta})}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"

        full_content = "".join(accumulated_parts).strip() or "[leere Antwort]"
        ai_message_id = str(uuid.uuid4())
        try:
            assistant_metadata = _build_visible_reasoning_summary(
                agent=message_data.agent,
                reasoning_mode=message_data.reasoning_mode,
                source_modes=message_data.source_modes,
                web_search=message_data.web_search,
                deep_research=message_data.deep_research,
                used_rag_context=bool(rag_context),
                selected_model_reason=model_reason,
                show_reasoning=message_data.show_reasoning,
            )
            assistant_metadata["stream"] = True
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, model_used, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    ai_message_id,
                    conversation_id,
                    "assistant",
                    full_content,
                    model,
                    json.dumps(assistant_metadata),
                )
                await conn.execute(
                    "UPDATE conversations SET updated_at = NOW() WHERE id = $1",
                    conversation_id,
                )
            asyncio.create_task(_analytics_track("conversation", zone=conversation.zone, model=model))
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'event': 'error', 'detail': f'persist failed: {exc}'})}\n\n"

        yield f"data: {json.dumps({'event': 'done', 'message_id': ai_message_id, 'model': model, 'content': full_content})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    zone: str = Form("FAMILY_PRIVATE"),
    human_approved: bool = Form(False),
    approval_note: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a file (image, document, etc.)"""
    zone = _normalize_zone(zone, default="FAMILY_PRIVATE")
    # Check zone permission
    if not await check_zone_permission(current_user.id, zone, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No write permission for zone {zone}"
        )
    trust_metadata = _upload_policy_metadata(
        zone,
        human_approved=human_approved,
        approval_note=approval_note,
    )

    # Create user-specific upload directory
    user_upload_dir = UPLOAD_DIR / current_user.username / zone.lower()
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = user_upload_dir / unique_filename

    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        file_size = len(content)
        text_content, ingest_status = _extract_text_payload(content, file.filename, file.content_type)
        metadata = _upload_metadata(
            kind="file",
            original_filename=file.filename,
            content_text=text_content,
            status_label=ingest_status,
            extra={
                "mime_type": file.content_type or "application/octet-stream",
                **trust_metadata,
            },
        )

        # Save to database
        file_id = str(uuid.uuid4())
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO file_uploads (id, user_id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                file_id,
                current_user.id,
                unique_filename,
                file.filename,
                str(file_path),
                file_size,
                file.content_type,
                zone,
                bool(text_content),
                json.dumps(metadata),
            )

            row = await conn.fetchrow(
                "SELECT id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata, created_at FROM file_uploads WHERE id = $1",
                file_id
            )

        asyncio.create_task(_analytics_track("upload", zone=zone, model="local-file"))
        return _upload_from_row(row)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.post("/uploads/text", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_text(
    payload: TextUploadCreate,
    current_user: User = Depends(get_current_user),
):
    """Persist a text snippet as a local-first knowledge upload."""
    zone = _normalize_zone(payload.zone, default="WORKSPACE")
    if not await check_zone_permission(current_user.id, zone, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No write permission for zone {zone}",
        )
    trust_metadata = _upload_policy_metadata(
        zone,
        human_approved=payload.human_approved,
        approval_note=payload.approval_note,
    )

    user_upload_dir = UPLOAD_DIR / current_user.username / zone.lower()
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    slug = (payload.title or "notiz").strip().replace("/", "-")[:40] or "notiz"
    unique_filename = f"{uuid.uuid4()}-{slug}.txt"
    file_path = user_upload_dir / unique_filename
    content = payload.content.strip()
    metadata = _upload_metadata(
        kind="text",
        original_filename=payload.title or "Schnellnotiz",
        content_text=content[:20000],
        status_label="local-search-ready",
        extra={"source": "pwa-text-upload", **trust_metadata},
    )

    async with aiofiles.open(file_path, "w", encoding="utf-8") as handle:
        await handle.write(content)

    file_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO file_uploads (id, user_id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            file_id,
            current_user.id,
            unique_filename,
            payload.title or "Schnellnotiz",
            str(file_path),
            len(content.encode("utf-8")),
            "text/plain",
            zone,
            True,
            json.dumps(metadata),
        )
        row = await conn.fetchrow(
            "SELECT id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata, created_at FROM file_uploads WHERE id = $1",
            file_id,
        )

    asyncio.create_task(_analytics_track("text_upload", zone=zone, model="local-text"))
    return _upload_from_row(row)


@app.get("/uploads", response_model=List[FileUploadResponse])
async def list_uploads(
    zone: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List uploaded files for current user"""
    zone = _normalize_zone(zone) if zone else None
    if zone and not await check_zone_permission(current_user.id, zone, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No read permission for zone {zone}",
        )
    async with db_pool.acquire() as conn:
        if zone:
            rows = await conn.fetch(
                """
                SELECT id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata, created_at
                FROM file_uploads
                WHERE user_id = $1 AND zone = $2
                ORDER BY created_at DESC
                """,
                current_user.id,
                zone
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, filename, original_filename, file_path, file_size, mime_type, zone, processed, metadata, created_at
                FROM file_uploads
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                current_user.id
            )

        return [_upload_from_row(row) for row in rows]


@app.get("/uploads/{file_id}/download")
async def download_upload(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download a previously uploaded file owned by the current user."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, filename, original_filename, file_path, file_size, mime_type, zone, created_at
            FROM file_uploads
            WHERE id = $1 AND user_id = $2
            """,
            file_id,
            current_user.id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")

    if not await check_zone_permission(current_user.id, row["zone"], "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No read permission for zone {row['zone']}",
        )

    file_path = _safe_upload_path(row["file_path"])
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")

    return FileResponse(
        path=file_path,
        filename=row["original_filename"],
        media_type=row["mime_type"] or "application/octet-stream",
    )


@app.get("/tasks", response_model=DashboardTasksResponse)
async def list_dashboard_tasks(limit: int = 50) -> DashboardTasksResponse:
    """Read-only dashboard task feed backed by supervisor_tasks."""
    async with db_pool.acquire() as conn:
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'supervisor_tasks'
            )
            """
        )
        if not table_exists:
            return DashboardTasksResponse(tasks=[])

        try:
            rows = await conn.fetch(
                """
                SELECT id, name, description, status, priority, assigned_agent, created_at, updated_at, metadata, last_error
                FROM supervisor_tasks
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
        except asyncpg.exceptions.UndefinedColumnError:
            rows = await conn.fetch(
                """
                SELECT id, name, description, status, priority, assigned_agent, created_at, updated_at, metadata, NULL::text AS last_error
                FROM supervisor_tasks
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

    return DashboardTasksResponse(
        tasks=[
            DashboardTask(
                id=row["id"],
                title=row["name"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                agent=row["assigned_agent"],
                zone=_task_zone(row["metadata"]),
                last_error=row["last_error"],
                operator_hint=_operator_hint(row["status"], row["last_error"]),
            )
            for row in rows
        ]
    )


@app.get("/dashboard/activity", response_model=DashboardActivityResponse)
async def dashboard_activity(limit: int = 12) -> DashboardActivityResponse:
    """Summarise recent auth + knowledge activity for the admin dashboard."""
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM (
                    SELECT
                        'auth:' || id::text AS id,
                        created_at,
                        'auth' AS surface,
                        action AS kind,
                        COALESCE(details->>'username', user_id, 'system') AS actor,
                        CASE
                            WHEN action = 'login' THEN 'Lokaler Login'
                            WHEN action = 'logout' THEN 'Abmeldung'
                            WHEN action = 'change_password' THEN 'Passwort geändert'
                            WHEN action = 'register' THEN 'Benutzer angelegt'
                            ELSE action
                        END AS summary,
                        NULL::text AS zone
                    FROM audit_log
                    UNION ALL
                    SELECT
                        'upload:' || f.id AS id,
                        f.created_at,
                        'knowledge' AS surface,
                        CASE WHEN f.processed THEN 'indexed_upload' ELSE 'upload' END AS kind,
                        COALESCE(u.display_name, u.username, f.user_id) AS actor,
                        'Upload: ' || f.original_filename AS summary,
                        f.zone
                    FROM file_uploads f
                    LEFT JOIN users u ON u.id = f.user_id
                    UNION ALL
                    SELECT
                        'conversation:' || c.id AS id,
                        c.updated_at AS created_at,
                        'chat' AS surface,
                        'conversation' AS kind,
                        COALESCE(u.display_name, u.username, c.user_id) AS actor,
                        'Gespräch aktiv: ' || COALESCE(NULLIF(c.title, ''), 'Neues Gespräch') AS summary,
                        c.zone
                    FROM conversations c
                    LEFT JOIN users u ON u.id = c.user_id
                ) activity
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
    except Exception:
        return DashboardActivityResponse(items=[])

    return DashboardActivityResponse(
        items=[
            DashboardActivityItem(
                id=row["id"],
                surface=row["surface"],
                kind=row["kind"],
                actor=row["actor"],
                summary=row["summary"],
                zone=row["zone"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
    )


@app.get("/control/status", response_model=OperatorControlStatus)
async def operator_control_status() -> OperatorControlStatus:
    """Operator-facing local control summary for the dashboard MVP."""
    default_guidance = [
        "Autonomie bleibt lokal und deterministisch; keine Cloud-Routing-Entscheidung im Supervisor.",
        "FAMILY_PRIVATE, QUARANTINE und SACRED bleiben human-gated und werden fail-closed geblockt.",
        "Das Dashboard-Proxy erlaubt nur read-only Status- und Kontrollpfade.",
    ]

    async with db_pool.acquire() as conn:
        tasks_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'supervisor_tasks'
            )
            """
        )
        events_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'supervisor_events'
            )
            """
        )

        if not tasks_exists and not events_exists:
            return OperatorControlStatus(
                supervisorAvailable=False,
                autonomousMode="local-only-deterministic",
                humanGateZones=["FAMILY_PRIVATE", "QUARANTINE", "SACRED"],
                queueDepth=0,
                pendingTasks=0,
                activeTasks=0,
                completedTasks=0,
                blockedTasks=0,
                deadLetterTasks=0,
                attentionRequired=0,
                operatorGuidance=[
                    "Supervisor noch nicht initialisiert: starte den lokalen Supervisor für Live-Kontrolle.",
                    *default_guidance,
                ],
            )

        counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
            "dead_letter": 0,
        }
        attention_rows = []
        if tasks_exists:
            counts_row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                    COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
                    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                    COUNT(*) FILTER (WHERE status = 'blocked') AS blocked,
                    COUNT(*) FILTER (WHERE status = 'dead_letter') AS dead_letter
                FROM supervisor_tasks
                """
            )
            if counts_row:
                counts.update({key: counts_row[key] or 0 for key in counts})
            try:
                attention_rows = await conn.fetch(
                    """
                    SELECT id, name, status, priority, assigned_agent, metadata, last_error
                    FROM supervisor_tasks
                    WHERE status IN ('blocked', 'dead_letter', 'pending', 'in_progress')
                    ORDER BY
                        CASE status
                            WHEN 'blocked' THEN 0
                            WHEN 'dead_letter' THEN 1
                            WHEN 'in_progress' THEN 2
                            ELSE 3
                        END,
                        updated_at DESC,
                        created_at DESC
                    LIMIT 5
                    """
                )
            except asyncpg.exceptions.UndefinedColumnError:
                attention_rows = await conn.fetch(
                    """
                    SELECT id, name, status, priority, assigned_agent, metadata, NULL::text AS last_error
                    FROM supervisor_tasks
                    WHERE status IN ('blocked', 'dead_letter', 'pending', 'in_progress')
                    ORDER BY
                        CASE status
                            WHEN 'blocked' THEN 0
                            WHEN 'dead_letter' THEN 1
                            WHEN 'in_progress' THEN 2
                            ELSE 3
                        END,
                        updated_at DESC,
                        created_at DESC
                    LIMIT 5
                    """
                )

        recent_rows = []
        health_row = None
        if events_exists:
            recent_rows = await conn.fetch(
                """
                SELECT timestamp, event_type, severity, message
                FROM supervisor_events
                ORDER BY timestamp DESC
                LIMIT 6
                """
            )
            health_row = await conn.fetchrow(
                """
                SELECT timestamp, metadata
                FROM supervisor_events
                WHERE event_type = 'health_check'
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )

    health = _json_field(health_row["metadata"], {}) if health_row else {}
    unhealthy = [
        name
        for name, value in health.items()
        if isinstance(value, str) and value not in {"healthy", "unknown"}
    ]

    guidance = list(default_guidance)
    if counts["blocked"]:
        guidance.insert(0, f"{counts['blocked']} Task(s) warten auf Operator-Freigabe oder Policy-Triage.")
    if counts["dead_letter"]:
        guidance.insert(0, f"{counts['dead_letter']} Task(s) sind im Dead-Letter und brauchen manuelles Requeue.")
    if unhealthy:
        guidance.insert(0, f"Unhealthy Services laut letztem Supervisor-Check: {', '.join(unhealthy)}.")

    return OperatorControlStatus(
        supervisorAvailable=bool(tasks_exists or events_exists),
        autonomousMode="local-only-deterministic",
        humanGateZones=["FAMILY_PRIVATE", "QUARANTINE", "SACRED"],
        queueDepth=counts["pending"] + counts["in_progress"] + counts["blocked"],
        pendingTasks=counts["pending"],
        activeTasks=counts["in_progress"],
        completedTasks=counts["completed"],
        blockedTasks=counts["blocked"],
        deadLetterTasks=counts["dead_letter"],
        attentionRequired=counts["blocked"] + counts["dead_letter"],
        lastEventAt=recent_rows[0]["timestamp"] if recent_rows else None,
        lastHealthCheckAt=health_row["timestamp"] if health_row else None,
        health=health,
        recentEvents=[
            ControlEvent(
                timestamp=row["timestamp"],
                event_type=row["event_type"],
                severity=row["severity"],
                message=row["message"],
            )
            for row in recent_rows
        ],
        attentionTasks=[
            ControlActionItem(
                id=row["id"],
                title=row["name"],
                status=row["status"],
                priority=row["priority"],
                agent=row["assigned_agent"],
                zone=_task_zone(row["metadata"]),
                last_error=row["last_error"],
                operator_hint=_operator_hint(row["status"], row["last_error"]),
            )
            for row in attention_rows
        ],
        operatorGuidance=guidance,
    )


# ============================================================================
# USER-SPACE & FAMILY-SPACE — filesystem-backed personal/shared notes
# ============================================================================

USERSPACE_ROOT = Path(os.getenv("KIROBI_USERSPACE_ROOT", "/data/experiences/users"))
FAMILY_SPACE_ROOT = Path(os.getenv("KIROBI_FAMILY_SPACE_ROOT", "/data/experiences/family"))
_USERSPACE_NAME_RE = __import__("re").compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
_USERSPACE_ALLOWED_EXTS = {".md", ".txt", ".json"}


class UserspaceNote(BaseModel):
    name: str
    size: int
    modified: str
    space: str  # "user" or "family"


class UserspaceWriteRequest(BaseModel):
    content: str = Field(..., max_length=512_000)


def _safe_username(username: str) -> str:
    norm = username.strip().lower()
    if not _USERSPACE_NAME_RE.match(norm):
        raise HTTPException(status_code=400, detail=f"invalid username: {username!r}")
    return norm


def _safe_note_name(name: str) -> str:
    name = name.strip()
    if not _USERSPACE_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="invalid note name (alnum, .-_, max 100)")
    if Path(name).suffix.lower() not in _USERSPACE_ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"unsupported extension; allowed: {sorted(_USERSPACE_ALLOWED_EXTS)}")
    return name


def _user_dir(username: str) -> Path:
    safe = _safe_username(username)
    base = USERSPACE_ROOT / safe
    base.mkdir(parents=True, exist_ok=True)
    return base


def _list_notes(directory: Path, space: str) -> List[UserspaceNote]:
    if not directory.exists():
        return []
    out: List[UserspaceNote] = []
    for p in sorted(directory.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in _USERSPACE_ALLOWED_EXTS:
            continue
        if p.name == "README.md":
            continue
        try:
            stat = p.stat()
        except OSError:
            continue
        out.append(UserspaceNote(
            name=p.name,
            size=stat.st_size,
            modified=datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
            space=space,
        ))
    return out


@app.get("/userspace/notes", response_model=List[UserspaceNote], tags=["userspace"])
async def list_user_notes(current_user: User = Depends(get_current_user)):
    """List notes in the current user's personal space."""
    return _list_notes(_user_dir(current_user.username), "user")


@app.get("/userspace/notes/{name}", tags=["userspace"])
async def read_user_note(name: str, current_user: User = Depends(get_current_user)):
    safe = _safe_note_name(name)
    path = _user_dir(current_user.username) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="note not found")
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"read failed: {exc}")
    return {"name": safe, "content": content, "space": "user"}


@app.put("/userspace/notes/{name}", response_model=UserspaceNote, tags=["userspace"])
async def write_user_note(
    name: str,
    body: UserspaceWriteRequest,
    current_user: User = Depends(get_current_user),
):
    safe = _safe_note_name(name)
    path = _user_dir(current_user.username) / safe
    path.write_text(body.content, encoding="utf-8")
    stat = path.stat()
    return UserspaceNote(
        name=safe, size=stat.st_size,
        modified=datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        space="user",
    )


@app.delete("/userspace/notes/{name}", status_code=204, tags=["userspace"])
async def delete_user_note(name: str, current_user: User = Depends(get_current_user)):
    safe = _safe_note_name(name)
    path = _user_dir(current_user.username) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="note not found")
    path.unlink()
    return None


@app.get("/family-space/notes", response_model=List[UserspaceNote], tags=["family-space"])
async def list_family_notes(current_user: User = Depends(get_current_user)):
    if not await check_zone_permission(current_user.id, "FAMILY_PRIVATE", "read"):
        raise HTTPException(status_code=403, detail="missing FAMILY_PRIVATE read permission")
    return _list_notes(FAMILY_SPACE_ROOT, "family")


@app.get("/family-space/notes/{name}", tags=["family-space"])
async def read_family_note(name: str, current_user: User = Depends(get_current_user)):
    if not await check_zone_permission(current_user.id, "FAMILY_PRIVATE", "read"):
        raise HTTPException(status_code=403, detail="missing FAMILY_PRIVATE read permission")
    safe = _safe_note_name(name)
    path = FAMILY_SPACE_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="note not found")
    return {"name": safe, "content": path.read_text(encoding="utf-8"), "space": "family"}


@app.put("/family-space/notes/{name}", response_model=UserspaceNote, tags=["family-space"])
async def write_family_note(
    name: str,
    body: UserspaceWriteRequest,
    current_user: User = Depends(get_current_user),
):
    if not await check_zone_permission(current_user.id, "FAMILY_PRIVATE", "write"):
        raise HTTPException(status_code=403, detail="missing FAMILY_PRIVATE write permission")
    safe = _safe_note_name(name)
    FAMILY_SPACE_ROOT.mkdir(parents=True, exist_ok=True)
    path = FAMILY_SPACE_ROOT / safe
    path.write_text(body.content, encoding="utf-8")
    stat = path.stat()
    return UserspaceNote(
        name=safe, size=stat.st_size,
        modified=datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        space="family",
    )


@app.delete("/family-space/notes/{name}", status_code=204, tags=["family-space"])
async def delete_family_note(name: str, current_user: User = Depends(get_current_user)):
    if not await check_zone_permission(current_user.id, "FAMILY_PRIVATE", "write"):
        raise HTTPException(status_code=403, detail="missing FAMILY_PRIVATE write permission")
    safe = _safe_note_name(name)
    path = FAMILY_SPACE_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="note not found")
    path.unlink()
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("BIND_HOST", "127.0.0.1"), port=8000)
