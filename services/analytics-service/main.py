from __future__ import annotations

"""
Kirobi Analytics Service
Zone: WORKSPACE
Purpose: Event tracking, usage statistics, and zone/model analytics
Port: 8010
"""

import os
import json
from datetime import datetime, date
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
import asyncpg
from dotenv import load_dotenv
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)

# Database connection pool (module-level, set during lifespan)
db_pool: Optional[asyncpg.Pool] = None

# ---------------------------------------------------------------------------
# DB Schema
# ---------------------------------------------------------------------------
ANALYTICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS analytics_events (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    user_id     TEXT,
    zone        TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS analytics_events_type_idx
    ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS analytics_events_created_idx
    ON analytics_events(created_at DESC);
CREATE INDEX IF NOT EXISTS analytics_events_user_idx
    ON analytics_events(user_id);
"""


async def _ensure_schema() -> None:
    """Create analytics tables idempotently on first boot."""
    async with db_pool.acquire() as conn:
        await conn.execute(ANALYTICS_SCHEMA)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=200)
    user_id: Optional[str] = None
    zone: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: int
    event_type: str
    user_id: Optional[str]
    zone: Optional[str]
    metadata: dict
    created_at: datetime


class EventTypeCount(BaseModel):
    event_type: str
    count: int


class ZoneStats(BaseModel):
    zone: str
    read_count: int
    write_count: int
    total_count: int


class ModelUsage(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_used: str
    usage_count: int


class DailyStats(BaseModel):
    date: str
    total_events: int
    active_users: int
    events_by_type: List[EventTypeCount]
    zones: List[dict]


class DashboardStats(BaseModel):
    eventsToday: int
    activeUsers: int
    zoneUsage: dict[str, int]
    totalConversations: int
    totalMessages: int


# ---------------------------------------------------------------------------
# CORS helper (mirrors auth/api pattern — no wildcard with credentials)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    await _ensure_schema()
    yield
    await db_pool.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Kirobi Analytics Service",
    description="Event tracking and usage statistics for the Kirobi ecosystem",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    max_age=3600,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _parse_metadata(value: Any) -> dict:
    """Safely coerce asyncpg JSONB result to a plain dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _event_from_row(row: asyncpg.Record) -> EventResponse:
    data = dict(row)
    data["metadata"] = _parse_metadata(data.get("metadata"))
    return EventResponse(**data)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check with DB connectivity verification."""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "analytics"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


@app.post("/events", response_model=EventResponse, status_code=201)
async def track_event(event: EventCreate):
    """Track a new analytics event.

    Stores event_type, optional user_id, optional zone, and arbitrary
    metadata (JSONB). No SACRED or FAMILY_PRIVATE content should be
    placed in metadata — callers are responsible for sanitisation.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO analytics_events (event_type, user_id, zone, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id, event_type, user_id, zone, metadata, created_at
            """,
            event.event_type,
            event.user_id,
            event.zone,
            json.dumps(event.metadata),
        )
    return _event_from_row(row)


@app.get("/events", response_model=List[EventResponse])
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    zone: Optional[str] = Query(None, description="Filter by zone"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Query analytics events with optional filters."""
    conditions: List[str] = []
    params: List[Any] = []
    idx = 1

    if event_type is not None:
        conditions.append(f"event_type = ${idx}")
        params.append(event_type)
        idx += 1
    if zone is not None:
        conditions.append(f"zone = ${idx}")
        params.append(zone)
        idx += 1
    if user_id is not None:
        conditions.append(f"user_id = ${idx}")
        params.append(user_id)
        idx += 1

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.extend([limit, offset])

    query = f"""
        SELECT id, event_type, user_id, zone, metadata, created_at
        FROM analytics_events
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [_event_from_row(row) for row in rows]


@app.get("/stats", response_model=DashboardStats)
async def dashboard_stats():
    """Dashboard summary shaped for the Next.js admin UI."""
    today = date.today()

    async with db_pool.acquire() as conn:
        summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) AS active_users
            FROM analytics_events
            WHERE created_at::date = $1
            """,
            today,
        )
        zone_rows = await conn.fetch(
            """
            SELECT zone, COUNT(*) AS count
            FROM analytics_events
            WHERE created_at::date = $1 AND zone IS NOT NULL
            GROUP BY zone
            ORDER BY count DESC
            """,
            today,
        )
        conversations_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'conversations'
            )
            """
        )
        messages_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'messages'
            )
            """
        )

        total_conversations = (
            await conn.fetchval("SELECT COUNT(*) FROM conversations")
            if conversations_exists
            else 0
        )
        total_messages = (
            await conn.fetchval("SELECT COUNT(*) FROM messages")
            if messages_exists
            else 0
        )

    return DashboardStats(
        eventsToday=summary["total_events"] if summary else 0,
        activeUsers=summary["active_users"] if summary else 0,
        zoneUsage={row["zone"]: row["count"] for row in zone_rows},
        totalConversations=total_conversations,
        totalMessages=total_messages,
    )


@app.get("/stats/daily", response_model=DailyStats)
async def daily_stats(
    target_date: Optional[str] = Query(
        None,
        alias="date",
        description="ISO date (YYYY-MM-DD). Defaults to today.",
    )
):
    """Daily statistics: total events, active users, events per type, zone breakdown."""
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        parsed_date = date.today()

    date_str = parsed_date.isoformat()

    async with db_pool.acquire() as conn:
        # Total events and active users for the day
        summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                    AS total_events,
                COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) AS active_users
            FROM analytics_events
            WHERE created_at::date = $1
            """,
            parsed_date,
        )

        # Events per type
        type_rows = await conn.fetch(
            """
            SELECT event_type, COUNT(*) AS count
            FROM analytics_events
            WHERE created_at::date = $1
            GROUP BY event_type
            ORDER BY count DESC
            """,
            parsed_date,
        )

        # Zone breakdown
        zone_rows = await conn.fetch(
            """
            SELECT zone, COUNT(*) AS count
            FROM analytics_events
            WHERE created_at::date = $1 AND zone IS NOT NULL
            GROUP BY zone
            ORDER BY count DESC
            """,
            parsed_date,
        )

    return DailyStats(
        date=date_str,
        total_events=summary["total_events"],
        active_users=summary["active_users"],
        events_by_type=[
            EventTypeCount(event_type=r["event_type"], count=r["count"])
            for r in type_rows
        ],
        zones=[{"zone": r["zone"], "count": r["count"]} for r in zone_rows],
    )


@app.get("/stats/zones", response_model=List[ZoneStats])
async def zone_stats():
    """Zone usage: read/write counts per zone derived from analytics events.

    Reads events where event_type contains 'read' or 'write' (case-insensitive)
    and groups them by zone.
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                zone,
                COUNT(*) FILTER (WHERE event_type ILIKE '%read%')  AS read_count,
                COUNT(*) FILTER (WHERE event_type ILIKE '%write%') AS write_count,
                COUNT(*)                                            AS total_count
            FROM analytics_events
            WHERE zone IS NOT NULL
            GROUP BY zone
            ORDER BY total_count DESC
            """
        )

    return [
        ZoneStats(
            zone=row["zone"],
            read_count=row["read_count"],
            write_count=row["write_count"],
            total_count=row["total_count"],
        )
        for row in rows
    ]


@app.get("/stats/models", response_model=List[ModelUsage])
async def model_stats():
    """Model usage: which Ollama models were used how often.

    Queries the messages table (owned by the API service) for model_used counts.
    Returns an empty list gracefully if the table does not exist yet.
    """
    async with db_pool.acquire() as conn:
        # Check table existence before querying to avoid hard errors on fresh DB
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'messages'
            )
            """
        )
        if not table_exists:
            return []

        rows = await conn.fetch(
            """
            SELECT model_used, COUNT(*) AS usage_count
            FROM messages
            WHERE model_used IS NOT NULL AND model_used <> ''
            GROUP BY model_used
            ORDER BY usage_count DESC
            """
        )

    return [
        ModelUsage(model_used=row["model_used"], usage_count=row["usage_count"])
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
