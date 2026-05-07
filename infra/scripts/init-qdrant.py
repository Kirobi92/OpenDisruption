#!/usr/bin/env python3
# zone: WORKSPACE
"""
Qdrant Collections Initialisierung
Erstellt alle benötigten Collections für das Kirobi-Ökosystem (idempotent).

Verwendung:
    python3 infra/scripts/init-qdrant.py [--dry-run] [--qdrant-url URL]

Optionen:
    --dry-run           Zeigt an, was erstellt würde, ohne echte Requests zu senden.
    --qdrant-url URL    Überschreibt QDRANT_HOST/QDRANT_PORT (z.B. http://localhost:6333)

Umgebungsvariablen:
    QDRANT_HOST  - Qdrant-Hostname (Standard: localhost)
    QDRANT_PORT  - Qdrant-Port     (Standard: 6333)
"""

import os
import sys
import urllib.request
import urllib.error
import json
import argparse
from typing import Any

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

# Vektor-Dimension für nomic-embed-text
VECTOR_SIZE: int = 768

# Collections: Name → Beschreibung
# 7 Collections insgesamt (PUBLIC 1 + WORKSPACE 4 + FAMILY_PRIVATE 1 + SACRED 1)
COLLECTIONS: dict[str, str] = {
    "kirobi_public_documents":         "Öffentliche Dokumente (PUBLIC-Zone)",
    "kirobi_workspace_documents":      "Workspace-Dokumente (WORKSPACE-Zone)",
    "kirobi_workspace_code":           "Code-Artefakte (WORKSPACE-Zone)",
    "kirobi_workspace_notes":          "Notizen und Learnings (WORKSPACE-Zone)",
    "kirobi_workspace_research":       "Recherche-Ergebnisse (WORKSPACE-Zone)",
    "kirobi_family_private_documents": "Familien-Dokumente (FAMILY_PRIVATE-Zone)",
    "kirobi_sacred_documents":         "Vertrauliche Dokumente (SACRED-Zone)",
}


# ---------------------------------------------------------------------------
# HTTP-Hilfsfunktionen (stdlib-only, kein httpx/requests nötig)
# ---------------------------------------------------------------------------

def _request(base_url: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    """Führt einen HTTP-Request gegen Qdrant aus.

    Args:
        base_url: Basis-URL des Qdrant-Servers
        method:   HTTP-Methode (GET, PUT, DELETE, …)
        path:     URL-Pfad relativ zu base_url
        body:     Optionaler Request-Body (wird als JSON serialisiert)

    Returns:
        Tupel aus (HTTP-Statuscode, geparste JSON-Antwort oder None)
    """
    url = f"{base_url}{path}"
    data: bytes | None = None
    headers: dict[str, str] = {"Content-Type": "application/json"}

    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return resp.status, None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return exc.code, None


def collection_exists(base_url: str, name: str) -> bool:
    """Prüft ob eine Collection bereits existiert."""
    status, _ = _request(base_url, "GET", f"/collections/{name}")
    return status == 200


def create_collection(base_url: str, name: str) -> bool:
    """Erstellt eine Collection mit Cosine-Distanz und 768-dim Vektoren.

    Returns:
        True wenn erfolgreich erstellt, False bei Fehler.
    """
    payload = {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine",
        }
    }
    status, response = _request(base_url, "PUT", f"/collections/{name}", body=payload)
    if status in (200, 201):
        return True
    print(f"  FEHLER: HTTP {status} – {response}", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main() -> int:
    """Initialisiert alle Qdrant-Collections.

    Returns:
        Exit-Code: 0 = Erfolg, 1 = mindestens ein Fehler
    """
    parser = argparse.ArgumentParser(
        description="Qdrant Collections für das Kirobi-Ökosystem initialisieren"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Zeigt an, was erstellt würde, ohne echte Requests zu senden",
    )
    parser.add_argument(
        "--qdrant-url",
        default=None,
        help="Qdrant-URL überschreiben (z.B. http://localhost:6333)",
    )
    args = parser.parse_args()

    # Basis-URL bestimmen
    if args.qdrant_url:
        base_url = args.qdrant_url.rstrip("/")
    else:
        base_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

    dry_run: bool = args.dry_run

    if dry_run:
        print(f"[DRY-RUN] Würde Verbindung zu Qdrant unter {base_url} herstellen …")
    else:
        print(f"Verbinde mit Qdrant unter {base_url} …")

        # Verbindungstest
        status, _ = _request(base_url, "GET", "/healthz")
        if status != 200:
            # Qdrant < 1.x nutzt /health statt /healthz
            status, _ = _request(base_url, "GET", "/health")
        if status != 200:
            print(f"FEHLER: Qdrant nicht erreichbar (HTTP {status})", file=sys.stderr)
            return 1

        print("Verbindung erfolgreich.\n")

    errors: int = 0
    processed: int = 0

    for collection_name, description in COLLECTIONS.items():
        processed += 1

        if dry_run:
            print(f"  [DRY-RUN] Würde erstellen: {collection_name}  ({description})")
            continue

        if collection_exists(base_url, collection_name):
            print(f"  [ÜBERSPRUNGEN] {collection_name}  ← bereits vorhanden")
            continue

        print(f"  [ERSTELLE]     {collection_name}  ({description})")
        success = create_collection(base_url, collection_name)
        if success:
            print(f"  [OK]           {collection_name}")
        else:
            print(f"  [FEHLER]       {collection_name}", file=sys.stderr)
            errors += 1

    total = len(COLLECTIONS)
    print()

    if dry_run:
        print(f"[DRY-RUN] Alle {total} Collections verarbeitet (kein echter Request gesendet).")
        return 0

    if errors == 0:
        print(f"Initialisierung abgeschlossen – alle {total} Collections bereit.")
        return 0
    else:
        print(f"Initialisierung mit {errors} Fehler(n) abgeschlossen.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
