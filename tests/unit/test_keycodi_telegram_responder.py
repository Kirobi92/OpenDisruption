"""
Unit-Tests fuer den lokalen KeyCodi-Telegram-Responder.
Zone: WORKSPACE
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch


async def test_build_keycodi_response_uses_local_ollama_when_available():
    """Responder nutzt Ollama lokal und ruft keine Kirobi-API auf."""
    from services.telegram.keycodi import responder

    with patch.object(responder.llm, "is_available", AsyncMock(return_value=True)), \
         patch.object(responder.llm, "chat", AsyncMock(return_value="Ich bin KeyCodi.")) as chat_mock:
        result = await responder.build_keycodi_response("Implementiere einen Test")

    assert result.source == "local_ollama"
    assert result.content == "Ich bin KeyCodi."
    chat_mock.assert_awaited_once()
    kwargs = chat_mock.await_args.kwargs
    assert kwargs["task_type"] == "code"
    assert "SACRED" in kwargs["system"]


async def test_build_keycodi_response_falls_back_to_local_plan_without_ollama():
    """Ohne Ollama entsteht ein deterministischer KeyCodi-Plan."""
    from services.telegram.keycodi import responder

    with patch.object(responder.llm, "is_available", AsyncMock(return_value=False)):
        result = await responder.build_keycodi_response("Mission: fix Telegram placeholder response")

    assert result.source == "local_keycodi_plan"
    assert "Lokaler KeyCodi-Plan" in result.content
    assert "KeyCodi - Master-Code-Orchestrator" in result.content
    assert "Cloud-Modelle" in result.content


async def test_send_to_kirobi_prefers_local_keycodi_response_over_api_login():
    """Telegram-Chat antwortet local-first statt Placeholder/API-Pflicht."""
    import services.telegram.keycodi.main as tg_main

    response = tg_main.build_keycodi_response.__annotations__
    assert response is not None

    fake_response = AsyncMock(
        return_value=type("Resp", (), {"content": "Lokale KeyCodi Antwort", "source": "local_ollama"})()
    )

    with patch("services.telegram.keycodi.main.build_keycodi_response", fake_response), \
         patch("services.telegram.keycodi.main.send", AsyncMock(return_value={"ok": True})) as send_mock, \
         patch("services.telegram.keycodi.main._get_api_token", AsyncMock(return_value=None)) as token_mock:
        await tg_main._send_to_kirobi(123, 456, "Baue eine Telegram-Verbesserung")

    assert send_mock.await_count == 2
    sent_texts = [call.args[1] for call in send_mock.await_args_list]
    assert sent_texts[0] == "⌛ KeyCodi denkt nach..."
    assert "Lokale KeyCodi Antwort" in sent_texts[1]
    token_mock.assert_not_awaited()
