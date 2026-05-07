"""
tests/unit/test_hermes_agent.py — Unit-Tests für HermesReasonerAgent

Testet:
- Keyword-Fallback-Klassifikation
- Dokument-Verarbeitung (TXT, MD, JSON)
- LLM-Reasoning mit gemocktem Ollama
- Graceful Fallback bei Ollama-Ausfall
- Zone-Validierung
- classify_document Task-Handler
- chain_of_thought Task-Handler

Zone: WORKSPACE
"""

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ─── Pfad-Setup ───────────────────────────────────────────────────────────────

# Repo-Root zum sys.path hinzufügen damit Imports funktionieren
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ─── Imports ──────────────────────────────────────────────────────────────────

from agents.hermes.agent import (
    HermesReasonerAgent,
    _build_classification_prompt,
    _extract_text_from_file,
    _keyword_classify,
    _process_document_async,
)
from agents._base.agent import Task


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def agent() -> HermesReasonerAgent:
    """Frische Agent-Instanz mit Test-Event-Log."""
    return HermesReasonerAgent(event_log_path="/tmp/test-hermes-events.log")


@pytest.fixture()
def txt_file(tmp_path: Path) -> Path:
    """Einfache TXT-Testdatei."""
    f = tmp_path / "test.txt"
    f.write_text("Dies ist ein Workspace-Dokument über Python-Entwicklung.", encoding="utf-8")
    return f


@pytest.fixture()
def md_file(tmp_path: Path) -> Path:
    """Markdown-Testdatei."""
    f = tmp_path / "readme.md"
    f.write_text(
        "# Projekt-Dokumentation\n\nDieses Dokument beschreibt die API-Architektur.",
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    """JSON-Testdatei."""
    f = tmp_path / "config.json"
    f.write_text(
        json.dumps({"service": "api", "version": "1.0", "public": True}),
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def family_txt_file(tmp_path: Path) -> Path:
    """TXT-Datei mit familiären Inhalten."""
    f = tmp_path / "family.txt"
    f.write_text(
        "Liebe Mama, ich schreibe dir über unsere Familie und die Kinder.",
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def sacred_txt_file(tmp_path: Path) -> Path:
    """TXT-Datei mit sacred-ähnlichen Inhalten."""
    f = tmp_path / "sacred.txt"
    f.write_text(
        "Trauma-Verarbeitung und Therapie-Notizen über Angst und Depression.",
        encoding="utf-8",
    )
    return f


@pytest.fixture()
def empty_file(tmp_path: Path) -> Path:
    """Leere Datei."""
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    return f


# ─── Ollama-Mock-Response ─────────────────────────────────────────────────────


def _make_ollama_response(
    summary: str = "Test-Zusammenfassung",
    zone: str = "WORKSPACE",
    tags: list[str] | None = None,
    confidence: float = 0.85,
) -> dict:
    """Erstellt eine gültige Ollama-Mock-Antwort."""
    return {
        "response": json.dumps({
            "summary": summary,
            "zone": zone,
            "tags": tags or ["test", "workspace"],
            "confidence": confidence,
        })
    }


# ─── Tests: Keyword-Klassifikation ────────────────────────────────────────────


class TestKeywordClassify:
    def test_workspace_default(self) -> None:
        zone, confidence = _keyword_classify("Technische Dokumentation über APIs")
        assert zone == "WORKSPACE"
        assert 0.0 < confidence <= 0.5

    def test_family_keywords(self) -> None:
        zone, confidence = _keyword_classify("Liebe Mama, die Kinder sind gesund")
        assert zone == "FAMILY_PRIVATE"
        assert confidence > 0.3

    def test_sacred_keywords(self) -> None:
        zone, confidence = _keyword_classify("Trauma und Therapie sind wichtig")
        assert zone == "SACRED"
        assert confidence > 0.3

    def test_public_keywords(self) -> None:
        zone, confidence = _keyword_classify("Öffentliche Pressemitteilung und Blog-Artikel")
        assert zone == "PUBLIC"
        assert confidence > 0.3

    def test_empty_text_returns_workspace(self) -> None:
        zone, confidence = _keyword_classify("")
        assert zone == "WORKSPACE"
        assert confidence == 0.3

    def test_confidence_capped_at_05(self) -> None:
        # Viele Keywords → Confidence darf 0.5 nicht überschreiten
        text = " ".join(["trauma"] * 20)
        _, confidence = _keyword_classify(text)
        assert confidence <= 0.5


# ─── Tests: Text-Extraktion ───────────────────────────────────────────────────


class TestExtractTextFromFile:
    def test_txt_file(self, txt_file: Path) -> None:
        text = _extract_text_from_file(txt_file)
        assert "Python-Entwicklung" in text

    def test_md_file(self, md_file: Path) -> None:
        text = _extract_text_from_file(md_file)
        assert "API-Architektur" in text

    def test_json_file(self, json_file: Path) -> None:
        text = _extract_text_from_file(json_file)
        assert "api" in text.lower()
        assert "version" in text

    def test_unknown_extension_as_text(self, tmp_path: Path) -> None:
        f = tmp_path / "data.xyz"
        f.write_text("Unbekanntes Format", encoding="utf-8")
        text = _extract_text_from_file(f)
        assert "Unbekanntes Format" in text

    def test_invalid_json_returns_raw(self, tmp_path: Path) -> None:
        f = tmp_path / "broken.json"
        f.write_text("{not valid json}", encoding="utf-8")
        text = _extract_text_from_file(f)
        assert "{not valid json}" in text


# ─── Tests: Prompt-Erstellung ─────────────────────────────────────────────────


class TestBuildClassificationPrompt:
    def test_contains_filename(self) -> None:
        prompt = _build_classification_prompt("Inhalt", "test.txt")
        assert "test.txt" in prompt

    def test_contains_zone_definitions(self) -> None:
        prompt = _build_classification_prompt("Inhalt", "doc.md")
        assert "PUBLIC" in prompt
        assert "SACRED" in prompt
        assert "FAMILY_PRIVATE" in prompt

    def test_long_text_truncated(self) -> None:
        long_text = "x" * 5000
        prompt = _build_classification_prompt(long_text, "big.txt")
        assert "gekürzt" in prompt

    def test_short_text_not_truncated(self) -> None:
        short_text = "Kurzer Text"
        prompt = _build_classification_prompt(short_text, "short.txt")
        assert "gekürzt" not in prompt


# ─── Tests: _process_document_async ──────────────────────────────────────────


class TestProcessDocumentAsync:
    def test_empty_file_returns_quarantine(self, empty_file: Path) -> None:
        result = asyncio.run(_process_document_async(
            empty_file,
            ollama_host="http://localhost:11434",
            model="llama3.2",
        ))
        assert result["zone"] == "QUARANTINE"
        assert result["llm_used"] is False
        assert result["confidence"] < 0.5

    def test_ollama_success(self, txt_file: Path) -> None:
        with patch("agents.hermes.agent._call_ollama", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "summary": "Python-Entwicklungsdokument",
                "zone": "WORKSPACE",
                "tags": ["python", "dev"],
                "confidence": 0.9,
            }
            result = asyncio.run(_process_document_async(
                txt_file,
                ollama_host="http://localhost:11434",
                model="llama3.2",
            ))

        assert result["zone"] == "WORKSPACE"
        assert result["llm_used"] is True
        assert result["confidence"] == 0.9
        assert result["fallback_reason"] is None

    def test_ollama_failure_uses_fallback(self, family_txt_file: Path) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Connection refused"),
        ):
            result = asyncio.run(_process_document_async(
                family_txt_file,
                ollama_host="http://localhost:11434",
                model="llama3.2",
            ))

        assert result["llm_used"] is False
        assert result["fallback_reason"] is not None
        assert result["confidence"] <= 0.5
        # Keyword-Fallback sollte FAMILY_PRIVATE erkennen
        assert result["zone"] == "FAMILY_PRIVATE"


# ─── Tests: HermesReasonerAgent ───────────────────────────────────────────────


class TestHermesReasonerAgent:
    def test_agent_id(self, agent: HermesReasonerAgent) -> None:
        assert agent.agent_id == "hermes-reasoner"

    def test_allowed_zones(self, agent: HermesReasonerAgent) -> None:
        assert "PUBLIC" in agent.allowed_input_zones
        assert "WORKSPACE" in agent.allowed_input_zones
        assert "SACRED" not in agent.allowed_input_zones

    def test_known_task_types(self, agent: HermesReasonerAgent) -> None:
        assert "classify_document" in agent.KNOWN_TASK_TYPES
        assert "chain_of_thought" in agent.KNOWN_TASK_TYPES

    def test_zone_violation_rejected(self, agent: HermesReasonerAgent) -> None:
        task = Task(
            task_type="classify_document",
            zone="SACRED",
            payload={"file_path": "some/file.txt"},
        )
        result = agent.run(task)
        assert result.success is False
        assert "zone" in result.error.lower() or "Zone" in result.error

    def test_classify_document_missing_file_path(
        self, agent: HermesReasonerAgent
    ) -> None:
        task = Task(task_type="classify_document", payload={})
        result = agent.run(task)
        assert result.success is False
        assert "file_path" in result.error

    def test_classify_document_nonexistent_file(
        self, agent: HermesReasonerAgent
    ) -> None:
        task = Task(
            task_type="classify_document",
            payload={"file_path": "/nonexistent/path/file.txt"},
        )
        result = agent.run(task)
        assert result.success is False
        assert "nicht gefunden" in result.error

    def test_classify_document_with_mocked_ollama(
        self, agent: HermesReasonerAgent, txt_file: Path
    ) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
        ) as mock_call:
            mock_call.return_value = {
                "summary": "Workspace-Dokument über Python",
                "zone": "WORKSPACE",
                "tags": ["python", "workspace"],
                "confidence": 0.88,
            }
            task = Task(
                task_type="classify_document",
                payload={"file_path": str(txt_file)},
            )
            result = agent.run(task)

        assert result.success is True
        assert result.payload["zone"] == "WORKSPACE"
        assert result.payload["llm_used"] is True
        assert result.payload["confidence"] == 0.88
        assert "summary" in result.payload
        assert "tags" in result.payload

    def test_classify_document_fallback_on_ollama_error(
        self, agent: HermesReasonerAgent, family_txt_file: Path
    ) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Ollama offline"),
        ):
            task = Task(
                task_type="classify_document",
                payload={"file_path": str(family_txt_file)},
            )
            result = agent.run(task)

        assert result.success is True  # Graceful degradation
        assert result.payload["llm_used"] is False
        assert result.payload["fallback_reason"] is not None
        assert result.payload["zone"] == "FAMILY_PRIVATE"

    def test_chain_of_thought_missing_question(
        self, agent: HermesReasonerAgent
    ) -> None:
        # Leeres Payload → graceful degradation (Ollama offline → Fallback-Pfad)
        # success=True weil der Agent nie hart fehlschlägt (Ollama-Offline ist normal)
        task = Task(task_type="chain_of_thought", payload={})
        result = agent.run(task)
        # Graceful degradation: success=True mit leerem reasoning
        assert result.success is True
        assert "reasoning_steps" in result.payload
        assert result.payload["llm_used"] is False

    def test_chain_of_thought_with_mocked_ollama(
        self, agent: HermesReasonerAgent
    ) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
        ) as mock_call:
            mock_call.return_value = {
                "summary": "Rust ist schneller wegen Zero-Cost-Abstractions",
                "reasoning_steps": [
                    "Rust hat kein GC",
                    "Rust kompiliert zu nativem Code",
                    "Python hat Interpreter-Overhead",
                ],
                "conclusion": "Rust ist schneller durch Systemdesign",
                "tags": ["rust", "python", "performance"],
                "confidence": 0.92,
            }
            task = Task(
                task_type="chain_of_thought",
                payload={"question": "Warum ist Rust schneller als Python?"},
            )
            result = agent.run(task)

        assert result.success is True
        assert result.payload["llm_used"] is True
        assert len(result.payload["reasoning_steps"]) == 3
        assert result.payload["conclusion"] is not None
        assert result.confidence == 0.92

    def test_chain_of_thought_fallback_on_ollama_error(
        self, agent: HermesReasonerAgent
    ) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Connection refused"),
        ):
            task = Task(
                task_type="chain_of_thought",
                payload={"question": "Was ist 2+2?"},
            )
            result = agent.run(task)

        # Graceful degradation: success=True aber llm_used=False
        assert result.success is True
        assert result.payload["llm_used"] is False
        assert result.payload["fallback_reason"] is not None
        assert result.confidence == 0.1

    def test_debate_task_type(self, agent: HermesReasonerAgent) -> None:
        with patch(
            "agents.hermes.agent._call_ollama",
            new_callable=AsyncMock,
        ) as mock_call:
            mock_call.return_value = {
                "summary": "Pro/Contra Remote Work",
                "reasoning_steps": ["Pro: Flexibilität", "Contra: Isolation"],
                "conclusion": "Hybrid ist optimal",
                "tags": ["remote", "work"],
                "confidence": 0.75,
            }
            task = Task(
                task_type="debate",
                payload={"question": "Remote Work: Pro oder Contra?"},
            )
            result = agent.run(task)

        assert result.success is True
        assert result.payload["task_type"] == "debate"

    def test_ollama_host_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_HOST", "http://custom-ollama:11434")
        a = HermesReasonerAgent()
        assert a._ollama_host == "http://custom-ollama:11434"

    def test_ollama_model_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_MODEL", "mistral")
        a = HermesReasonerAgent()
        assert a._model == "mistral"


# ─── Tests: _call_ollama (HTTP-Mock) ─────────────────────────────────────────


class TestCallOllama:
    def test_valid_response_parsed(self) -> None:
        from agents.hermes.agent import _call_ollama

        mock_http_response = MagicMock()
        mock_http_response.raise_for_status = MagicMock()
        mock_http_response.json.return_value = {
            "response": json.dumps({
                "summary": "Test",
                "zone": "WORKSPACE",
                "tags": ["a"],
                "confidence": 0.8,
            })
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(_call_ollama(
                "test prompt",
                ollama_host="http://localhost:11434",
                model="llama3.2",
            ))

        assert result["zone"] == "WORKSPACE"
        assert result["confidence"] == 0.8

    def test_invalid_zone_falls_back_to_quarantine(self) -> None:
        from agents.hermes.agent import _call_ollama

        mock_http_response = MagicMock()
        mock_http_response.raise_for_status = MagicMock()
        mock_http_response.json.return_value = {
            "response": json.dumps({
                "summary": "Test",
                "zone": "INVALID_ZONE",
                "tags": ["a"],
                "confidence": 0.8,
            })
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(_call_ollama(
                "test prompt",
                ollama_host="http://localhost:11434",
                model="llama3.2",
            ))

        assert result["zone"] == "QUARANTINE"

    def test_no_json_in_response_raises(self) -> None:
        from agents.hermes.agent import _call_ollama

        mock_http_response = MagicMock()
        mock_http_response.raise_for_status = MagicMock()
        mock_http_response.json.return_value = {
            "response": "Hier ist keine JSON-Antwort, nur Text."
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Kein JSON"):
                asyncio.run(_call_ollama(
                    "test prompt",
                    ollama_host="http://localhost:11434",
                    model="llama3.2",
                ))

    def test_confidence_clamped_to_range(self) -> None:
        from agents.hermes.agent import _call_ollama

        mock_http_response = MagicMock()
        mock_http_response.raise_for_status = MagicMock()
        mock_http_response.json.return_value = {
            "response": json.dumps({
                "summary": "Test",
                "zone": "PUBLIC",
                "tags": [],
                "confidence": 1.5,  # Über 1.0 — muss auf 1.0 geklemmt werden
            })
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_http_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(_call_ollama(
                "test prompt",
                ollama_host="http://localhost:11434",
                model="llama3.2",
            ))

        assert result["confidence"] == 1.0
