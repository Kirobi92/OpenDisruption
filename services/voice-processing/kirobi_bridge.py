"""Bridge to the kirobi-api conversation system.

Reuses the existing 15-agent persona system + conversation memory in
services/api/main.py. This module handles JWT login, conversation
creation, and message posting on behalf of voice-processing.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

API_URL = os.getenv("KIROBI_API_URL", "http://api:8000").rstrip("/")
AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000").rstrip("/")
API_USER = os.getenv("KIROBI_API_USER", "sven")
API_PASSWORD = os.getenv("KIROBI_API_PASSWORD", "changeme")

_TOKEN: Optional[str] = None
_TOKEN_EXPIRES: float = 0.0


async def _login(client: httpx.AsyncClient) -> str:
    """Obtain (or refresh) JWT token via /auth/login."""
    global _TOKEN, _TOKEN_EXPIRES
    if _TOKEN and time.time() < _TOKEN_EXPIRES - 60:
        return _TOKEN
    try:
        resp = await client.post(
            f"{AUTH_URL}/login",
            json={"username": API_USER, "password": API_PASSWORD},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        _TOKEN = data["access_token"]
        # Tokens are typically 30 minutes; refresh after 25
        _TOKEN_EXPIRES = time.time() + 25 * 60
        return _TOKEN
    except Exception as exc:
        logger.error("API login failed: %s", exc)
        raise


async def _auth_headers(client: httpx.AsyncClient) -> dict:
    token = await _login(client)
    return {"Authorization": f"Bearer {token}"}


async def ensure_conversation(
    client: httpx.AsyncClient,
    conversation_id: Optional[str],
    title: str,
    agent: str,
) -> str:
    """Return an existing conversation_id or create a new one.

    The API stores the agent on the conversation; we re-create on 404.
    """
    if conversation_id:
        try:
            headers = await _auth_headers(client)
            resp = await client.get(
                f"{API_URL}/conversations/{conversation_id}",
                headers=headers,
                timeout=8.0,
            )
            if resp.status_code == 200:
                return conversation_id
        except Exception:  # noqa: BLE001
            pass

    headers = await _auth_headers(client)
    resp = await client.post(
        f"{API_URL}/conversations",
        json={"title": title, "agent": agent},
        headers=headers,
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["id"]


async def send_message(
    client: httpx.AsyncClient,
    conversation_id: str,
    text: str,
    agent: str,
    extra_system: Optional[str] = None,
) -> dict[str, Any]:
    """Post a user message and return the assistant reply payload.

    The API runs LLM inference internally and returns the assistant message.
    """
    headers = await _auth_headers(client)
    payload: dict[str, Any] = {"content": text, "agent": agent}
    if extra_system:
        payload["system_prompt_extra"] = extra_system
    resp = await client.post(
        f"{API_URL}/conversations/{conversation_id}/messages",
        json=payload,
        headers=headers,
        timeout=120.0,  # LLM inference can take a while
    )
    resp.raise_for_status()
    return resp.json()
