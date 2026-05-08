"""
Unit-Tests fuer den KeyCodi-gestuetzten Telegram-Responder.
Zone: WORKSPACE
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch


async def test_build_keycodi_response_uses_keycodi_local_when_available():
    """Responder nutzt KeyCodi als Primaerroute fuer Telegram-Antworten."""
    from services.telegram.keycodi import responder

    with patch.object(responder.llm, "is_available", AsyncMock(return_value=True)), \
         patch.object(responder.llm, "chat", AsyncMock(return_value="KeyCodi hat die Lage analysiert.\n\nSchlussfolgerung: Fokus zuerst auf die Telegram-Anbindung.")) as chat_mock, \
         patch.object(responder.llm, "model_for", return_value="qwen2.5-coder:32b"):
        result = await responder.build_keycodi_response_with_context(
            "Analysiere den Telegram-Bot",
            context="Sven: Bitte zuerst Telegram stabil machen",
        )

    assert result.source == "keycodi_local"
    assert result.model_used == "qwen2.5-coder:32b"
    assert "KeyCodi hat die Lage analysiert." in result.content
    assert "Schlussfolgerung" in result.content
    chat_mock.assert_awaited_once()


async def test_build_keycodi_response_supports_copilot_persona():
    """Copilot-Modus soll den alternativen Antwortpfad markieren."""
    from services.telegram.keycodi import responder

    with patch.object(responder.llm, "is_available", AsyncMock(return_value=True)), \
         patch.object(responder.llm, "chat", AsyncMock(return_value="Copilot analysiert das Repo konkret.")) as chat_mock, \
         patch.object(responder.llm, "model_for", return_value="openai/gpt-4.1-mini"):
        result = await responder.build_keycodi_response_with_context(
            "Wo liegt die Telegram-Logik?",
            context="",
            persona="copilot",
        )

    assert result.source == "copilot_cloud"
    assert result.model_used == "openai/gpt-4.1-mini"
    assert "Copilot analysiert" in result.content
    chat_mock.assert_awaited_once()


async def test_build_keycodi_response_falls_back_to_local_plan_without_ollama():
    """Ohne Ollama entsteht ein deterministischer lokaler Fallback-Plan."""
    from services.telegram.keycodi import responder

    with patch.object(responder.llm, "is_available", AsyncMock(return_value=False)):
        result = await responder.build_keycodi_response("Mission: fix Telegram placeholder response")

    assert result.source == "local_keycodi_plan"
    assert "Lokaler KeyCodi-Fallback-Plan" in result.content
    assert "KeyCodi — Master-Code-Orchestrator" in result.content


async def test_send_to_kirobi_prefers_local_keycodi_response_over_api_login():
    """Telegram-Chat antwortet zuerst ueber KeyCodi und nicht ueber API-Login."""
    import services.telegram.keycodi.main as tg_main

    tg_main._chat_history_by_user.clear()

    fake_response = AsyncMock(
        return_value=type(
            "Resp",
            (),
            {
                "content": "KeyCodi liefert jetzt eine echte Antwort.",
                "source": "keycodi_local",
                "model_used": "llama3.2",
            },
        )()
    )

    with patch("services.telegram.keycodi.main.build_keycodi_response_with_context", fake_response), \
         patch(
             "services.telegram.keycodi.main.send",
             AsyncMock(side_effect=[
                 {"ok": True, "result": {"message_id": 77}},
                 {"ok": True},
             ]),
         ) as send_mock, \
         patch("services.telegram.keycodi.main.edit_msg", AsyncMock(return_value={"ok": True})) as edit_mock, \
         patch("services.telegram.keycodi.main._get_api_token", AsyncMock(return_value=None)) as token_mock:
        await tg_main._send_to_kirobi(123, 456, "Baue eine Telegram-Verbesserung")

    assert send_mock.await_count == 2
    sent_texts = [call.args[1] for call in send_mock.await_args_list]
    assert "KeyCodi startet" in sent_texts[0]
    assert "KeyCodi liefert jetzt eine echte Antwort." in sent_texts[1]
    fake_response.assert_awaited_once()
    assert fake_response.await_args.kwargs["context"] == ""
    token_mock.assert_not_awaited()
    edit_mock.assert_awaited_once_with(123, 77, "✅ <b>KeyCodi</b> hat geantwortet.")


async def test_progress_reporter_edits_status_after_each_interval():
    """Laeuft eine Anfrage laenger, editiert der Bot die Statusmeldung periodisch."""
    import services.telegram.keycodi.main as tg_main

    calls = {"count": 0}

    async def fake_wait_for(awaitable, timeout):
        calls["count"] += 1
        awaitable.close()
        if calls["count"] == 1:
            raise asyncio.TimeoutError
        return True

    stop_event = asyncio.Event()

    with patch("services.telegram.keycodi.main.asyncio.wait_for", side_effect=fake_wait_for), \
         patch("services.telegram.keycodi.main.edit_msg", AsyncMock(return_value={"ok": True})) as edit_mock:
        await tg_main._progress_reporter(5, 9, stop_event)

    edit_mock.assert_awaited_once_with(5, 9, tg_main._status_text(1))


async def test_screen_home_uses_keycodi_branding_and_clean_menu():
    """Das Hauptmenue soll KeyCodi klar als primaeren Bot zeigen."""
    from services.telegram.keycodi import menus

    with patch("services.telegram.keycodi.menus.db.task_counts", AsyncMock(return_value={"pending": 2, "running": 1, "failed": 0})):
        text, keyboard = await menus.screen_home("Sven")

    assert "KeyCodi" in text
    labels = [button["text"] for row in keyboard["inline_keyboard"] for button in row]
    assert "💬 KeyCodi" in labels
    assert "🤝 Copilot" in labels
    assert "♻️ Neuer Chat" in labels
    assert "📋 Aufgaben" in labels


async def test_handle_slash_chat_uses_keycodi_wording():
    """Der /chat-Befehl soll KeyCodi klar als aktive Bot-Stimme anzeigen."""
    import services.telegram.keycodi.main as tg_main

    with patch("services.telegram.keycodi.main.send", AsyncMock(return_value={"ok": True})) as send_mock:
        await tg_main._handle_slash(1, 2, "Sven", "chat", "")

    send_mock.assert_awaited_once()
    assert "KeyCodi ist bereit" in send_mock.await_args.args[1]


async def test_handle_slash_copilot_uses_copilot_wording():
    """Der /copilot-Befehl soll den Copilot-Modus aktivieren."""
    import services.telegram.keycodi.main as tg_main

    with patch("services.telegram.keycodi.main.send", AsyncMock(return_value={"ok": True})) as send_mock:
        await tg_main._handle_slash(1, 2, "Sven", "copilot", "")

    send_mock.assert_awaited_once()
    assert "Copilot ist bereit" in send_mock.await_args.args[1]


async def test_process_update_routes_voice_messages_to_voice_handler():
    """Voice-Nachrichten sollen in den Voice-Flow und nicht in den Text-Handler gehen."""
    import services.telegram.keycodi.main as tg_main

    update = {
        "message": {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Sven"},
            "voice": {"file_id": "voice-file-1"},
        }
    }

    with patch("services.telegram.keycodi.main._handle_voice_message", AsyncMock()) as voice_mock, \
         patch("services.telegram.keycodi.main._handle_message", AsyncMock()) as text_mock:
        await tg_main._process_update(update)

    voice_mock.assert_awaited_once_with(123, 456, update["message"])
    text_mock.assert_not_awaited()


async def test_handle_voice_message_transcribes_and_returns_audio(tmp_path):
    """KeyCodi soll Voice lokal transkribieren und mit Audio antworten."""
    import services.telegram.keycodi.main as tg_main

    tg_main._chat_history_by_user.clear()
    audio_path = tmp_path / "hermes-reply.wav"
    audio_path.write_bytes(b"RIFFdemo")

    fake_response = type(
        "Resp",
        (),
        {
            "content": "Hier ist deine gesprochene KeyCodi-Antwort.",
            "source": "keycodi_local",
            "model_used": "llama3.2",
        },
    )()

    with patch(
        "services.telegram.keycodi.main.send",
        AsyncMock(side_effect=[
            {"ok": True, "result": {"message_id": 55}},
            {"ok": True},
        ]),
    ) as send_mock, \
         patch("services.telegram.keycodi.main.edit_msg", AsyncMock(return_value={"ok": True})) as edit_mock, \
         patch("services.telegram.keycodi.main.download_file", AsyncMock(return_value=tmp_path / "input.ogg")) as download_mock, \
         patch("services.telegram.keycodi.main._transcribe_telegram_audio", AsyncMock(return_value="Wie ist der Status?")) as transcribe_mock, \
         patch("services.telegram.keycodi.main.build_keycodi_response_with_context", AsyncMock(return_value=fake_response)) as response_mock, \
         patch("services.telegram.keycodi.main._synthesize_telegram_audio", AsyncMock(return_value=audio_path)) as synth_mock, \
         patch("services.telegram.keycodi.main.send_audio", AsyncMock(return_value={"ok": True})) as send_audio_mock, \
         patch("services.telegram.keycodi.main._progress_reporter", AsyncMock(return_value=None)):
        await tg_main._handle_voice_message(
            123,
            456,
            {"voice": {"file_id": "voice-file-1"}},
        )

    assert send_mock.await_count == 2
    download_mock.assert_awaited_once()
    transcribe_mock.assert_awaited_once()
    response_mock.assert_awaited_once()
    synth_mock.assert_awaited_once_with("Hier ist deine gesprochene KeyCodi-Antwort.")
    edit_mock.assert_awaited_once_with(123, 55, "✅ <b>KeyCodi Voice-Antwort ist bereit.</b>")
    send_audio_mock.assert_awaited_once_with(123, audio_path, caption="🧠 KeyCodi Voice Reply")
