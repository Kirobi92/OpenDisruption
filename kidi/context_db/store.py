"""
kidi/context_db/store.py
Zone: WORKSPACE

SQLite-basierter Context-Store für den kidi MCP-Server.
Speichert Key-Value-Paare mit Zone-Klassifizierung und optionalem TTL.
Datenbankpfad: ~/.kirobi/context.db
"""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .errors import EgressViolation, SacredApprovalMissing

# Zonen die im MCP-Server erlaubt sind (kein FAMILY_PRIVATE, kein SACRED)
_ALLOWED_ZONES = frozenset({"PUBLIC", "WORKSPACE"})

_DB_PATH = Path.home() / ".kirobi" / "context.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_entries (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    zone       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at REAL
);
"""


def _get_connection(db_path: Path = _DB_PATH) -> sqlite3.Connection:
    """Öffnet (und initialisiert) die SQLite-Datenbank."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _validate_zone(zone: str) -> None:
    """
    Prüft ob die Zone für den MCP-Server erlaubt ist.

    Raises:
        SacredApprovalMissing: bei SACRED
        EgressViolation: bei FAMILY_PRIVATE
        ValueError: bei unbekannter Zone
    """
    if zone == "SACRED":
        raise SacredApprovalMissing()
    if zone == "FAMILY_PRIVATE":
        raise EgressViolation(zone)
    if zone not in _ALLOWED_ZONES:
        raise ValueError(f"Unbekannte oder nicht erlaubte Zone: '{zone}'")


def store_context(
    key: str,
    value: str,
    zone: str,
    ttl_seconds: Optional[int] = None,
    db_path: Path = _DB_PATH,
) -> dict:
    """
    Speichert einen Kontext-Eintrag in der SQLite-Datenbank.

    Args:
        key:         Eindeutiger Schlüssel
        value:       Zu speichernder Wert
        zone:        Zone des Eintrags (PUBLIC oder WORKSPACE)
        ttl_seconds: Optionale Lebensdauer in Sekunden
        db_path:     Pfad zur SQLite-Datenbank

    Returns:
        Dict mit key, zone, created_at

    Raises:
        SacredApprovalMissing: bei SACRED-Zone
        EgressViolation: bei FAMILY_PRIVATE-Zone
    """
    _validate_zone(zone)
    created_at = datetime.now(timezone.utc).isoformat()
    expires_at = (time.time() + ttl_seconds) if ttl_seconds else None

    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO context_entries (key, value, zone, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                zone       = excluded.zone,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at
            """,
            (key, value, zone, created_at, expires_at),
        )

    return {"key": key, "zone": zone, "created_at": created_at}


def get_context(key: str, db_path: Path = _DB_PATH) -> Optional[dict]:
    """
    Liest einen Kontext-Eintrag aus der Datenbank.

    Args:
        key:     Schlüssel des Eintrags
        db_path: Pfad zur SQLite-Datenbank

    Returns:
        Dict mit key, value, zone, created_at oder None wenn nicht gefunden / abgelaufen
    """
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT key, value, zone, created_at, expires_at FROM context_entries WHERE key = ?",
            (key,),
        ).fetchone()

    if row is None:
        return None

    # TTL-Prüfung
    if row["expires_at"] is not None and time.time() > row["expires_at"]:
        delete_context(key, db_path)
        return None

    return {
        "key": row["key"],
        "value": row["value"],
        "zone": row["zone"],
        "created_at": row["created_at"],
    }


def list_context(
    zone: Optional[str] = None,
    prefix: Optional[str] = None,
    db_path: Path = _DB_PATH,
) -> list[dict]:
    """
    Listet alle gültigen Kontext-Einträge auf.

    Args:
        zone:    Optionaler Zone-Filter
        prefix:  Optionaler Key-Präfix-Filter
        db_path: Pfad zur SQLite-Datenbank

    Returns:
        Liste von Dicts mit key, zone, created_at
    """
    now = time.time()
    query = "SELECT key, zone, created_at, expires_at FROM context_entries WHERE 1=1"
    params: list = []

    if zone:
        query += " AND zone = ?"
        params.append(zone)

    if prefix:
        query += " AND key LIKE ?"
        params.append(f"{prefix}%")

    with _get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    result = []
    for row in rows:
        # Abgelaufene Einträge überspringen
        if row["expires_at"] is not None and now > row["expires_at"]:
            continue
        result.append({
            "key": row["key"],
            "zone": row["zone"],
            "created_at": row["created_at"],
        })

    return result


def delete_context(key: str, db_path: Path = _DB_PATH) -> bool:
    """
    Löscht einen Kontext-Eintrag.

    Args:
        key:     Schlüssel des zu löschenden Eintrags
        db_path: Pfad zur SQLite-Datenbank

    Returns:
        True wenn ein Eintrag gelöscht wurde, False wenn nicht gefunden
    """
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM context_entries WHERE key = ?", (key,)
        )
    return cursor.rowcount > 0
