#!/usr/bin/env python3
"""
OpenDisruption Knowledge Base Indexer
Zone: WORKSPACE

Indexiert alle Inhalte aus dem Repo in die Qdrant-Collections:
  - kirobi_workspace   → docs, extracts, metadata, prompts
  - kirobi_canon       → canon/ (ohne Family/Sacred)
  - kirobi_experiences → experiences/ (ohne family/)
  - kirobi_research    → research/
  - kirobi_code        → services/*.py, kirobi_core/*.py, apps/
  - kirobi_metadata    → metadata/
  - kirobi_public      → extracts/public/

Verwendung:
  python3 infra/scripts/index-knowledge-base.py [--dry-run] [--collection NAME]

Voraussetzungen:
  - Embeddings-Service auf Port 8004 (localhost)
  - Qdrant auf Port 6333 (localhost)
  - pip install qdrant-client httpx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Generator

try:
    import httpx
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm
except ImportError:
    print("ERROR: qdrant-client und httpx fehlen. Installieren mit:")
    print("  pip install qdrant-client httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
DATENSPEICHER = Path("/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL", "http://localhost:8004")
EMBED_DIM = 768
CHUNK_SIZE = 1000      # Zeichen pro Chunk
CHUNK_OVERLAP = 150    # Überlappung zwischen Chunks
BATCH_SIZE = 15        # Texte pro Embedding-Batch (nomic-embed-text ist langsam)

# Checkpoint-Datei für Resume-Fähigkeit
CHECKPOINT_FILE = REPO_ROOT / ".qdrant-index-checkpoint.json"

# User-Vault Pfade → Collections (FAMILY_PRIVATE)
USER_VAULTS: dict[str, str] = {
    str(DATENSPEICHER / "Sven"):   "kirobi_user_sven",
    str(DATENSPEICHER / "Samira"): "kirobi_user_samira",
    str(DATENSPEICHER / "Sineo"):  "kirobi_user_sineo",
}

# ---------------------------------------------------------------------------
# Pfad → Collection Mapping
# ---------------------------------------------------------------------------
PATH_RULES: list[tuple[str, str, str]] = [
    # (glob-like prefix, collection, zone)
    ("canon/public",       "kirobi_public",     "PUBLIC"),
    ("extracts/public",    "kirobi_public",     "PUBLIC"),
    ("canon",              "kirobi_canon",      "WORKSPACE"),
    ("experiences/projects", "kirobi_experiences", "WORKSPACE"),
    ("experiences/learnings", "kirobi_experiences", "WORKSPACE"),
    ("experiences/users",  "kirobi_experiences", "WORKSPACE"),
    ("research",           "kirobi_research",   "WORKSPACE"),
    ("metadata",           "kirobi_metadata",   "WORKSPACE"),
    ("extracts/workspace", "kirobi_workspace",  "WORKSPACE"),
    ("extracts/technical", "kirobi_workspace",  "WORKSPACE"),
    ("services",           "kirobi_code",       "WORKSPACE"),
    ("apps",               "kirobi_code",       "WORKSPACE"),
    ("kirobi_core",        "kirobi_code",       "WORKSPACE"),
    ("infra/scripts",      "kirobi_code",       "WORKSPACE"),
    ("prompts",            "kirobi_workspace",  "WORKSPACE"),
    ("docs",               "kirobi_workspace",  "WORKSPACE"),
    # Root-level docs
    ("",                   "kirobi_workspace",  "WORKSPACE"),
]

# Dateierweiterungen die indexiert werden
INCLUDE_EXTENSIONS = {".md", ".txt", ".rst", ".py", ".yaml", ".yml", ".toml", ".json"}
# Pfade die übersprungen werden (Prefix-Match gegen rel_path)
SKIP_PREFIXES = {
    "sacred/", "extracts/family-private/", "experiences/family/",
    "canon/family/", "clusters/family/", "quarantine/",
    ".git/", ".venv/", "__pycache__/", ".pytest_cache/",
    "data/piper-voices/", "services/nutzi/data/chapters/",  # Nutzi hat eigenen Indexer
    "archive/", ".kirobi/", "external/",  # externe Repos nicht indexieren
}
# Segmente die irgendwo im Pfad vorkommen dürfen → überspringen
SKIP_SEGMENTS = {
    "node_modules", "__pycache__", ".pytest_cache", ".next", ".next-build",
    ".svelte-kit", "build", "dist", ".cache", ".venv", ".env",
}
# Dateien die übersprungen werden
SKIP_FILES = {"package-lock.json", "yarn.lock", "Unbenannt.base"}
# Max. Dateigröße (Bytes) - ignoriere sehr große Dateien
MAX_FILE_SIZE = 200_000


def get_collection_for_path(rel_path: str) -> tuple[str, str]:
    """Gibt (collection, zone) für einen relativen Pfad zurück."""
    for prefix, collection, zone in PATH_RULES:
        if not prefix or rel_path.startswith(prefix):
            return collection, zone
    return "kirobi_workspace", "WORKSPACE"


def should_skip(rel_path: str) -> bool:
    """True wenn der Pfad übersprungen werden soll."""
    for skip in SKIP_PREFIXES:
        if rel_path.startswith(skip):
            return True
    # Segment-Check: node_modules, .next etc. irgendwo im Pfad
    parts = set(Path(rel_path).parts)
    if parts & SKIP_SEGMENTS:
        return True
    filename = Path(rel_path).name
    if filename in SKIP_FILES:
        return True
    ext = Path(rel_path).suffix.lower()
    if ext not in INCLUDE_EXTENSIONS:
        return True
    return False


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Teilt Text in überlappende Chunks auf."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Versuche am Satzende zu schneiden
        if end < len(text):
            last_newline = chunk.rfind("\n")
            last_period = chunk.rfind(". ")
            cut = max(last_newline, last_period)
            if cut > chunk_size // 2:
                chunk = text[start:start + cut + 1]
                end = start + cut + 1
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def file_hash(content: str) -> str:
    """SHA256 der Datei für Change-Detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def collect_files(repo_root: Path) -> Generator[tuple[Path, str, str, str], None, None]:
    """Yieldet (path, rel_path, collection, zone) für alle zu indexierenden Dateien."""
    # 1. Repo-Dateien
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = str(path.relative_to(repo_root))
        except ValueError:
            continue
        if should_skip(rel):
            continue
        if path.stat().st_size > MAX_FILE_SIZE:
            continue
        collection, zone = get_collection_for_path(rel)
        yield path, rel, collection, zone

    # 2. User-Vault-Dateien (Datenspeicher)
    for vault_path_str, collection in USER_VAULTS.items():
        vault_path = Path(vault_path_str)
        if not vault_path.exists():
            continue
        for path in sorted(vault_path.rglob("*")):
            if not path.is_file():
                continue
            if path.stat().st_size > MAX_FILE_SIZE:
                continue
            ext = path.suffix.lower()
            if ext not in INCLUDE_EXTENSIONS:
                continue
            # Skip .obsidian config files
            if ".obsidian" in path.parts:
                continue
            rel = f"vault:{vault_path.name}/{path.relative_to(vault_path)}"
            yield path, rel, collection, "FAMILY_PRIVATE"


def embed_batch(client: httpx.Client, texts: list[str]) -> list[list[float]] | None:
    """Embeddet eine Batch von Texten via Embeddings-Service."""
    try:
        resp = client.post(
            f"{EMBEDDINGS_URL}/embed/batch",
            json={"texts": texts},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]
    except Exception as e:
        print(f"  ⚠️  Embedding-Fehler: {e}")
        return None


def ensure_collections(qdrant: QdrantClient, collections: set[str]) -> None:
    """Erstellt fehlende Collections."""
    existing = {c.name for c in qdrant.get_collections().collections}
    for name in collections:
        if name not in existing:
            print(f"  📦 Erstelle Collection: {name}")
            qdrant.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(size=EMBED_DIM, distance=qm.Distance.COSINE),
            )


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"indexed": {}}


def save_checkpoint(cp: dict) -> None:
    CHECKPOINT_FILE.write_text(json.dumps(cp, indent=2))


def main():
    parser = argparse.ArgumentParser(description="OpenDisruption Knowledge Base Indexer")
    parser.add_argument("--dry-run", action="store_true", help="Nichts schreiben, nur zählen")
    parser.add_argument("--collection", help="Nur diese Collection indexieren")
    parser.add_argument("--force", action="store_true", help="Bereits indexierte Dateien neu indexieren")
    parser.add_argument("--reset", action="store_true", help="Checkpoint zurücksetzen (alles neu)")
    args = parser.parse_args()

    print("=" * 60)
    print("OpenDisruption Knowledge Base Indexer")
    print(f"Repo:       {REPO_ROOT}")
    print(f"Qdrant:     {QDRANT_URL}")
    print(f"Embeddings: {EMBEDDINGS_URL}")
    print(f"Dry-Run:    {args.dry_run}")
    print("=" * 60)

    # Checkpoint laden
    checkpoint = load_checkpoint()
    if args.reset:
        checkpoint = {"indexed": {}}
        print("🔄 Checkpoint zurückgesetzt.")

    # Services prüfen
    with httpx.Client(timeout=5.0) as hc:
        try:
            hc.get(f"{EMBEDDINGS_URL}/health").raise_for_status()
            print("✅ Embeddings-Service erreichbar")
        except Exception as e:
            print(f"❌ Embeddings-Service nicht erreichbar: {e}")
            sys.exit(1)
        try:
            hc.get(f"{QDRANT_URL}/healthz").raise_for_status()
            print("✅ Qdrant erreichbar")
        except Exception:
            try:
                hc.get(f"{QDRANT_URL}/collections").raise_for_status()
                print("✅ Qdrant erreichbar")
            except Exception as e:
                print(f"❌ Qdrant nicht erreichbar: {e}")
                sys.exit(1)

    # Dateien sammeln
    print("\n📂 Sammle Dateien...")
    files = list(collect_files(REPO_ROOT))
    if args.collection:
        files = [(p, r, c, z) for p, r, c, z in files if c == args.collection]
    print(f"  {len(files)} Dateien gefunden")

    # Collections prüfen
    needed_collections = {c for _, _, c, _ in files}
    print(f"\n📦 Benötigte Collections: {needed_collections}")

    if not args.dry_run:
        qdrant = QdrantClient(url=QDRANT_URL, timeout=30)
        ensure_collections(qdrant, needed_collections)
    else:
        qdrant = None

    # Statistiken
    stats = {
        "total_files": len(files),
        "skipped": 0,
        "processed": 0,
        "indexed_chunks": 0,
        "errors": 0,
        "by_collection": {},
    }

    # Alle Chunks sammeln für Batch-Verarbeitung
    pending_chunks: list[tuple[str, str, str, str, int, int, str]] = []
    # (text, collection, zone, rel_path, chunk_idx, total_chunks, file_hash)

    print("\n📖 Lese Dateien...")
    for path, rel, collection, zone in files:
        # Skip-Check via Checkpoint
        fhash = file_hash(path.read_text(encoding="utf-8", errors="ignore"))
        if not args.force and checkpoint["indexed"].get(rel) == fhash:
            stats["skipped"] += 1
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            stats["errors"] += 1
            continue

        # Für .py und .ts Dateien den Pfad als Kontext voranstellen
        ext = path.suffix.lower()
        if ext in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            text = f"# Datei: {rel}\n\n{text}"

        chunks = chunk_text(text)
        if not chunks:
            stats["skipped"] += 1
            continue

        for i, chunk in enumerate(chunks):
            pending_chunks.append((chunk, collection, zone, rel, i, len(chunks), fhash))

        stats["processed"] += 1
        stats["by_collection"][collection] = stats["by_collection"].get(collection, 0) + len(chunks)

    total_chunks = len(pending_chunks)
    print(f"  {stats['processed']} Dateien verarbeitet ({stats['skipped']} unverändert, {stats['errors']} Fehler)")
    print(f"  {total_chunks} Chunks zu indexieren")

    if args.dry_run:
        print("\n[DRY RUN] Keine Daten geschrieben.")
        print(f"\nStatistiken: {json.dumps(stats['by_collection'], indent=2)}")
        return

    if total_chunks == 0:
        print("\n✅ Alles bereits indexiert. Fertig!")
        return

    # Batch-Indexierung
    print(f"\n🚀 Indexiere {total_chunks} Chunks in Batches à {BATCH_SIZE}...")
    print("  (Das kann je nach Ollama-Geschwindigkeit 10-60 Minuten dauern)")

    with httpx.Client(timeout=120.0) as hc:
        processed_files_in_run: dict[str, str] = {}

        for batch_start in range(0, total_chunks, BATCH_SIZE):
            batch = pending_chunks[batch_start:batch_start + BATCH_SIZE]
            texts = [item[0] for item in batch]

            # Embeddings
            embeddings = embed_batch(hc, texts)
            if embeddings is None:
                print(f"  ⚠️  Batch {batch_start}-{batch_start+len(batch)} fehlgeschlagen, überspringe")
                stats["errors"] += len(batch)
                continue

            # Gruppiere nach Collection für Batch-Upsert
            by_collection: dict[str, list] = {}
            for i, (chunk, collection, zone, rel, chunk_idx, total, fhash) in enumerate(batch):
                if i >= len(embeddings):
                    break
                point = qm.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{rel}::{chunk_idx}")),
                    vector=embeddings[i],
                    payload={
                        "text": chunk,
                        "source_path": rel,
                        "zone": zone,
                        "chunk_index": chunk_idx,
                        "total_chunks": total,
                        "file_hash": fhash,
                        "language": "de",
                        "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    },
                )
                by_collection.setdefault(collection, []).append(point)
                processed_files_in_run[rel] = fhash

            # Upsert pro Collection
            for collection, points in by_collection.items():
                try:
                    qdrant.upsert(collection_name=collection, points=points)
                    stats["indexed_chunks"] += len(points)
                except Exception as e:
                    print(f"  ❌ Upsert-Fehler ({collection}): {e}")
                    stats["errors"] += len(points)

            # Progress
            done = min(batch_start + BATCH_SIZE, total_chunks)
            pct = done / total_chunks * 100
            print(f"  [{pct:5.1f}%] {done}/{total_chunks} Chunks | {stats['indexed_chunks']} gespeichert", end="\r")

            # Checkpoint regelmäßig sichern
            if batch_start % (BATCH_SIZE * 20) == 0:
                checkpoint["indexed"].update(processed_files_in_run)
                save_checkpoint(checkpoint)

    # Finaler Checkpoint
    checkpoint["indexed"].update(processed_files_in_run)
    save_checkpoint(checkpoint)

    print(f"\n\n{'='*60}")
    print("✅ Indexierung abgeschlossen!")
    print(f"  Dateien verarbeitet: {stats['processed']}")
    print(f"  Chunks indexiert:    {stats['indexed_chunks']}")
    print(f"  Fehler:              {stats['errors']}")
    print(f"  Übersprungen:        {stats['skipped']}")
    print("\nPro Collection:")
    for col, count in sorted(stats["by_collection"].items()):
        print(f"  {col:<30} {count:>5} Chunks")
    print("=" * 60)


if __name__ == "__main__":
    main()
