# Agent-Registry: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE | **Verwaltet von:** kirobi-architect

---

## Übersicht

Das Kirobi-Ökosystem umfasst 14 spezialisierte Agenten, die als Flowise-Flows implementiert sind und über Kirobi Core orchestriert werden.

---

## 1. kirobi-core (Supervisor)

**Rolle:** Haupt-Orchestrator und Supervisor aller Agenten  
**Modell:** llama3.1:70b  
**Zone-Zugriff:** Alle Zonen (außer direkte SACRED-Schreibzugriffe)

### Berechtigungen
- ✅ Routing zu anderen Agenten
- ✅ Lesen aller Zonen
- ✅ Schreiben in PUBLIC, WORKSPACE
- ✅ Schreiben in FAMILY_PRIVATE mit Logging
- ❌ Direkte SACRED-Schreibzugriffe
- ✅ Human-in-the-Loop aktivieren

### Werkzeuge
- Qdrant-Suche (alle Collections)
- PostgreSQL-Abfragen
- Agent-Dispatcher
- Event-Logger
- Context-Manager

### System-Prompt-Datei
`kirobi-core/core-prompts/supervisor-system-prompt.md`

---

## 2. kirobi-architect

**Rolle:** System-Design, Planung, Architektur-Entscheidungen  
**Modell:** deepseek-r1:32b (Reasoning-Modell)  
**Zone-Zugriff:** PUBLIC, WORKSPACE

### Berechtigungen
- ✅ Architektur-Dokumente erstellen und aktualisieren
- ✅ Schema-Änderungen vorschlagen
- ✅ Roadmap-Updates
- ❌ Direkter Code-Deployment
- ❌ Produktionsdaten-Zugriff ohne Review

### Werkzeuge
- Qdrant (canon/, metadata/)
- Markdown-Editor
- Diagram-Generator (Mermaid)
- Git-Interface (read-only)

### System-Prompt-Datei
`kirobi-core/core-prompts/architect-prompt.md`

---

## 3. kirobi-coder

**Rolle:** Code-Entwicklung, Debugging, Code-Reviews  
**Modell:** qwen2.5-coder:32b  
**Zone-Zugriff:** PUBLIC, WORKSPACE

### Berechtigungen
- ✅ Code schreiben und editieren (in /services, /apps, /infra)
- ✅ Unit-Tests erstellen
- ✅ Code-Review-Kommentare
- ❌ Produktions-Deployment ohne kirobi-ops
- ❌ Zugriff auf Datenbanken in Production

### Werkzeuge
- Code-Ausführung (Sandbox)
- Git-Interface
- Linter und Formatter
- Test-Runner
- Docker-Build

### System-Prompt-Datei
`kirobi-core/core-prompts/coder-prompt.md`

---

## 4. kirobi-ops

**Rolle:** DevOps, Infrastruktur, Deployment, Monitoring  
**Modell:** llama3.1:8b  
**Zone-Zugriff:** PUBLIC, WORKSPACE

### Berechtigungen
- ✅ Docker-Container management
- ✅ Backup-Ausführung
- ✅ Service-Neustart
- ✅ Log-Analyse
- ❌ Schema-Änderungen ohne kirobi-architect
- ❌ Sicherheits-Policy-Änderungen

### Werkzeuge
- Docker API
- Shell-Befehle (eingeschränkt)
- Monitoring-APIs
- Backup-Skripte
- Healthcheck-Runner

### System-Prompt-Datei
`kirobi-core/core-prompts/ops-prompt.md`

---

## 5. kirobi-observer

**Rolle:** Monitoring, Analyse, Mustererkennung, proaktive Berichte  
**Modell:** mistral:7b  
**Zone-Zugriff:** Lesen aller Zonen (außer SACRED)

### Berechtigungen
- ✅ Lesen aller nicht-SACRED Zonen
- ✅ Analytics-Schreiben
- ✅ Alerts generieren
- ❌ Direktes Schreiben in andere Verzeichnisse
- ❌ Agent-Aktionen auslösen (nur Empfehlungen)

### Werkzeuge
- Qdrant-Suche (alle zugänglichen Collections)
- PostgreSQL-Abfragen (Read-Only)
- Metrics-APIs
- Alert-System
- Report-Generator

### System-Prompt-Datei
`kirobi-core/core-prompts/observer-prompt.md`

---

## 6. hermes-extractor

**Rolle:** Datenextraktion, Ingestion, Transformation aus sources/ nach extracts/  
**Modell:** mistral:7b  
**Zone-Zugriff:** sources/ (Lesen), extracts/ (Schreiben), quarantine/ (Schreiben)

### Berechtigungen
- ✅ sources/ lesen und verarbeiten
- ✅ extracts/ erstellen und aktualisieren
- ✅ quarantine/ bei Fehlern schreiben
- ❌ canon/ direkt schreiben
- ❌ SACRED-Inhalte verarbeiten ohne explizite Freigabe

### Werkzeuge
- Dokument-Parser (PDF, DOCX, HTML)
- Bild-OCR
- Audio-Transkription (Whisper)
- Qdrant-Ingest
- Metadata-Extraktor

### System-Prompt-Datei
`kirobi-core/core-prompts/hermes-prompt.md`

---

## 7. samira-heart-agent

**Rolle:** Familien-Mediation, emotionale Unterstützung, Herzensthemen  
**Modell:** llama3.1:8b  
**Zone-Zugriff:** FAMILY_PRIVATE (Lesen/Schreiben mit Logging), WORKSPACE

### Berechtigungen
- ✅ experiences/family/ lesen und schreiben
- ✅ Mediation-Protokolle erstellen
- ✅ Manometer-Einträge
- ❌ SACRED ohne explizite Einladung
- ❌ Externe APIs mit familiären Daten

### Werkzeuge
- Qdrant (family-collections)
- Sentiment-Analyse
- Kalender-Integration
- Mediation-Protokoll-Generator
- Ritual-Tracker

### System-Prompt-Datei
`kirobi-core/core-prompts/heart-agent-prompt.md`

---

## 8. sineo-creator-coach

**Rolle:** Creator-Coaching, YouTube-Strategie, Kreativitäts-Unterstützung für Sineo  
**Modell:** llama3.1:8b  
**Zone-Zugriff:** WORKSPACE, FAMILY_PRIVATE (Sineo-spezifisch)

### Berechtigungen
- ✅ experiences/family/sineo* lesen und schreiben
- ✅ experiences/projects/sineo* lesen und schreiben
- ✅ Coaching-Protokolle erstellen
- ❌ Eltern-Daten ohne Einwilligung
- ❌ Social-Media-Posts direkt veröffentlichen

### Werkzeuge
- YouTube Analytics API
- Content-Planner
- Script-Generator
- Thumbnail-Ideen (beschreibend)
- Trend-Analyse

### System-Prompt-Datei
`kirobi-core/core-prompts/creator-coach-prompt.md`

---

## 9. research-crew

**Rolle:** Web-Recherche, Marktanalyse, Technologie-Scouting  
**Modell:** Perplexica + llama3.1:70b  
**Zone-Zugriff:** PUBLIC, WORKSPACE

### Berechtigungen
- ✅ Web-Suchen durchführen
- ✅ research/ Verzeichnis befüllen
- ✅ Zusammenfassungen und Reports erstellen
- ❌ Persönliche Daten in Suchanfragen
- ❌ Kostenpflichtige APIs ohne Genehmigung

### Werkzeuge
- Perplexica (Web-Suche)
- Arxiv-Zugang
- GitHub-API
- News-Aggregator
- Citation-Manager

---

## 10. mediation-crew

**Rolle:** Multi-Agent-Konfliktlösung, Familien-Dynamiken  
**Modell:** llama3.1:8b (multi-perspective)  
**Zone-Zugriff:** FAMILY_PRIVATE

### Berechtigungen
- ✅ Mediation-Protokolle lesen und schreiben
- ✅ Perspektiven-Analyse
- ✅ Lösungsvorschläge generieren
- ❌ Entscheidungen treffen (nur unterstützen)
- ❌ SACRED ohne explizite Einladung

### Werkzeuge
- Familien-Kontext-Abruf aus Qdrant
- Perspektiven-Generator
- Protokoll-Manager
- NVC-Framework (Gewaltfreie Kommunikation)

---

## 11. creative-agent

**Rolle:** Kreative Inhalte, Storytelling, Brainstorming, Texte  
**Modell:** llama3.1:70b  
**Zone-Zugriff:** PUBLIC, WORKSPACE

### Berechtigungen
- ✅ Kreative Texte erstellen
- ✅ Ideen-Brainstorming
- ✅ Skript- und Content-Erstellung
- ❌ Private Inhalte veröffentlichen
- ❌ Urheberrechtlich geschütztes Material kopieren

### Werkzeuge
- Textgenerator
- Bild-Prompts (für DALL-E/SD)
- Musik-Ideen-Generator
- Story-Planner

---

## 12. voice-agent

**Rolle:** Sprach-Interface, STT/TTS, Voice-Kommandos  
**Modell:** Whisper (STT) + Piper/Coqui (TTS)  
**Zone-Zugriff:** Abhängig von Kontext (delegiert an kirobi-core)

### Berechtigungen
- ✅ Sprache transkribieren (lokal)
- ✅ Text vorlesen
- ✅ Voice-Kommandos an kirobi-core weiterleiten
- ❌ Sprachaufnahmen ohne aktive Sitzung
- ❌ Cloud-STT für sensible Inhalte

### Werkzeuge
- Whisper (lokal)
- Piper TTS
- Wake-Word-Erkennung
- Rhasspy/OpenHome-Integration

---

## 13. installer-agent

**Rolle:** Onboarding, Setup-Wizard, System-Installation  
**Modell:** llama3.1:8b  
**Zone-Zugriff:** Nur während Installation (temporär erhöht)

### Berechtigungen
- ✅ System-Setup durchführen
- ✅ Konfigurationsdateien erstellen
- ✅ Docker-Services starten
- ❌ Bestehende Produktionsdaten modifizieren
- ❌ Nach Installation: Zugriff automatisch eingeschränkt

### Werkzeuge
- Bootstrap-Skripte
- Konfigurations-Generator
- Dependency-Checker
- Health-Validator

---

## 14. enterprise-agent

**Rolle:** Business-Prozesse, Enterprise-Workflows, Client-Management  
**Modell:** llama3.1:70b  
**Zone-Zugriff:** WORKSPACE, PUBLIC

### Berechtigungen
- ✅ Business-Dokumente erstellen
- ✅ CRM-Daten lesen und aktualisieren
- ✅ Reports und Analysen
- ❌ FAMILY_PRIVATE
- ❌ Externe Kommunikation ohne Review

### Werkzeuge
- M365-Integration
- Enventa/ERP-Connector
- Reporting-Engine
- E-Mail-Drafting
- Projekt-Tracking

---

## Agent-Kommunikations-Matrix

| Von / An | core | architect | coder | ops | observer | hermes | samira | sineo |
|----------|------|-----------|-------|-----|----------|--------|--------|-------|
| **core** | – | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **architect** | ✅ | – | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **coder** | ✅ | ✅ | – | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ops** | ✅ | ✅ | ✅ | – | ✅ | ❌ | ❌ | ❌ |
| **observer** | ✅ | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ |
| **hermes** | ✅ | ❌ | ❌ | ❌ | ✅ | – | ❌ | ❌ |
| **samira** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | – | ✅ |
| **sineo** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | – |

---

## KIDI-Rollout: Neue Agenten (Phase 0 — Design)

> Status: Architektur dokumentiert, Runtime-Code folgt in Phasen 1–6. Siehe
> `docs/agent/MULTI-AGENT-ARCHITECTURE.md`, `AGENT-DECISION-MATRIX.md`,
> `docs/agent/CONTEXT-WINDOW.md`, `docs/agent/KIDI-ENGINE.md`,
> `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`,
> `docs/agent/TELEGRAM-INTEGRATION.md`.

### 15. opencode

- **Rolle:** Code-Generierung, Refactoring, CI/CD-Authoring, Test-Generierung.
- **Modell:** noch offen (Phase 2). Default-Vorschlag: lokales Coding-Modell aus `metadata/MODEL-REGISTRY.md`.
- **Zone-Zugriff:** Lesen PUBLIC, WORKSPACE — Schreiben PUBLIC, WORKSPACE.
- **Werkzeuge:** ContextDB, Git (read), Test-Runner. Commits/Deploys erfordern Human-Approval.
- **Quelle (geplant):** `agents/opencode/`.

### 16. openclaw

- **Rolle:** Tool-Use (Web, API, Filesystem, Browser-Automation) für PUBLIC/WORKSPACE-Daten.
- **Zone-Zugriff:** Lesen PUBLIC, WORKSPACE, QUARANTINE — Schreiben PUBLIC, WORKSPACE, QUARANTINE.
- **Hartes Verbot:** keine API-Calls, die FAMILY_PRIVATE/SACRED-Daten ausgehend transportieren.
- **Quelle (geplant):** `agents/openclaw/`.

### 17. hermes-reasoner

- **Rolle:** Mehrstufiges Reasoning, Pro/Contra-Debatte, Hypothesen-Validierung, Forschungssynthese.
  *Nicht zu verwechseln mit `hermes-extractor` (Ingestion-Agent, oben gelistet).*
- **Zone-Zugriff:** Lesen PUBLIC, WORKSPACE — Schreiben PUBLIC, WORKSPACE.
- **Quelle (geplant):** `agents/hermes/`.

### 18. obsidian

- **Rolle:** Obsidian-Vault-CRUD, Knowledge-Graph-Queries, Daily-Notes, MOCs.
- **Zone-Zugriff:** Lesen PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal) — Schreiben PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal, mit Approval).
- **Deployment-Zwang:** läuft nur auf Hosts mit `KIROBI_EGRESS_ALLOWED=false`.
- **Quelle (geplant):** `agents/obsidian/`.

### 19. kidi

- **Rolle:** Konfidenz-gewichtete Synthese über ContextDB-Einträge mehrerer Agenten; Konflikt-Erkennung.
- **Zone-Zugriff:** Lesen/Schreiben PUBLIC, WORKSPACE. Kein direkter FAMILY_PRIVATE/SACRED-Zugriff.
- **Garantie:** `output.zone <= min(input.zone)` — keine Zonen-Eskalation.
- **Quelle (geplant):** `kidi/core/`, `kidi/context_db/`.

### 20. keybrodi

- **Rolle:** Master-Orchestrator: Task-Routing gemäß `AGENT-DECISION-MATRIX.md`, Metrik-Sammlung in `kirobi-core/core-events.log`.
- **Zone-Zugriff:** Routing-Metadaten in WORKSPACE; **keine** Inhalte aus FAMILY_PRIVATE/SACRED.
- **Hart ausgeschlossen:** Selbst-modifizierender RL-Loop, prädiktive Orchestrierung ohne Human-PR.
- **Quelle (geplant):** `kidi/keybrodi/`.
