#!/usr/bin/env python3
"""
Qdrant Collections Init-Skript
Zone: WORKSPACE
Zweck: Erstellt die 7 Kirobi-Collections in Qdrant beim ersten Start.
       Idempotent — bereits vorhandene Collections werden übersprungen.

Verwendung:
    python infra/scripts/init-qdrant.py
    python infra/scripts/init-qdrant.py --dry-run
    QDRANT_URL=http://qdrant:6333 python infra/scripts/init-qdrant.py
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import os
from typing import Optional

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Collection-Definitionen gemäß metadata/COLLECTION-MAPPING.md
COLLECTIONS = [
    {
        "name": "kirobi_workspace",
        "description": "WORKSPACE-Wissen: Code, Docs, Configs",
        "zone": "WORKSPACE",
        "vector_size": 1024,    # bge-m3
        "distance": "Cosine",
    },
    {
        "name": "kirobi_family",
        "description": "FAMILY_PRIVATE: Familienwissen, persönliche Daten",
        "zone": "FAMILY_PRIVATE",
        "vector_size": 1024,    # bge-m3
        "distance": "Cosine",
    },
    {
        "name": "kirobi_canon",
        "description": "Canon: autorisiertes, geprüftes Wissen",
        "zone": "mixed",
        "vector_size": 1024,    # bge-m3
        "distance": "Cosine",
    },
    {
        "name": "kirobi_experiences",
        "description": "FAMILY_PRIVATE: Lernpfade, Projekte, Erlebnisse",
        "zone": "FAMILY_PRIVATE",
        "vector_size": 1024,    # bge-m3
        "distance": "Cosine",
    },
    {
        "name": "kirobi_public",
        "description": "PUBLIC: Allgemeines, öffentliches Wissen",
        "zone": "PUBLIC",
        "vector_size": 768,     # nomic-embed-text
        "distance": "Cosine",
    },
    {
        "name": "kirobi_code",
        "description": "WORKSPACE: Code-Embeddings für semantische Code-Suche",
        "zone": "WORKSPACE",
        "vector_size": 768,     # nomic-embed-text
        "distance": "Cosine",
    },
    {
        "name": "kirobi_quarantine",
        "description": "QUARANTINE: Noch nicht geprüfte Inhalte",
        "zone": "QUARANTINE",
        "vector_size": 768,     # nomic-embed-text
        "distance": "Cosine",
    },
]


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        h["api-key"] = QDRANT_API_KEY
    return h


def _request(method: str, path: str, body: Optional[dict] = None) -> tuple[int, dict]:
    url = f"{QDRANT_URL.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw_body = e.read()
        try:
            return e.code, json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            return e.code, {"error": raw_body.decode("utf-8", errors="replace")}
    except Exception as e:
        return 0, {"error": str(e)}


def collection_exists(name: str) -> bool:
    status, body = _request("GET", f"/collections/{name}")
    return status == 200


def create_collection(col: dict, dry_run: bool) -> bool:
    name = col["name"]
    if dry_run:
        print(f"  DRY   {name} — würde geprüft/erstellt (size={col['vector_size']}, zone={col['zone']})")
        return True

    if collection_exists(name):
        print(f"  SKIP  {name} (bereits vorhanden)")
        return True

    payload = {
        "vectors": {
            "size": col["vector_size"],
            "distance": col["distance"],
        },
        "optimizers_config": {
            "indexing_threshold": 20000,
        },
        "on_disk_payload": True,
    }

    status, body = _request("PUT", f"/collections/{name}", payload)
    if status in (200, 201):
        print(f"  OK    {name} (size={col['vector_size']}, zone={col['zone']})")
        return True
    else:
        print(f"  FAIL  {name} — HTTP {status}: {body}", file=sys.stderr)
        return False


def wait_for_qdrant(retries: int = 10, delay: float = 2.0) -> bool:
    import time
    for i in range(retries):
        status, _ = _request("GET", "/collections")
        if status == 200:
            return True
        print(f"  Warte auf Qdrant ({i+1}/{retries})...")
        time.sleep(delay)
    return False


def main():
    global QDRANT_URL

    parser = argparse.ArgumentParser(description="Kirobi Qdrant Collections initialisieren")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts erstellen")
    parser.add_argument("--qdrant-url", default=QDRANT_URL, help=f"Qdrant-URL (default: {QDRANT_URL})")
    args = parser.parse_args()

    QDRANT_URL = args.qdrant_url

    print(f"Kirobi Qdrant Init — {QDRANT_URL}")
    if args.dry_run:
        print("(DRY-RUN — keine Änderungen)")
    print()

    if not args.dry_run:
        print("Verbindung zu Qdrant prüfen...")
        if not wait_for_qdrant():
            print("FEHLER: Qdrant nicht erreichbar", file=sys.stderr)
            sys.exit(1)
        print("Qdrant erreichbar.\n")

    errors = 0
    for col in COLLECTIONS:
        ok = create_collection(col, args.dry_run)
        if not ok:
            errors += 1

    print()
    if errors:
        print(f"FEHLER: {errors} Collections konnten nicht erstellt werden", file=sys.stderr)
        sys.exit(1)
    else:
        mode = "DRY-RUN" if args.dry_run else "OK"
        print(f"{mode}: Alle {len(COLLECTIONS)} Collections verarbeitet.")


if __name__ == "__main__":
    main()
