"""
services/telegram/keycodi/db.py
Postgres-Zugriff: Tasks, Events, Entscheidungs-Queue.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

import asyncpg

from .config import DATABASE_URL

log = logging.getLogger("keycodi.db")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> Optional[asyncpg.Pool]:
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=8)
            await _ensure_schema(_pool)
        except Exception as exc:
            log.warning("DB-Verbindung fehlgeschlagen: %s", exc)
            return None
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
    _pool = None


async def _ensure_schema(pool: asyncpg.Pool) -> None:
    """Erstellt fehlende Tabellen falls nicht vorhanden (idempotent)."""
    async with pool.acquire() as conn:
        # Supervisor-Tasks (könnte bereits existieren)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS supervisor_tasks (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                description  TEXT,
                status       TEXT NOT NULL DEFAULT 'pending',
                priority     TEXT NOT NULL DEFAULT 'medium',
                assigned_agent TEXT,
                sofort       BOOLEAN NOT NULL DEFAULT FALSE,
                created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
                metadata     JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """)

        # Entscheidungs-Queue (neu für v3)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS keycodi_decisions (
                id           TEXT PRIMARY KEY,
                task_id      TEXT,
                question     TEXT NOT NULL,
                context      TEXT,
                options      JSONB NOT NULL DEFAULT '[]'::jsonb,
                answered     BOOLEAN NOT NULL DEFAULT FALSE,
                answer       TEXT,
                answered_at  TIMESTAMP,
                created_at   TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)

        # Cron-Report-Log (neu für v3)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS keycodi_cron_reports (
                id           SERIAL PRIMARY KEY,
                report_type  TEXT NOT NULL DEFAULT 'status',
                content      TEXT NOT NULL,
                sent_at      TIMESTAMP NOT NULL DEFAULT NOW(),
                notified     BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)

        # Events (könnte existieren, erweitern falls nicht)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS supervisor_events (
                id           SERIAL PRIMARY KEY,
                timestamp    TIMESTAMP NOT NULL DEFAULT NOW(),
                event_type   TEXT,
                severity     TEXT DEFAULT 'info',
                message      TEXT,
                metadata     JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """)


# ─── Tasks ───────────────────────────────────────────────────────────────────

async def task_counts() -> dict:
    pool = await get_pool()
    if pool is None:
        return {}
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE status='pending')     AS pending,
                    COUNT(*) FILTER (WHERE status='in_progress') AS running,
                    COUNT(*) FILTER (WHERE status='completed')   AS completed,
                    COUNT(*) FILTER (WHERE status='failed')      AS failed,
                    COUNT(*) FILTER (WHERE sofort=TRUE AND status='pending') AS sofort
                FROM supervisor_tasks
            """)
            return dict(row) if row else {}
    except Exception as exc:
        log.warning("task_counts: %s", exc)
        return {}


async def tasks_list(limit: int = 12, status: Optional[str] = None, sofort_only: bool = False) -> list[dict]:
    pool = await get_pool()
    if pool is None:
        return []
    try:
        async with pool.acquire() as conn:
            where_parts = []
            params: list = []
            if status:
                params.append(status)
                where_parts.append(f"status=${len(params)}")
            if sofort_only:
                where_parts.append("sofort=TRUE")
            where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            params.append(limit)
            rows = await conn.fetch(
                f"SELECT id, name, status, priority, assigned_agent, sofort, created_at "
                f"FROM supervisor_tasks {where} "
                f"ORDER BY sofort DESC, priority DESC, created_at DESC LIMIT ${len(params)}",
                *params,
            )
            return [dict(r) for r in rows]
    except Exception as exc:
        log.warning("tasks_list: %s", exc)
        return []


async def task_detail(task_id: str) -> Optional[dict]:
    pool = await get_pool()
    if pool is None:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, description, status, priority, assigned_agent, sofort, created_at, updated_at "
                "FROM supervisor_tasks WHERE id=$1",
                task_id,
            )
            return dict(row) if row else None
    except Exception as exc:
        log.warning("task_detail: %s", exc)
        return None


async def task_add(
    name: str,
    description: str,
    priority: str = "medium",
    sofort: bool = False,
    source: str = "telegram",
) -> str:
    pool = await get_pool()
    if pool is None:
        raise RuntimeError("Postgres nicht erreichbar")
    task_id = f"tg_{int(datetime.now().timestamp() * 1000)}"
    now = datetime.now()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO supervisor_tasks
               (id, name, description, priority, sofort, status, created_at, updated_at, metadata)
               VALUES ($1,$2,$3,$4,$5,'pending',$6,$7,$8::jsonb)""",
            task_id,
            name,
            description,
            priority,
            sofort,
            now,
            now,
            json.dumps({"source": source}),
        )
    return task_id


async def task_update_status(task_id: str, status: str) -> None:
    pool = await get_pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE supervisor_tasks SET status=$1, updated_at=NOW() WHERE id=$2",
                status,
                task_id,
            )
    except Exception as exc:
        log.warning("task_update_status: %s", exc)


# ─── Entscheidungs-Queue ─────────────────────────────────────────────────────

async def decision_create(
    question: str,
    context: str = "",
    options: list[str] | None = None,
    task_id: str | None = None,
) -> str:
    pool = await get_pool()
    if pool is None:
        raise RuntimeError("Postgres nicht erreichbar")
    decision_id = f"dec_{int(datetime.now().timestamp() * 1000)}"
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO keycodi_decisions
               (id, task_id, question, context, options, created_at)
               VALUES ($1,$2,$3,$4,$5::jsonb,NOW())""",
            decision_id,
            task_id,
            question,
            context,
            json.dumps(options or []),
        )
    return decision_id


async def decision_answer(decision_id: str, answer: str) -> None:
    pool = await get_pool()
    if pool is None:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE keycodi_decisions SET answered=TRUE, answer=$1, answered_at=NOW() WHERE id=$2",
            answer,
            decision_id,
        )


async def decision_pending() -> list[dict]:
    pool = await get_pool()
    if pool is None:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, question, context, options, task_id, created_at "
                "FROM keycodi_decisions WHERE answered=FALSE ORDER BY created_at ASC LIMIT 5"
            )
            return [dict(r) for r in rows]
    except Exception as exc:
        log.warning("decision_pending: %s", exc)
        return []


# ─── Events ──────────────────────────────────────────────────────────────────

async def events_recent(limit: int = 10) -> list[dict]:
    pool = await get_pool()
    if pool is None:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT timestamp, event_type, severity, message FROM supervisor_events "
                "ORDER BY timestamp DESC LIMIT $1",
                limit,
            )
            return [dict(r) for r in rows]
    except Exception as exc:
        log.warning("events_recent: %s", exc)
        return []


async def event_log(event_type: str, message: str, severity: str = "info", metadata: dict | None = None) -> None:
    pool = await get_pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO supervisor_events (event_type, severity, message, metadata) VALUES ($1,$2,$3,$4::jsonb)",
                event_type,
                severity,
                message,
                json.dumps(metadata or {}),
            )
    except Exception as exc:
        log.warning("event_log: %s", exc)


# ─── Cron-Reports ────────────────────────────────────────────────────────────

async def cron_report_save(content: str, report_type: str = "status") -> None:
    pool = await get_pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO keycodi_cron_reports (report_type, content, notified) VALUES ($1,$2,TRUE)",
                report_type,
                content,
            )
    except Exception as exc:
        log.warning("cron_report_save: %s", exc)
