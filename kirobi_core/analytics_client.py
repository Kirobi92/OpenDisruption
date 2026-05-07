"""
kirobi_core/analytics_client.py — Fire-and-forget Analytics-Client

Sendet Events an den Analytics-Service (Port 8010).
SICHERHEIT: Niemals Inhalte loggen — nur Metadaten (event_type, zone, model, counts).
Zone: WORKSPACE
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

ANALYTICS_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics:8010")


async def track(
    event_type: str,
    *,
    zone: str = "WORKSPACE",
    model: str | None = None,
    tokens: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Fire-and-forget: sendet ein Event an den Analytics-Service.

    Niemals Inhalte (Texte, Nachrichten, Dokument-Inhalte) übergeben.
    Nur Metadaten: event_type, zone, model, token-counts, timestamps.
    """
    try:
        import httpx  # lazy — damit sys.modules-Patching in Tests greift
        payload: dict[str, Any] = {
            "event_type": event_type,
            "zone": zone,
            "timestamp": time.time(),
        }
        if model:
            payload["model"] = model
        if tokens is not None:
            payload["tokens"] = tokens
        if metadata:
            # Sicherheits-Filter: keine String-Werte über 200 Zeichen
            payload["metadata"] = {
                k: v for k, v in metadata.items()
                if not isinstance(v, str) or len(v) <= 200
            }
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(f"{ANALYTICS_URL}/events", json=payload)
    except Exception as exc:  # noqa: BLE001
        # Analytics-Fehler dürfen nie den Haupt-Flow unterbrechen
        logger.debug("Analytics-Event fehlgeschlagen (ignoriert): %s", exc)


def track_sync(event_type: str, **kwargs: Any) -> None:
    """Sync-Wrapper für track() — nutzt asyncio.run wenn kein Loop läuft."""
    try:
        loop = asyncio.get_running_loop()
        # In laufendem Loop: als Task schedulen (fire-and-forget)
        loop.create_task(track(event_type, **kwargs))
    except RuntimeError:
        # Kein Loop: asyncio.run
        try:
            asyncio.run(track(event_type, **kwargs))
        except Exception:  # noqa: BLE001
            pass
