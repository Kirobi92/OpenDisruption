"""
Kirobi Embeddings Service
Zone: WORKSPACE
Zweck: Text-Embeddings via Ollama (nomic-embed-text) + Speicherung in Qdrant
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("embeddings-service")

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_DIM: int = int(os.getenv("EMBED_DIM", "768"))

ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Gültige Zonen gemäß Fünf-Zonen-Sicherheitsmodell
VALID_ZONES: frozenset[str] = frozenset(
    {"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"}
)

# ---------------------------------------------------------------------------
# Globale Clients
# ---------------------------------------------------------------------------
qdrant_client: AsyncQdrantClient | None = None
http_client: httpx.AsyncClient | None = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startet und beendet globale Clients."""
    global qdrant_client, http_client

    logger.info("Embeddings-Service wird gestartet …")
    logger.info("Ollama-Host: %s, Modell: %s", OLLAMA_HOST, EMBED_MODEL)
    logger.info("Qdrant: %s:%d", QDRANT_HOST, QDRANT_PORT)

    http_client = httpx.AsyncClient(timeout=60.0)
    qdrant_client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    logger.info("Embeddings-Service bereit.")
    yield

    logger.info("Embeddings-Service wird heruntergefahren …")
    if http_client:
        await http_client.aclose()
    if qdrant_client:
        await qdrant_client.close()
    logger.info("Embeddings-Service gestoppt.")


# ---------------------------------------------------------------------------
# FastAPI-App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Kirobi Embeddings Service",
    description="Text-Embeddings via Ollama + Qdrant-Speicherung für das OpenDisruption-Ökosystem",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Kein allow_credentials=True mit Wildcard-Origins
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------
class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Zu embeddender Text")


class EmbedResponse(BaseModel):
    embedding: list[float]
    model: str
    dimensions: int


class BatchEmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100, description="Liste von Texten")


class BatchEmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int
    count: int


class StoreRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Zu speichernder Text")
    zone: str = Field(..., description="Sicherheitszone (PUBLIC, WORKSPACE, …)")
    doc_type: str = Field(default="document", description="Dokumenttyp (z.B. document, note)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten")
    doc_id: str | None = Field(default=None, description="Optionale Dokument-ID (UUID)")


class StoreResponse(BaseModel):
    id: str
    collection: str
    zone: str
    dimensions: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    qdrant: str
    model: str


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _collection_name(zone: str, doc_type: str) -> str:
    """Gibt den Qdrant-Collection-Namen zurück: kirobi_{zone}_{type}."""
    return f"kirobi_{zone.lower()}_{doc_type.lower()}"


def _validate_zone(zone: str) -> None:
    """Wirft HTTPException wenn die Zone ungültig ist."""
    if zone not in VALID_ZONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Ungültige Zone '{zone}'. Erlaubt: {sorted(VALID_ZONES)}",
        )


async def _get_embedding(text: str) -> list[float]:
    """Ruft ein einzelnes Embedding von Ollama ab."""
    assert http_client is not None, "HTTP-Client nicht initialisiert"

    try:
        response = await http_client.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama HTTP-Fehler: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama hat einen Fehler zurückgegeben: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Ollama nicht erreichbar: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama ist nicht erreichbar. Bitte prüfe den OLLAMA_HOST.",
        ) from exc

    data = response.json()
    embedding: list[float] = data.get("embedding", [])
    if not embedding:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama hat kein Embedding zurückgegeben.",
        )
    return embedding


async def _ensure_collection(collection: str, vector_size: int) -> None:
    """Erstellt die Qdrant-Collection falls sie noch nicht existiert."""
    assert qdrant_client is not None, "Qdrant-Client nicht initialisiert"

    try:
        existing = await qdrant_client.get_collections()
        names = {c.name for c in existing.collections}
        if collection not in names:
            logger.info("Erstelle Qdrant-Collection '%s' (dim=%d) …", collection, vector_size)
            await qdrant_client.create_collection(
                collection_name=collection,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            logger.info("Collection '%s' erfolgreich erstellt.", collection)
    except Exception as exc:
        logger.error("Fehler beim Erstellen der Collection '%s': %s", collection, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Qdrant-Collection konnte nicht erstellt werden: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Prüft die Erreichbarkeit von Ollama und Qdrant.
    Gibt den Gesamtstatus zurück.
    """
    assert http_client is not None
    assert qdrant_client is not None

    ollama_status = "ok"
    qdrant_status = "ok"

    # Ollama prüfen
    try:
        resp = await http_client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Ollama Health-Check fehlgeschlagen: %s", exc)
        ollama_status = f"fehler: {exc}"

    # Qdrant prüfen
    try:
        await qdrant_client.get_collections()
    except Exception as exc:
        logger.warning("Qdrant Health-Check fehlgeschlagen: %s", exc)
        qdrant_status = f"fehler: {exc}"

    overall = "ok" if ollama_status == "ok" and qdrant_status == "ok" else "degradiert"

    return HealthResponse(
        status=overall,
        ollama=ollama_status,
        qdrant=qdrant_status,
        model=EMBED_MODEL,
    )


@app.post("/embed", response_model=EmbedResponse, tags=["Embeddings"])
async def embed_text(request: EmbedRequest) -> EmbedResponse:
    """
    Berechnet den Embedding-Vektor für einen einzelnen Text via Ollama.

    - **text**: Der zu embeddende Text (min. 1 Zeichen)
    """
    logger.info("Embedding-Anfrage für Text der Länge %d", len(request.text))
    embedding = await _get_embedding(request.text)
    return EmbedResponse(
        embedding=embedding,
        model=EMBED_MODEL,
        dimensions=len(embedding),
    )


@app.post("/embed/batch", response_model=BatchEmbedResponse, tags=["Embeddings"])
async def embed_batch(request: BatchEmbedRequest) -> BatchEmbedResponse:
    """
    Berechnet Embedding-Vektoren für mehrere Texte (max. 100).

    - **texts**: Liste von Texten
    """
    logger.info("Batch-Embedding-Anfrage für %d Texte", len(request.texts))

    embeddings: list[list[float]] = []
    for idx, text in enumerate(request.texts):
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Text an Position {idx} ist leer.",
            )
        vec = await _get_embedding(text)
        embeddings.append(vec)

    dimensions = len(embeddings[0]) if embeddings else 0
    logger.info("Batch-Embedding abgeschlossen: %d Vektoren, dim=%d", len(embeddings), dimensions)

    return BatchEmbedResponse(
        embeddings=embeddings,
        model=EMBED_MODEL,
        dimensions=dimensions,
        count=len(embeddings),
    )


@app.post("/store", response_model=StoreResponse, status_code=status.HTTP_201_CREATED, tags=["Speicherung"])
async def store_embedding(request: StoreRequest) -> StoreResponse:
    """
    Berechnet das Embedding für einen Text und speichert es in Qdrant.

    - **text**: Der zu speichernde Text
    - **zone**: Sicherheitszone (PUBLIC, WORKSPACE, FAMILY_PRIVATE, QUARANTINE, SACRED)
    - **doc_type**: Dokumenttyp (Standard: document)
    - **metadata**: Optionale Metadaten (werden als Payload gespeichert)
    - **doc_id**: Optionale UUID; wird automatisch generiert wenn nicht angegeben
    """
    assert qdrant_client is not None

    _validate_zone(request.zone)

    doc_id = request.doc_id or str(uuid.uuid4())
    collection = _collection_name(request.zone, request.doc_type)

    logger.info(
        "Speichere Dokument '%s' in Collection '%s' (Zone: %s)",
        doc_id,
        collection,
        request.zone,
    )

    # Embedding berechnen
    embedding = await _get_embedding(request.text)

    # Collection sicherstellen
    await _ensure_collection(collection, len(embedding))

    # Payload zusammenstellen — kein f-String mit User-Input in Queries
    payload: dict[str, Any] = {
        "text": request.text,
        "zone": request.zone,
        "doc_type": request.doc_type,
        **{k: v for k, v in request.metadata.items()},
    }

    # In Qdrant speichern
    try:
        await qdrant_client.upsert(
            collection_name=collection,
            points=[
                qdrant_models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )
    except Exception as exc:
        logger.error("Fehler beim Speichern in Qdrant: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Dokument konnte nicht in Qdrant gespeichert werden: {exc}",
        ) from exc

    logger.info("Dokument '%s' erfolgreich gespeichert.", doc_id)

    return StoreResponse(
        id=doc_id,
        collection=collection,
        zone=request.zone,
        dimensions=len(embedding),
    )
