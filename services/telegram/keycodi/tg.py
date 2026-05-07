"""
services/telegram/keycodi/tg.py
Telegram API Wrapper — alle API-Calls an einem Ort.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from .config import TELEGRAM_API

log = logging.getLogger("keycodi.tg")


def _chunks(text: str, size: int = 3900) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


async def tg(method: str, *, log_failures: bool = True, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{TELEGRAM_API}/{method}", json=kwargs)
    data: dict = {}
    try:
        data = r.json()
    except ValueError:
        data = {"ok": False, "status_code": r.status_code}
    if log_failures and not data.get("ok"):
        log.warning("Telegram %s failed: %s", method, data.get("description", r.status_code))
    return data


async def send(
    chat_id: int | str,
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: str = "HTML",
    *,
    log_failures: bool = True,
) -> dict:
    result: dict = {"ok": False}
    for chunk in _chunks(text):
        payload: dict = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        result = await tg("sendMessage", log_failures=log_failures, **payload)
        if not result.get("ok") and parse_mode:
            fallback = {"chat_id": chat_id, "text": chunk}
            if reply_markup:
                fallback["reply_markup"] = reply_markup
            result = await tg("sendMessage", log_failures=log_failures, **fallback)
    return result


async def edit_msg(
    chat_id: int | str,
    message_id: int,
    text: str,
    reply_markup: Optional[dict] = None,
) -> dict:
    payload: dict = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    result = await tg("editMessageText", **payload)
    if not result.get("ok"):
        return await send(chat_id, text, reply_markup)
    return result


async def answer_cb(callback_query_id: str, text: str = "", alert: bool = False) -> dict:
    return await tg(
        "answerCallbackQuery",
        callback_query_id=callback_query_id,
        text=text,
        show_alert=alert,
    )


async def set_commands(commands: list[dict]) -> None:
    result = await tg("setMyCommands", commands=commands)
    log.info("Bot-Commands gesetzt: %s", result.get("ok"))
