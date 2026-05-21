# Changelog: Kirobi / Disruptive OS

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.  
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Unreleased]

### Geplant
- Vollständige Flowise-Workflow-Konfigurationen
- Agent-Implementations in Python/Node.js
- Automatisierte Test-Suite

---

## [music-generation 1.0.2] – 2026-05-21 – T5EncoderModel-Referenz auf OPE-212 erweitert (OPE-212)

### Dokumentiert

**services/music-generation/README.md — OPE-212 Referenz ergänzt**

Die bestehende Warndokumentation (seit OPE-164) wurde um die Ticket-Referenz OPE-212 ergänzt.
Der Eintrag bestätigt: T5EncoderModel Lazy-Loading über den transformers CPU-Pfad ist dauerhaft
als bekanntes, nicht-kritisches Verhalten klassifiziert. Kein Handlungsbedarf.

- **Datei:** `services/music-generation/README.md` → Abschnitt "Bekannte Warnungen"
- **Referenz im README:** OPE-164, OPE-212

---

## [music-generation 1.0.1] – 2026-05-21 – T5EncoderModel-Warnung dokumentiert (OPE-164)

### Dokumentiert

**services/music-generation — T5EncoderModel Lazy-Loading via transformers CPU-Pfad**

Beim Start des music-generation Service (Port 8013) erscheint beim ersten Laden von MusicGen
eine transformers-Initialisierungs-Warnung zu `T5EncoderModel`. Diese wurde als bekanntes,
**nicht-kritisches Verhalten** identifiziert und in `README.md` festgehalten:

- **Ursache:** audiocraft 1.3.0 nutzt T5 als frozen Text-Konditionierungs-Encoder;
  transformers lädt dessen Gewichte über den CPU-Fallback-Pfad und gibt eine Hinweismeldung aus.
- **Auswirkung:** keine — Gewichte korrekt geladen, Audio-Jobs funktionieren fehlerfrei.
- **Optional unterdrücken:** `TRANSFORMERS_VERBOSITY=error` in `.env` / Compose setzen.
- **Referenz:** OPE-164

---

## [Run-105+] – 2026-05-21 – Fixture-Dokumentation (tests/conftest.py)

### Hinzugefügt

**Pytest-Fixture-Tabelle (ab Run 105 explizit dokumentiert)**

Die folgende Tabelle beschreibt alle Fixtures in `tests/conftest.py` und ihrem Verhalten:

| Fixture | Scope | Beschreibung |
|---|---|---|
| `_register_hyphenated_service` | session (helper) | Registriert Services mit Bindestrich-Verzeichnissen als importierbares Namespace-Paket im `sys.modules` (z.B. `model-routing` → `services.model_routing`) |
| `pytest_ignore_collect` | global hook | Überspringt optionale Service-Tests automatisch wenn Service-Stack-Dependencies (fastapi, asyncpg, etc.) fehlen — ermöglicht Baseline-Tests auf frischem Clone ohne Installation |

**Optionale Service-Stack-Module (geprüft beim Test-Collect):**
`asyncpg`, `dotenv`, `email_validator`, `fastapi`, `httpx`, `jose`, `multipart`, `passlib`, `qdrant_client`, `uvicorn`

**Optionale Service-Tests (werden bei fehlenden Deps übersprungen):**
- `test_analytics_service.py`
- `test_api_service.py`
- `test_auth_service.py`
- `test_embeddings_service.py`
- `test_image_generation_service.py`
- `test_ingest_service.py`
- `test_keycodi_telegram_responder.py`
- `test_media_processing_service.py`
- `test_model_routing_service.py`
- `test_music_generation_service.py`
- `test_personal_memory_pipeline_contract.py`
- `test_retrieval_service.py`
- `test_telegram_service.py`
- `test_video_generation_service.py`

**Hyphenated Services (registriert via `_register_hyphenated_service`):**
| Verzeichnis | Python-Modul |
|---|---|
| `services/model-routing` | `services.model_routing` |
| `services/image-generation` | `services.image_generation` |
| `services/media-processing` | `services.media_processing` |
| `services/music-generation` | `services.music_generation` |
| `services/video-generation` | `services.video_generation` |
| `services/analytics-service` | `services.analytics_service` |

### Hinweise
- Baseline-Tests (`tests/unit/test_zones.py` etc.) laufen ohne jede optionale Dep.
- CI-Gate: `make integration-test` führt Unit-Tests + Compose-Validierung + Script-Syntax-Checks durch.
- Fixture-Design: stdlib-first, kein Install nötig für normalen Unit-Test-Lauf.

---

## [0.1.0] – 2024 – Initiale Projektstruktur

### Hinzugefügt
- Vollständige Verzeichnis- und Dateistruktur für Kirobi / Disruptive OS
- `README.md` mit Projektübersicht, Architektur und Schnellstart
- `PROJECT-CHARTER.md` mit Vision, Mission, Prinzipien und Stakeholdern
- `ROADMAP.md` mit dreiphasigem Entwicklungsplan (MVP → Expand → Enterprise)
- `CONTRIBUTING.md` mit Richtlinien für Menschen und KI-Agenten
- `docker-compose.yml` mit Ollama, Open WebUI, Qdrant, PostgreSQL, Flowise
- `.env.example` mit allen Umgebungsvariablen und Kommentaren
- `Makefile` mit Management-Targets (up, down, logs, pull-models, etc.)
- `.gitignore` für Python, Node.js, Docker, Secrets, ML-Modelle

**Metadata-Verzeichnis:**
- `AGENTREGISTRY.md` – 14 Agenten mit Rollen, Berechtigungen, Modellen
- `MODEL-REGISTRY.md` – Lokale und Cloud-Modelle
- `ZONE-POLICY-MATRIX.md` – Zonenbasierte Zugriffsrechte
- `SYSTEMCONFIG.md` – Systemkonfiguration
- `BOOT-SEQUENCE.md` – Boot-Sequenz-Dokumentation
- `SECURITY-CLASSIFICATION.md` – Sicherheitsklassifizierung
- `EMBEDDINGSCHEMA.md` – Embedding- und Chunking-Regeln
- `FOLDERMANIFEST.md` – Vollständiges Verzeichnis-Manifest
- `COLLECTION-MAPPING.md` – Qdrant-Collection-Mapping
- `EVENT-TAXONOMY.md` – Event-Typen und Taxonomie
- `TAG-TAXONOMY.md` – Tag-System
- `AQAL-TAXONOMY.md` – Integrale Theorie Taxonomie
- `RETENTION-POLICY.md` – Datenaufbewahrungs-Policies
- `BACKUP-POLICY.md` – Backup-Strategie
- `REVIEW-MATRIX.md` – Review-Anforderungen
- `TEMPLATE-LIBRARY.md` – Template-Bibliothek
- `API-CATALOG-SCHEMA.md` – API-Katalog-Schema

**Kirobi-Core:**
- Kernidentität, Kontext, Routing, Policies
- Agenten-Prompts für alle 8 Core-Agenten
- Schemas für Events, Routing, Kontext, Policies

**Erfahrungs-Verzeichnisse:**
- `experiences/family/` – Familien-Erfahrungen (Sven, Samira, Sineo)
- `experiences/projects/` – 7 aktive Projekte
- `experiences/learnings/` – Lernpunkte und Best Practices
- `experiences/experiments/` – Experimente und Tests
- `experiences/knowledge/` – Wissensartikel

**Infra-Skripte:**
- `init-folders.sh` – Erstellt alle erforderlichen Verzeichnisse
- `healthcheck.sh` – Überprüft alle Dienste
- `pull-models.sh` – Lädt Ollama-Modelle herunter
- `bootstrap.sh` – Vollständiges Bootstrap-Skript

**Alle weiteren Verzeichnisse:**
- sources/, extracts/, clusters/, canon/
- analytics/, integrations/, apps/, services/
- models/, prompts/, templates/, research/
- tests/, quarantine/, sacred/, archive/

### Technische Details
- Sprache: Deutsch (außer technische Terms)
- Zonen: PUBLIC, WORKSPACE, FAMILY_PRIVATE, QUARANTINE, SACRED
- Agenten: 14 spezialisierte Agenten
- Modelle: Ollama-basiert (lokal) + optionale Cloud-APIs

---

## Versionsschema

```
MAJOR.MINOR.PATCH
  │      │     └── Fehlerbehebungen, kleine Anpassungen
  │      └──────── Neue Features, neue Agenten, neue Integrationen
  └─────────────── Breaking Changes, große Architektur-Änderungen
```

---

[Unreleased]: https://github.com/Kirobi92/OpenDisruption/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Kirobi92/OpenDisruption/releases/tag/v0.1.0
