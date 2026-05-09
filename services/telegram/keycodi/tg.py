"""
services/telegram/keycodi/tg.py
Telegram API Wrapper — alle API-Calls an einem Ort.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import httpx

from .config import TELEGRAM_API, TELEGRAM_FILE_API

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


async def set_descriptions(description: str, short_description: str | None = None) -> None:
    result = await tg("setMyDescription", description=description)
    log.info("Bot-Beschreibung gesetzt: %s", result.get("ok"))
    if short_description:
        short_result = await tg("setMyShortDescription", short_description=short_description)
        log.info("Bot-Kurzbeschreibung gesetzt: %s", short_result.get("ok"))


async def set_chat_menu_commands() -> None:
    result = await tg("setChatMenuButton", menu_button={"type": "commands"})
    log.info("Chat-Menü auf Commands gesetzt: %s", result.get("ok"))


async def set_descriptions(description: str, short_description: str | None = None) -> None:
    result = await tg("setMyDescription", description=description)
    log.info("Bot-Beschreibung gesetzt: %s", result.get("ok"))
    if short_description:
        short_result = await tg("setMyShortDescription", short_description=short_description)
        log.info("Bot-Kurzbeschreibung gesetzt: %s", short_result.get("ok"))


async def set_chat_menu_commands() -> None:
    result = await tg("setChatMenuButton", menu_button={"type": "commands"})
    log.info("Chat-Menü auf Commands gesetzt: %s", result.get("ok"))


async def download_file(file_id: str, target_path: str | Path) -> Path:
    """Laedt eine Telegram-Datei anhand ihrer file_id herunter."""
    meta = await tg("getFile", file_id=file_id)
    file_path = meta.get("result", {}).get("file_path")
    if not file_path:
        raise RuntimeError(f"Telegram-Datei nicht gefunden: {file_id}")

    target = Path(target_path)
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(f"{TELEGRAM_FILE_API}/{file_path}")
        response.raise_for_status()
    target.write_bytes(response.content)
    return target


async def send_audio(
    chat_id: int | str,
    audio_path: str | Path,
    *,
    caption: str | None = None,
    title: str = "KeyCodi",
    performer: str = "KeyCodi",
) -> dict:
    """Sendet eine Audiodatei an Telegram."""
    target = Path(audio_path)
    data = {
        "chat_id": str(chat_id),
        "title": title,
        "performer": performer,
    }
    if caption:
        data["caption"] = caption

    async with httpx.AsyncClient(timeout=120) as client:
        with target.open("rb") as handle:
            files = {
                "audio": (target.name, handle, "audio/wav"),
            }
            response = await client.post(
                f"{TELEGRAM_API}/sendAudio",
                data=data,
                files=files,
            )
    try:
        payload = response.json()
    except ValueError:
        payload = {"ok": False, "status_code": response.status_code}
    if not payload.get("ok"):
        log.warning("Telegram sendAudio failed: %s", payload.get("description", response.status_code))
    return payload
