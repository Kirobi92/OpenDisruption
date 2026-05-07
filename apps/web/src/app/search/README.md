---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Wissenssuche-Seite (`/search`)

Semantische Volltextsuche über alle Dokumente und Erfahrungen im Kirobi-Stack — zonenfilterbar.

## Was diese Seite tut

- **Semantische Suche**: Sendet eine Suchanfrage an `POST /api/rag/search` — der Retrieval-Service durchsucht Qdrant-Embeddings
- **Zonen-Filter**: Suche kann auf eine bestimmte Zone eingeschränkt werden (`PUBLIC`, `WORKSPACE`, `FAMILY_PRIVATE`) oder alle Zonen gleichzeitig durchsuchen
- **Ergebnisdarstellung**: Jedes Ergebnis zeigt Titel/Quelle, Relevanz-Score (farbkodiert), Zone-Badge, Textausschnitt und Datum
- **Lade-Skeleton**: Animierte Platzhalter während der Suche verhindern Layout-Sprünge

## Relevanz-Score

Der Score kommt direkt aus dem Qdrant-Cosine-Similarity-Ergebnis (0–1):

| Score | Farbe | Bedeutung |
|-------|-------|-----------|
| ≥ 80 % | Grün | Sehr hohe Relevanz |
| 50–79 % | Gelb | Mittlere Relevanz |
| < 50 % | Grau | Geringe Relevanz |

## API-Endpunkt

| Methode | Pfad | Body | Beschreibung |
|---------|------|------|--------------|
| `POST` | `/api/rag/search` | `{ query, zone? }` | Semantische Suche; `zone` weglassen = alle Zonen |

Der Retrieval-Service (Port 8006) blockiert SACRED-Zonen grundsätzlich mit HTTP 403 — das ist kein Bug.

## Authentifizierung

Erfordert ein gültiges JWT-Token in `localStorage` (`access_token`). Ohne Token wird auf `/` weitergeleitet.

## Bekannte Einschränkungen

- Keine Paginierung — alle Ergebnisse werden auf einmal geladen
- Qdrant-Collections müssen initialisiert sein (`python3 infra/scripts/init-qdrant.py`), sonst liefert die Suche leere Ergebnisse
- SACRED-Zone ist bewusst nicht als Filter-Option vorhanden (Retrieval-Service verweigert den Zugriff)
