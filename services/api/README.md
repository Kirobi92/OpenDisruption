# services/api

**Verantwortlich:** kirobi-coder  
**Status:** Aktiv

## Zweck

FastAPI-Hauptservice für die unterstützten Clients. Er stabilisiert die Route-Verträge für Family PWA, Voice-UI und Dashboard.

## Kernaufgaben

- Chat-Kompatibilitätsendpoint für lokale Clients (`POST /chat`)
- persistierte Konversationen und Nachrichten
- Datei- und Text-Uploads inkl. Download, Metadaten und Zonenbindung
- UI-Suche über Retrieval **plus** lokalen Upload-Fallback (`POST /rag/search`)
- Dashboard-Task-Feed (`GET /tasks`)
- Dashboard-Aktivität für Operatoren (`GET /dashboard/activity`)
- Health-Probes für API, Datenbank und Qdrant

## Wichtige Endpunkte

| Methode | Pfad |
|---|---|
| `GET` | `/health`, `/health/db`, `/health/qdrant` |
| `POST` | `/chat`, `/rag/search`, `/upload`, `/uploads/text` |
| `GET` | `/conversations`, `/conversations/{id}`, `/conversations/{id}/messages` |
| `POST` | `/conversations`, `/conversations/{id}/messages` |
| `GET` | `/uploads`, `/uploads/{id}/download`, `/tasks`, `/dashboard/activity` |

## Hinweise

- Bootstrapt beim ersten Start die API-eigenen Tabellen `conversations`, `messages` und `file_uploads`
- Nutzt `auth` für Benutzerkontext und Zonen-Rechte
- SACRED und QUARANTINE werden im MVP-Flow explizit abgewiesen
