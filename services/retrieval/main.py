"""
Kirobi Retrieval Service
Zone: WORKSPACE
Zweck: RAG-Retrieval via Qdrant — semantische Suche für alle Agenten
Port: 8006
"""
from __future__ import annotations

import os
from typing import List, Optional
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from urllib.parse import urlparse, urlunparse

try:
    from kirobi_core.qdrant_collections import ZONE_COLLECTIONS as _CANONICAL_ZONE_COLLECTIONS
except Exception:  # noqa: BLE001
    _CANONICAL_ZONE_COLLECTIONS = {
        "PUBLIC": ("kirobi_public",),
        "WORKSPACE": (
            "kirobi_workspace",
            "kirobi_code",
            "kirobi_canon",
            "kirobi_experiences",
            "kirobi_research",
            "kirobi_conversations",
            "kirobi_metadata",
        ),
        "FAMILY_PRIVATE": ("kirobi_family",),
    }

_INTERNAL_SERVICE_PORTS = {
    "embeddings": 8000,
}


def _service_url(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    target_port = _INTERNAL_SERVICE_PORTS.get(host)
    if not target_port or parsed.port in (None, target_port):
        return value.rstrip("/")
    netloc = f"{host}:{target_port}"
    return urlunparse(parsed._replace(netloc=netloc)).rstrip("/")


EMBEDDINGS_URL = _service_url(os.getenv("EMBEDDINGS_SERVICE_URL", "http://embeddings:8004"))
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
PORT = int(os.getenv("RETRIEVAL_SERVICE_PORT", "8006"))

ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Erlaubte Collections pro Zone (Zone-Enforcement)
ZONE_COLLECTIONS = {zone: list(collections) for zone, collections in _CANONICAL_ZONE_COLLECTIONS.items()}


def _zone_filter(zone: str) -> dict:
    """Erzeugt einen Qdrant-Filter, der Treffer strikt auf die angeforderte Zone begrenzt."""
    return {"must": [{"key": "zone", "match": {"value": zone}}]}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    zone: str = Field(default="WORKSPACE", pattern="^(PUBLIC|WORKSPACE|FAMILY_PRIVATE|QUARANTINE|SACRED)$")
    collection: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=50)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    family_private_approved: bool = False


class SearchResult(BaseModel):
    id: int | str
    score: float
    text: str
    source: Optional[str] = None
    zone: Optional[str] = None
    tags: List[str] = []


class SearchResponse(BaseModel):
    query: str
    zone: str
    results: List[SearchResult]
    collection: str
    total: int
    local_only: bool
    approval_required: bool
    family_private_approved: bool
    refusal_semantics: str


class HealthResponse(BaseModel):
    status: str
    service: str
    qdrant_reachable: bool
    embeddings_reachable: bool
    collections: List[str]


app = FastAPI(
    title="kirobi-retrieval",
    version="1.0.0",
    description="RAG-Retrieval-Service für OpenDisruption",
)

app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


async def _get_embedding(text: str) -> List[float]:
    """Holt Embedding vom Embeddings-Service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{EMBEDDINGS_URL}/embed/single",
            params={"text": text},
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Embeddings-Service nicht erreichbar",
            )
        return resp.json()["embedding"]


def _query_policy(zone: str, family_private_approved: bool = False) -> dict:
    if zone == "FAMILY_PRIVATE":
        if not family_private_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FAMILY_PRIVATE retrieval requires explicit local human approval.",
            )
        return {
            "local_only": True,
            "approval_required": True,
            "family_private_approved": True,
            "refusal_semantics": "family-private-requires-human-approval",
        }
    if zone == "QUARANTINE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="QUARANTINE search is refused until content has been reviewed.",
        )
    if zone == "SACRED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SACRED zone is not accessible via retrieval.",
        )
    return {
        "local_only": True,
        "approval_required": False,
        "family_private_approved": False,
        "refusal_semantics": "zone-aware",
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health-Check mit Qdrant- und Embeddings-Status."""
    qdrant_ok = False
    collections = []
    embeddings_ok = False

    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections")
            if resp.status_code == 200:
                qdrant_ok = True
                collections = [c["name"] for c in resp.json().get("result", {}).get("collections", [])]
        except Exception:
            pass
        try:
            resp = await client.get(f"{EMBEDDINGS_URL}/health")
            embeddings_ok = resp.status_code == 200
        except Exception:
            pass

    return HealthResponse(
        status="ok" if (qdrant_ok and embeddings_ok) else "degraded",
        service="kirobi-retrieval",
        qdrant_reachable=qdrant_ok,
        embeddings_reachable=embeddings_ok,
        collections=collections,
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Semantische Suche in Qdrant.
    
    Zone-Enforcement: Nur Collections der angeforderten Zone sind zugänglich.
    FAMILY_PRIVATE-Daten sind von PUBLIC/WORKSPACE-Anfragen isoliert.
    """
    policy = _query_policy(request.zone, request.family_private_approved)

    # Zone-Enforcement: Collection validieren
    allowed = ZONE_COLLECTIONS.get(request.zone, [])
    collection = request.collection or (allowed[0] if allowed else "kirobi_workspace")
    if collection not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Collection '{collection}' nicht erlaubt für Zone '{request.zone}'",
        )

    # Embedding für Query
    query_embedding = await _get_embedding(request.query)

    # Qdrant-Suche
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{collection}/points/search",
            json={
                "vector": query_embedding,
                "limit": request.limit,
                "score_threshold": request.score_threshold,
                "filter": _zone_filter(request.zone),
                "with_payload": True,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Qdrant Fehler: {resp.status_code}",
            )
        qdrant_results = resp.json().get("result", [])

    results = [
        SearchResult(
            id=r["id"],
            score=r["score"],
            text=r["payload"].get("text", ""),
            source=r["payload"].get("source"),
            zone=r["payload"].get("zone"),
            tags=r["payload"].get("tags", []),
        )
        for r in qdrant_results
    ]

    return SearchResponse(
        query=request.query,
        zone=request.zone,
        results=results,
        collection=collection,
        total=len(results),
        **policy,
    )


@app.post("/rag/search", response_model=SearchResponse)
async def rag_search(request: SearchRequest) -> SearchResponse:
    """Compatibility alias for older clients expecting /rag/search."""
    return await search(request)


@app.get("/collections")
async def list_collections() -> dict:
    """Listet alle verfügbaren Qdrant-Collections."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections")
            if resp.status_code == 200:
                cols = resp.json().get("result", {}).get("collections", [])
                return {"collections": cols, "count": len(cols)}
        except Exception:
            pass
    return {"collections": [], "count": 0, "error": "Qdrant nicht erreichbar"}


# ---------------------------------------------------------------------------
# RAG-Endpoint
# ---------------------------------------------------------------------------

class RagRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    zone: str = Field(default="WORKSPACE", pattern="^(PUBLIC|WORKSPACE|FAMILY_PRIVATE|QUARANTINE|SACRED)$")
    limit: int = Field(default=3, ge=1, le=10)
    score_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    family_private_approved: bool = False


class RagResponse(BaseModel):
    query: str
    zone: str
    context: str  # Zusammengebauter Kontext für LLM-Prompt
    sources: List[dict]
    total_results: int
    local_only: bool
    approval_required: bool
    family_private_approved: bool
    refusal_semantics: str


@app.post("/rag", response_model=RagResponse)
async def rag_query(request: RagRequest) -> RagResponse:
    """
    RAG: Embedding → Qdrant-Suche → Kontext für LLM.

    Zone-Enforcement: SACRED ist immer 403.
    Durchsucht alle Collections der angeforderten Zone und baut einen
    Kontext-String für den LLM-Prompt zusammen.
    """
    policy = _query_policy(request.zone, request.family_private_approved)

    # Embedding holen
    embedding = await _get_embedding(request.query)

    # Collections für Zone
    collections = ZONE_COLLECTIONS.get(request.zone, ["kirobi_workspace"])

    all_results: List[dict] = []
    async with httpx.AsyncClient(timeout=15.0) as qclient:
        for collection in collections:
            try:
                resp = await qclient.post(
                    f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{collection}/points/search",
                    json={
                        "vector": embedding,
                        "limit": request.limit,
                        "score_threshold": request.score_threshold,
                        "filter": _zone_filter(request.zone),
                        "with_payload": True,
                    },
                )
                if resp.status_code != 200:
                    continue
                for hit in resp.json().get("result", []):
                    all_results.append({
                        "text": hit["payload"].get("text", ""),
                        "source": hit["payload"].get("source", collection),
                        "score": hit["score"],
                        "zone": hit["payload"].get("zone", request.zone),
                    })
            except Exception:
                continue

    # Nach Score sortieren, Top-N nehmen
    all_results.sort(key=lambda x: x["score"], reverse=True)
    top = all_results[:request.limit]

    # Kontext zusammenbauen
    context_parts = [f"[{r['source']}]: {r['text']}" for r in top]
    context = "\n\n".join(context_parts)

    return RagResponse(
        query=request.query,
        zone=request.zone,
        context=context,
        sources=top,
        total_results=len(top),
        **policy,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
