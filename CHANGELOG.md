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
