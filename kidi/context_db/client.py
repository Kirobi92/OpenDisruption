"""
kidi/context_db/client.py
Zone: WORKSPACE

Redis-basierter ContextDB-Client für das OpenDisruption Multi-Agenten-System.

API (exakt wie docs/agent/CONTEXT-WINDOW.md §5 spezifiziert):
    put(key, value, ttl=86400)          — Eintrag schreiben
    get(key, requester_zone)            — Eintrag lesen
    query(zone, agent, category, ...)   — Mehrere Einträge abrufen
    merge(key, patch, requester_zone)   — Partielles Update (deep-merge)
    delete(key)                         — Eintrag löschen

Value-Schema (JSON):
    {
        "zone":    str,         # muss mit Key-Zone übereinstimmen
        "agent":   str,
        "payload": any,
        "ts":      float,       # Unix-Timestamp (UTC)
        "meta":    dict         # optional
    }

Umgebungsvariablen:
    KIROBI_REDIS_URL      — Redis-URL (Default: redis://localhost:6379/0)
    KIROBI_REDIS_PASSWORD — Redis-Passwort (leer = kein Auth)
    KIROBI_EGRESS_ALLOWED — "true"/"false" (Default: "false")
"""

import json
import os
import time
from typing import Any

from .errors import ConnectionError as ContextConnectionError
from .errors import KeyValueMismatch
from .keys import make_key, parse_key
from .zone_guard import check_read, check_write

try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

# Default TTL: 24 Stunden
DEFAULT_TTL = 86_400


def _get_redis_client():
    """Baut einen Redis-Client aus Umgebungsvariablen."""
    if not _REDIS_AVAILABLE:
        raise ImportError(
            "redis-py nicht installiert. "
            "Füge 'redis>=5.0' zu requirements.txt hinzu und installiere es."
        )
    url = os.environ.get("KIROBI_REDIS_URL", "redis://localhost:6379/0")
    password = os.environ.get("KIROBI_REDIS_PASSWORD") or None
    try:
        client = _redis_lib.from_url(url, password=password, decode_responses=True)
        client.ping()
        return client
    except Exception as exc:
        raise ContextConnectionError(url, exc) from exc


class ContextDB:
    """
    Zonen-getaggter Kurzzeit-Kontext-Store für OpenDisruption-Agenten.

    Kann mit einem vorhandenen Redis-Client initialisiert werden (für Tests)
    oder baut einen eigenen Client aus Umgebungsvariablen.

    Usage:
        db = ContextDB()
        key = db.put("WORKSPACE", "opencode", "task", {"title": "Phase 1"})
        entry = db.get(key, requester_zone="WORKSPACE")
    """

    def __init__(self, redis_client=None):
        """
        Args:
            redis_client: Optionaler Redis-Client (z.B. fakeredis.FakeRedis für Tests).
                          Wenn None, wird ein echter Client aus Env-Variablen gebaut.
        """
        self._redis = redis_client

    def _client(self):
        if self._redis is None:
            self._redis = _get_redis_client()
        return self._redis

    # ─── Core API ────────────────────────────────────────────────────────────

    def put(
        self,
        zone: str,
        agent: str,
        category: str,
        payload: Any,
        *,
        uid: str | None = None,
        ttl: int = DEFAULT_TTL,
        meta: dict | None = None,
    ) -> str:
        """
        Schreibt einen neuen Eintrag in den Store.

        Args:
            zone:     Zonen-String des Eintrags
            agent:    Agent-Bezeichner
            category: Kategorie des Eintrags
            payload:  Beliebiger JSON-serialisierbarer Inhalt
            uid:      Optionale UUID4 (wird sonst generiert)
            ttl:      Time-to-live in Sekunden (Default: 86400)
            meta:     Optionale Metadaten

        Returns:
            Erzeugter Key-String

        Raises:
            EgressViolation: bei sensitiven Zonen und KIROBI_EGRESS_ALLOWED=false
            SacredApprovalMissing: bei SACRED-Zone
            ZoneViolation: bei QUARANTINE
        """
        check_write(zone)
        key = make_key(zone, agent, category, uid)
        value = {
            "zone": zone,
            "agent": agent,
            "payload": payload,
            "ts": time.time(),
            "meta": meta or {},
        }
        r = self._client()
        r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        return key

    def get(self, key: str, requester_zone: str) -> dict:
        """
        Liest einen Eintrag aus dem Store.

        Args:
            key:            ContextDB-Schlüssel
            requester_zone: Maximale Zone des anfragenden Agenten

        Returns:
            Value-Dictionary (zone, agent, payload, ts, meta)

        Raises:
            ZoneViolation:         wenn requester_zone < entry_zone
            SacredApprovalMissing: wenn entry_zone == SACRED
            KeyError:              wenn key nicht existiert
        """
        parsed = parse_key(key)
        check_read(requester_zone, parsed.zone)
        r = self._client()
        raw = r.get(key)
        if raw is None:
            raise KeyError(f"ContextDB-Schlüssel nicht gefunden: '{key}'")
        return json.loads(raw)

    def query(
        self,
        zone: str,
        agent: str | None = None,
        category: str | None = None,
        requester_zone: str = "PUBLIC",
        limit: int = 100,
    ) -> list[dict]:
        """
        Sucht nach Einträgen anhand von Zone, Agent und/oder Kategorie.

        Args:
            zone:           Zonen-Filter (Pflichtangabe)
            agent:          Optionaler Agent-Filter
            category:       Optionaler Kategorie-Filter
            requester_zone: Maximale Zone des Anfragenden (für Zugriffsprüfung)
            limit:          Maximale Anzahl Ergebnisse

        Returns:
            Liste von (key, value)-Dicts: [{"key": ..., **value}, ...]
        """
        check_read(requester_zone, zone)

        # Pattern: ZONE:agent:category:* oder ZONE:*:*:* etc.
        agent_part = agent if agent else "*"
        cat_part = category if category else "*"
        pattern = f"{zone}:{agent_part}:{cat_part}:*"

        r = self._client()
        results = []
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor, match=pattern, count=200)
            for key in keys:
                raw = r.get(key)
                if raw:
                    entry = json.loads(raw)
                    entry["key"] = key
                    results.append(entry)
                if len(results) >= limit:
                    break
            if cursor == 0 or len(results) >= limit:
                break

        return results[:limit]

    def merge(self, key: str, patch: dict, requester_zone: str) -> dict:
        """
        Partielles Update eines bestehenden Eintrags (Deep-Merge des payload-Felds).

        Args:
            key:            ContextDB-Schlüssel
            patch:          Dict mit zu aktualisierenden payload-Feldern
            requester_zone: Maximale Zone des Anfragenden

        Returns:
            Aktualisierter Value

        Raises:
            ZoneViolation: wenn requester_zone < entry_zone
            KeyError:      wenn key nicht existiert
        """
        parsed = parse_key(key)
        check_read(requester_zone, parsed.zone)
        check_write(parsed.zone)

        r = self._client()
        raw = r.get(key)
        if raw is None:
            raise KeyError(f"ContextDB-Schlüssel nicht gefunden: '{key}'")

        value = json.loads(raw)

        # Deep-merge des payload-Felds
        if isinstance(value.get("payload"), dict) and isinstance(patch, dict):
            value["payload"] = _deep_merge(value["payload"], patch)
        else:
            # Scalar oder List: last-write-wins
            value["payload"] = patch

        value["ts"] = time.time()

        # TTL ermitteln und beibehalten
        ttl = r.ttl(key)
        if ttl < 0:
            ttl = DEFAULT_TTL

        r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        return value

    def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag.

        Returns:
            True wenn der Eintrag existierte, False wenn nicht
        """
        r = self._client()
        return bool(r.delete(key))

    def ping(self) -> bool:
        """Gibt True zurück wenn Redis erreichbar ist."""
        try:
            return self._client().ping()
        except Exception:
            return False


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _deep_merge(base: dict, patch: dict) -> dict:
    """
    Rekursiver Deep-Merge: patch überschreibt base-Felder.
    Nested dicts werden zusammengeführt, alle anderen Typen last-write-wins.
    """
    result = dict(base)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
