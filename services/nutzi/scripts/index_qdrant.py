#!/usr/bin/env python3
"""
Nutzi Qdrant Indexer
Indexiert alle eNVenta Hilfe-Kapitel in die Qdrant Collection 'nutzi_enventa'.
Benötigt: laufender Embeddings-Service (Port 8004) und Qdrant (Port 6333).
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL", "http://embeddings:8000")
COLLECTION = "nutzi_enventa"
EMBEDDING_DIM = 768  # nomic-embed-text
CHAPTERS_DIR = Path(__file__).parent.parent / "data" / "chapters"
INDEX_PATH = Path(__file__).parent.parent / "data" / "master_index.json"
BATCH_SIZE = 20


def ensure_collection(client: httpx.Client):
    """Collection anlegen falls nicht vorhanden."""
    resp = client.get(f"{QDRANT_URL}/collections/{COLLECTION}")
    if resp.status_code == 200:
        print(f"Collection '{COLLECTION}' existiert bereits.")
        return

    payload = {
        "vectors": {
            "size": EMBEDDING_DIM,
            "distance": "Cosine",
        }
    }
    resp = client.put(f"{QDRANT_URL}/collections/{COLLECTION}", json=payload)
    resp.raise_for_status()
    print(f"Collection '{COLLECTION}' angelegt.")


def embed_texts(client: httpx.Client, texts: list[str]) -> list[list[float]]:
    """Embeddings via lokalen Embeddings-Service."""
    resp = client.post(
        f"{EMBEDDINGS_URL}/embed/batch",
        json={"texts": texts},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


def index_chapters(dry_run: bool = False):
    print(f"Nutzi Qdrant Indexer")
    print(f"Qdrant:     {QDRANT_URL}")
    print(f"Embeddings: {EMBEDDINGS_URL}")
    print(f"Collection: {COLLECTION}")

    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)

    chapters = index.get("chapters", [])
    print(f"Chapters to index: {len(chapters)}")

    if dry_run:
        print("[DRY RUN] Nothing written.")
        return

    with httpx.Client(timeout=30.0) as client:
        # Health check
        try:
            client.get(f"{QDRANT_URL}/healthz", timeout=5).raise_for_status()
        except Exception as e:
            print(f"ERROR: Qdrant nicht erreichbar: {e}")
            sys.exit(1)

        ensure_collection(client)

        # Process in batches
        total = 0
        for i in range(0, len(chapters), BATCH_SIZE):
            batch = chapters[i: i + BATCH_SIZE]
            texts = []
            valid_batch = []

            for chap in batch:
                chap_id = chap.get("chapter_id")
                path = CHAPTERS_DIR / f"{chap_id}.md"
                if not path.exists():
                    continue
                content = path.read_text(encoding="utf-8")
                # Use title + first 1500 chars for embedding
                title = chap.get("title", "")
                embed_text = f"{title}\n\n{content[:1500]}"
                texts.append(embed_text)
                valid_batch.append(chap)

            if not texts:
                continue

            try:
                embeddings = embed_texts(client, texts)
            except Exception as e:
                print(f"  Batch {i}-{i+len(batch)}: Embedding-Fehler: {e}")
                continue

            points = []
            for chap, vec in zip(valid_batch, embeddings):
                chap_id = chap.get("chapter_id")
                points.append({
                    "id": int(chap_id) if chap_id.isdigit() else hash(chap_id) % (2**31),
                    "vector": vec,
                    "payload": {
                        "chapter_id": chap_id,
                        "title": chap.get("title", ""),
                        "topics": chap.get("topics", []),
                        "source": "eNVenta 4.5 Onlinehilfe",
                        "zone": "WORKSPACE",
                        "char_count": chap.get("char_count", 0),
                    },
                })

            resp = client.put(
                f"{QDRANT_URL}/collections/{COLLECTION}/points",
                json={"points": points},
            )
            if resp.status_code not in (200, 201):
                print(f"  Batch {i}: Qdrant-Fehler {resp.status_code}: {resp.text[:200]}")
                continue

            total += len(points)
            if (i // BATCH_SIZE + 1) % 10 == 0:
                print(f"  Indexed {total}/{len(chapters)} chapters...")
            time.sleep(0.1)

    print(f"\nDone! {total} Kapitel indexiert in '{COLLECTION}'.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    index_chapters(dry_run=args.dry_run)
