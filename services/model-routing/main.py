"""
Kirobi Model-Routing Service
Zone: WORKSPACE
Zweck: Intelligente Modell-Selektion basierend auf Task-Typ, GPU-Verfügbarkeit und Kontext
Port: 8009
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
PORT = int(os.getenv("MODEL_ROUTING_PORT", "8009"))

# Modell-Routing-Tabelle: Task-Typ → bevorzugtes Modell
MODEL_ROUTING: Dict[str, Dict[str, str]] = {
    "chat": {
        "primary": os.getenv("MODEL_CHAT_PRIMARY", "llama3.1:8b"),
        "fallback": os.getenv("MODEL_CHAT_FALLBACK", "llama3.2:3b"),
        "description": "Allgemeine Konversation",
    },
    "code": {
        "primary": os.getenv("MODEL_CODE_PRIMARY", "qwen2.5-coder:7b"),
        "fallback": os.getenv("MODEL_CODE_FALLBACK", "llama3.1:8b"),
        "description": "Code-Generierung und -Analyse",
    },
    "reasoning": {
        "primary": os.getenv("MODEL_REASONING_PRIMARY", "deepseek-r1:7b"),
        "fallback": os.getenv("MODEL_REASONING_FALLBACK", "llama3.1:8b"),
        "description": "Komplexes Reasoning und Analyse",
    },
    "embedding": {
        "primary": os.getenv("MODEL_EMBED_PRIMARY", "nomic-embed-text"),
        "fallback": os.getenv("MODEL_EMBED_FALLBACK", "nomic-embed-text"),
        "description": "Vektor-Embeddings für RAG",
    },
    "vision": {
        "primary": os.getenv("MODEL_VISION_PRIMARY", "llava:7b"),
        "fallback": os.getenv("MODEL_VISION_FALLBACK", "llama3.2-vision:11b"),
        "description": "Bild-Analyse und -Beschreibung",
    },
    "supervisor": {
        "primary": os.getenv("SUPERVISOR_MODEL", "llama3.1:8b"),
        "fallback": os.getenv("MODEL_SUPERVISOR_FALLBACK", "llama3.2:3b"),
        "description": "Supervisor-Orchestrierung",
    },
}


class RouteRequest(BaseModel):
    task_type: str = Field(..., description="Task-Typ: chat, code, reasoning, embedding, vision, supervisor")
    context_length: int = Field(default=0, ge=0, description="Geschätzte Kontext-Länge in Tokens")
    prefer_fast: bool = Field(default=False, description="Schnelles Modell bevorzugen")
    agent: Optional[str] = Field(default=None, description="Anfragender Agent")


class RouteResponse(BaseModel):
    task_type: str
    model: str
    fallback_model: str
    available: bool
    reason: str


class HealthResponse(BaseModel):
    status: str
    service: str
    ollama_reachable: bool
    available_models: List[str]


_available_models_cache: List[str] = []


async def _get_available_models() -> List[str]:
    """Holt verfügbare Modelle von Ollama (gecacht)."""
    global _available_models_cache
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                _available_models_cache = [m["name"] for m in models]
    except Exception:
        pass
    return _available_models_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _get_available_models()
    yield


app = FastAPI(
    title="kirobi-model-routing",
    version="1.0.0",
    description="Intelligente Modell-Selektion für OpenDisruption",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health-Check mit verfügbaren Modellen."""
    models = await _get_available_models()
    return HealthResponse(
        status="ok" if models else "degraded",
        service="kirobi-model-routing",
        ollama_reachable=bool(models),
        available_models=models,
    )


@app.post("/route", response_model=RouteResponse)
async def route_model(request: RouteRequest) -> RouteResponse:
    """
    Wählt das optimale Modell für einen Task-Typ.
    
    Berücksichtigt:
    - Task-Typ (code, reasoning, chat, etc.)
    - Verfügbare Modelle in Ollama
    - Kontext-Länge (große Kontexte → größere Modelle)
    - prefer_fast Flag
    """
    routing = MODEL_ROUTING.get(request.task_type)
    if not routing:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannter Task-Typ: '{request.task_type}'. Erlaubt: {list(MODEL_ROUTING.keys())}",
        )

    available = await _get_available_models()
    primary = routing["primary"]
    fallback = routing["fallback"]

    # Modell-Auswahl-Logik
    if request.prefer_fast:
        # Schnelles Modell bevorzugen → Fallback zuerst prüfen
        selected = fallback if fallback in available else primary
        reason = "prefer_fast: kleinstes verfügbares Modell"
    elif primary in available:
        selected = primary
        reason = f"Primär-Modell für {request.task_type} verfügbar"
    elif fallback in available:
        selected = fallback
        reason = f"Fallback-Modell (Primär '{primary}' nicht verfügbar)"
    else:
        # Kein konfiguriertes Modell verfügbar → erstes verfügbares
        selected = available[0] if available else primary
        reason = "Kein konfiguriertes Modell verfügbar — erstes verfügbares Modell"

    return RouteResponse(
        task_type=request.task_type,
        model=selected,
        fallback_model=fallback,
        available=selected in available,
        reason=reason,
    )


@app.get("/models")
async def list_models() -> dict:
    """Listet alle verfügbaren Ollama-Modelle."""
    models = await _get_available_models()
    return {"models": models, "count": len(models), "routing_table": MODEL_ROUTING}


@app.get("/routing-table")
async def routing_table() -> dict:
    """Zeigt die vollständige Routing-Tabelle."""
    return {"routing": MODEL_ROUTING, "task_types": list(MODEL_ROUTING.keys())}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
