"""
Unit-Tests für services/analytics-service/main.py
Zone: WORKSPACE

asyncpg-Pool wird vollständig gemockt — kein echter DB-Zugriff.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event_row(
    event_id: int = 1,
    event_type: str = "page_view",
    user_id: str | None = "user-1",
    zone: str | None = "WORKSPACE",
    metadata: dict | None = None,
) -> dict:
    return {
        "id": event_id,
        "event_type": event_type,
        "user_id": user_id,
        "zone": zone,
        "metadata": json.dumps(metadata or {"source": "test"}),
        "created_at": datetime.now(timezone.utc),
    }


def _make_summary_row(total_events: int = 5, active_users: int = 2) -> dict:
    return {"total_events": total_events, "active_users": active_users}


def _make_type_row(event_type: str = "page_view", count: int = 3) -> dict:
    return {"event_type": event_type, "count": count}


def _make_zone_row(zone: str = "WORKSPACE", count: int = 4) -> dict:
    return {"zone": zone, "count": count}


def _make_zone_stats_row(
    zone: str = "WORKSPACE",
    read_count: int = 2,
    write_count: int = 1,
    total_count: int = 3,
) -> dict:
    return {
        "zone": zone,
        "read_count": read_count,
        "write_count": write_count,
        "total_count": total_count,
    }


class _AsyncContextManagerMock:
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=_AsyncContextManagerMock(mock_conn))
    mock_pool.close = AsyncMock(return_value=None)
    return mock_pool


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    import services.analytics_service.main as svc

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    with patch("services.analytics_service.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            svc.db_pool = mock_pool
            yield c, mock_conn

    svc.db_pool = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health → 'healthy' wenn DB erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "analytics"


def test_health_db_error_returns_degraded(client):
    """GET /health → 'unhealthy' wenn DB-Fehler."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unhealthy"
    assert "DB down" in data["error"]


# ---------------------------------------------------------------------------
# POST /events
# ---------------------------------------------------------------------------

def test_track_event_success(client):
    """POST /events → 201 und EventResponse."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_event_row())

    resp = c.post("/events", json={"event_type": "page_view", "zone": "WORKSPACE"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "page_view"
    assert data["zone"] == "WORKSPACE"
    assert isinstance(data["metadata"], dict)


def test_track_event_missing_type_returns_422(client):
    """POST /events ohne event_type → 422 Validation Error."""
    c, _ = client
    resp = c.post("/events", json={"zone": "WORKSPACE"})
    assert resp.status_code == 422


def test_dashboard_stats_returns_dashboard_shape(client):
    """GET /stats liefert das vom Dashboard erwartete Aggregat."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_summary_row(total_events=7, active_users=3))
    mock_conn.fetch = AsyncMock(return_value=[_make_zone_row(zone="WORKSPACE", count=5)])
    mock_conn.fetchval = AsyncMock(side_effect=[True, True, 11, 42])

    resp = c.get("/stats")

    assert resp.status_code == 200
    assert resp.json() == {
        "eventsToday": 7,
        "activeUsers": 3,
        "zoneUsage": {"WORKSPACE": 5},
        "totalConversations": 11,
        "totalMessages": 42,
    }


def test_dashboard_stats_handles_missing_conversation_tables(client):
    """GET /stats fällt auf Nullwerte zurück, wenn API-Tabellen fehlen."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_summary_row(total_events=2, active_users=1))
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchval = AsyncMock(side_effect=[False, False])

    resp = c.get("/stats")

    assert resp.status_code == 200
    assert resp.json()["totalConversations"] == 0
    assert resp.json()["totalMessages"] == 0


# ---------------------------------------------------------------------------
# GET /stats/daily
# ---------------------------------------------------------------------------

def test_get_stats_returns_data(client):
    """GET /stats/daily → DailyStats mit Daten."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_summary_row())
    mock_conn.fetch = AsyncMock(side_effect=[
        [_make_type_row()],
        [_make_zone_row()],
    ])

    resp = c.get("/stats/daily?date=2026-05-08")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-05-08"
    assert data["total_events"] == 5
    assert data["active_users"] == 2
    assert len(data["events_by_type"]) == 1
    assert data["events_by_type"][0]["event_type"] == "page_view"


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------

def test_list_events_empty(client):
    """GET /events → leere Liste wenn keine Events."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/events")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_events_with_filter(client):
    """GET /events?event_type=page_view → gefilterte Events."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_event_row(event_type="page_view")])

    resp = c.get("/events?event_type=page_view")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "page_view"


# ---------------------------------------------------------------------------
# GET /stats/zones
# ---------------------------------------------------------------------------

def test_get_zone_stats(client):
    """GET /stats/zones → ZoneStats-Liste."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_zone_stats_row()])

    resp = c.get("/stats/zones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"
    assert data[0]["read_count"] == 2
    assert data[0]["write_count"] == 1
    assert data[0]["total_count"] == 3
