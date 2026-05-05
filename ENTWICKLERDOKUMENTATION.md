# Entwicklerdokumentation: Kirobi / Disruptive OS

**Version:** 1.0
**Datum:** 2026-05-05
**Zone:** WORKSPACE
**Zielgruppe:** Entwickler, technische Mitarbeiter, Contributor

---

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Codebase-Übersicht](#codebase-übersicht)
3. [Architektur im Detail](#architektur-im-detail)
4. [Service-Dokumentation](#service-dokumentation)
5. [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
6. [Entwicklungsworkflows](#entwicklungsworkflows)
7. [API-Dokumentation](#api-dokumentation)
8. [Datenbank-Schema](#datenbank-schema)
9. [Testing](#testing)
10. [Debugging](#debugging)
11. [Deployment](#deployment)
12. [Best Practices](#best-practices)
13. [Häufige Probleme](#häufige-probleme)
14. [Contribution Guidelines](#contribution-guidelines)

---

## Einführung

### Was ist Kirobi / Disruptive OS?

Kirobi ist ein **lokales, agenten-orchestriertes KI-Betriebssystem** für die persönliche und familiäre Nutzung. Es kombiniert:

- 🤖 **14 spezialisierte KI-Agenten** für verschiedene Lebensbereiche
- 🔒 **5-Zonen-Sicherheitsmodell** (PUBLIC → WORKSPACE → FAMILY_PRIVATE → QUARANTINE → SACRED)
- 🏠 **Local-First-Architektur** mit optionalen Cloud-APIs
- 📚 **Strukturiertes Wissensmanagement** mit 5-Schichten-Pipeline
- 🎙️ **Multimodale Interfaces** (Text, Sprache, zukünftig Bild/Video)

### Technologie-Stack

| Komponente | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | Python 3.10+ | FastAPI |
| **Frontend** | Next.js | 14+ |
| **Containerization** | Docker | 24+ |
| **Orchestration** | Docker Compose | v2+ |
| **Datenbank (Relational)** | PostgreSQL | 16 |
| **Datenbank (Vektor)** | Qdrant | latest |
| **LLM Server** | Ollama | latest |
| **Workflow Engine** | Flowise | latest |
| **GPU** | NVIDIA CUDA | 12.0+ |

---

## Codebase-Übersicht

### Repository-Struktur

```
OpenDisruption/
│
├── .agents/                   # GitHub Copilot Agent-Definitionen
├── .claude/                   # Claude Code-spezifische Konfiguration
├── .codex/                    # KI-generierte Code-Snippets
├── .env.example               # Umgebungsvariablen-Vorlage
├── .gitignore                 # Git-Ignore-Regeln
│
├── CLAUDE.md                  # ⚠️ PFLICHTLEKTÜRE für alle KI-Agenten
├── README.md                  # Projekt-Übersicht
├── PROJECT-CHARTER.md         # Vision, Mission, Prinzipien
├── ARCHITECTURE.md            # Architektur-Dokumentation
├── DEVELOPER-RUNBOOK.md       # Ops-Handbuch
├── SECURITY.md                # Sicherheitsrichtlinien
├── THREAT-MODEL.md            # Bedrohungsmodell
├── ROADMAP.md                 # Entwicklungs-Roadmap
├── CONTRIBUTING.md            # Contribution Guidelines
│
├── docker-compose.yml         # Service-Orchestrierung
├── Makefile                   # Build- und Betriebsbefehle
│
├── kirobi-core/               # ⭐ Kern-Identität und Supervisor
│   ├── core-identity.md
│   ├── core-policies.md
│   ├── core-routing.md
│   ├── core-events.log        # System-Event-Log
│   └── core-prompts/          # Agent System Prompts
│
├── services/                  # ⭐ Backend-Microservices
│   ├── orchestrator/          # Supervisor-Agent (Python)
│   │   └── supervisor.py
│   ├── api/                   # Haupt-API (FastAPI)
│   │   └── main.py
│   ├── auth/                  # Authentifizierung
│   │   └── main.py
│   ├── voice-processing/      # Sprach-Interface
│   │   ├── api.py
│   │   └── voice_interface.py
│   ├── embeddings/            # Embedding-Generierung
│   ├── ingest/                # Dokument-Ingestion
│   ├── retrieval/             # RAG-Suche
│   ├── model-routing/         # Modell-Router
│   └── analytics-service/     # Analytics & Monitoring
│
├── apps/                      # Frontend-Anwendungen
│   └── web/                   # Next.js Web-App
│       ├── pages/
│       ├── components/
│       └── styles/
│
├── infra/                     # Infrastruktur-Code
│   ├── scripts/               # Bash-Scripts
│   │   ├── bootstrap.sh       # System-Init
│   │   └── healthcheck.sh     # Gesundheitsprüfung
│   ├── docker/                # Dockerfiles
│   ├── compose/               # Docker Compose Erweiterungen
│   ├── db/                    # Datenbank-Migrations
│   ├── monitoring/            # Monitoring-Konfig
│   └── backups/               # Backup-Scripts
│
├── metadata/                  # ⭐ Governance & Registry
│   ├── AGENTREGISTRY.md       # Alle Agenten-Definitionen
│   ├── MODEL-REGISTRY.md      # Modell-Katalog
│   ├── ZONE-POLICY-MATRIX.md  # Zonen-Berechtigungen
│   ├── SECURITY-CLASSIFICATION.md
│   └── FOLDERMANIFEST.md      # Verzeichnisstruktur-Mapping
│
├── prompts/                   # LLM-Prompts und Templates
│   ├── agents/
│   ├── workflows/
│   └── templates/
│
├── models/                    # Modell-Konfigurationen
│   ├── ollama/
│   ├── embeddings/
│   └── configs/
│
├── integrations/              # Externe Integrationen
│   ├── m365/                  # Microsoft 365
│   ├── enventa/               # ERP-System
│   ├── perplexica/            # Web-Recherche
│   └── home-assistant/        # Smart Home
│
├── sources/                   # ⚠️ Rohdaten-Eingang (UNTRUSTED)
│   ├── inbox/
│   ├── imports/
│   ├── web-research/
│   └── apis/
│
├── extracts/                  # Verarbeitete, klassifizierte Daten
│   ├── public/                # PUBLIC Zone
│   ├── workspace/             # WORKSPACE Zone
│   ├── technical/             # WORKSPACE (Tech)
│   ├── business/              # WORKSPACE (Business)
│   └── family-private/        # FAMILY_PRIVATE Zone
│
├── clusters/                  # Semantisch geclusterte Knoten
│   └── [topic]/
│
├── canon/                     # ⭐ Kanonische Masterdokumente
│   ├── public/
│   ├── workspace/
│   └── family/
│
├── experiences/               # Lern- und Reflexionsdokumente
│   ├── projects/
│   ├── learnings/
│   ├── knowledge/
│   └── experiments/
│
├── analytics/                 # System-Metriken
│   └── dashboards/
│
├── sacred/                    # 🔐 Höchst vertraulich (SACRED Zone)
│
├── quarantine/                # ⚠️ Unverarbeitete, unsichere Daten
│
├── archive/                   # Archivierte Inhalte
│   └── snapshots/
│
├── research/                  # Forschungsprojekte
│
├── templates/                 # Vorlagen für Dokumente
│
└── tests/                     # Test-Suite
    ├── unit/
    ├── integration/
    ├── security/
    └── retrieval/
```

### Dateifluss und Pipeline

```
User Upload → sources/ → [hermes-extractor] → extracts/ → [clustering] → clusters/
                                                    ↓
                                            [Qdrant Embedding]
                                                    ↓
                                            [Canon Update] → canon/
                                                    ↓
                                            [Experience Capture] → experiences/
```

---

## Architektur im Detail

### Schichtenmodell

```
┌─────────────────────────────────────────┐
│     PRESENTATION LAYER                  │  Open WebUI, Flowise, Voice UI
├─────────────────────────────────────────┤
│     ORCHESTRATION LAYER                 │  kirobi-core (Supervisor)
│                                         │  14 spezialisierte Agenten
├─────────────────────────────────────────┤
│     KNOWLEDGE MANAGEMENT LAYER          │  5-Schichten-Pipeline
│     sources → extracts → clusters       │  → canon → experiences
├─────────────────────────────────────────┤
│     STORAGE LAYER                       │  Qdrant, PostgreSQL, Filesystem
├─────────────────────────────────────────┤
│     MODEL LAYER                         │  Ollama, BGE-M3, Cloud APIs
├─────────────────────────────────────────┤
│     INFRASTRUCTURE LAYER                │  Docker, GPU, Networking
└─────────────────────────────────────────┘
```

### Supervisor Pattern

**kirobi-core** fungiert als zentraler Supervisor, der alle Anfragen routet und koordiniert:

```python
def route_request(request: str) -> List[Agent]:
    intent = classify_intent(request)

    routing_map = {
        "code": [kirobi_coder],
        "architecture": [kirobi_architect],
        "family": [samira_heart_agent],
        "research": [research_crew],
        # ...
    }

    agents = routing_map.get(intent, [kirobi_core])

    # Filter by zone permissions
    required_zones = detect_zones(request)
    agents = [a for a in agents if a.can_access(required_zones)]

    return agents
```

### Agent-Kommunikationsprotokoll

Alle Agenten kommunizieren über **kirobi-core** (Stern-Topologie):

```
User → kirobi-core → [Intent Analysis] → Route to Agent(s)
                                              ↓
                                        Execute Task
                                              ↓
                                    Return to kirobi-core
                                              ↓
                                        Synthesize Response
                                              ↓
                                          User Response
```

**Nachrichtenformat:**

```json
{
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "from": "kirobi-core",
  "to": "kirobi-coder",
  "intent": "code_generation",
  "payload": {
    "task": "Create a Python function...",
    "context": {...},
    "zones": ["PUBLIC", "WORKSPACE"]
  },
  "metadata": {
    "user": "sven",
    "session_id": "uuid"
  }
}
```

---

## Service-Dokumentation

### 1. Supervisor Service

**Pfad:** `services/orchestrator/supervisor.py`
**Port:** N/A (interner Service)
**Zweck:** Zentraler Orchestrator, der 24/7 läuft und Aufgaben koordiniert

**Hauptkomponenten:**

```python
class KirobiSupervisor:
    async def initialize()          # DB-Verbindung, Schema-Init
    async def main_loop()           # Haupt-Kontrollschleife
    async def process_task_queue()  # Task-Verarbeitung
    async def route_to_agent()      # Agent-Routing
    async def health_check()        # System-Gesundheit
    async def log_event()           # Event-Logging
```

**Datenbank-Tabellen:**

- `supervisor_tasks` - Task-Queue
- `supervisor_events` - Event-Log

**Umgebungsvariablen:**

```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=kirobi
POSTGRES_USER=kirobi
POSTGRES_PASSWORD=changeme
OLLAMA_HOST=http://ollama:11434
SUPERVISOR_MODEL=llama3.1:70b
```

**Starten:**

```bash
docker compose up -d supervisor
docker compose logs -f supervisor
```

---

### 2. API Service

**Pfad:** `services/api/main.py`
**Port:** 8003
**Zweck:** Haupt-REST-API für Familie-Interaktionen

**Endpoints:**

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Gesundheitsstatus |
| `/conversations` | GET | Liste aller Konversationen |
| `/conversations` | POST | Neue Konversation erstellen |
| `/conversations/{id}` | GET | Spezifische Konversation abrufen |
| `/conversations/{id}/messages` | GET | Nachrichten abrufen |
| `/conversations/{id}/messages` | POST | Nachricht senden & KI-Antwort |
| `/upload` | POST | Datei hochladen |
| `/uploads` | GET | Liste hochgeladener Dateien |

**Beispiel: Nachricht senden**

```bash
curl -X POST http://localhost:8003/conversations/{conv_id}/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Wie geht es der Familie heute?",
    "attachments": []
  }'
```

**Antwort:**

```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant",
  "content": "Hallo! Basierend auf den letzten Einträgen...",
  "model_used": "llama3.1:8b",
  "created_at": "2026-05-05T10:30:00Z"
}
```

---

### 3. Auth Service

**Pfad:** `services/auth/main.py`
**Port:** 8002
**Zweck:** JWT-basierte Authentifizierung und Benutzerverwaltung

**Endpoints:**

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/register` | POST | Neuen Benutzer registrieren |
| `/token` | POST | JWT-Token erhalten |
| `/me` | GET | Aktuellen Benutzer abrufen |
| `/users` | GET | Alle Benutzer (Admin only) |

**Beispiel: Login**

```bash
curl -X POST http://localhost:8002/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=sven&password=mypassword"
```

**Antwort:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 4. Voice Processing Service

**Pfad:** `services/voice-processing/`
**Port:** 8001
**Zweck:** Sprach-zu-Text (STT) und Text-zu-Sprache (TTS)

**Technologien:**

- **STT:** Whisper Large v3 (lokal, GPU-beschleunigt)
- **TTS:** Piper oder Coqui TTS
- **Sprache:** Deutsch (konfigurierbar)

**Endpoints:**

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Service-Status |
| `/transcribe` | POST | Audio zu Text |
| `/synthesize` | POST | Text zu Audio |
| `/conversation/start` | POST | Konversation starten |
| `/conversation/{id}/speak` | POST | In Konversation sprechen |

**Beispiel: Transkription**

```bash
curl -X POST http://localhost:8001/transcribe \
  -F "audio=@recording.wav" \
  -F "language=de"
```

---

## Entwicklungsumgebung einrichten

### Voraussetzungen

```bash
# Minimal
- Docker 24+
- Docker Compose v2+
- Git 2.40+
- 32 GB RAM
- 500 GB SSD

# Empfohlen
- NVIDIA GPU mit 24+ GB VRAM
- CUDA 12.0+
- 64 GB RAM
- 1 TB NVMe SSD
- Ubuntu 22.04 LTS
```

### Setup-Schritte

```bash
# 1. Repository klonen
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
nano .env  # Passwörter und Secrets ändern!

# 3. System initialisieren
make init

# 4. Services starten
make up

# 5. Modelle herunterladen (dauert!)
make pull-models

# 6. Status prüfen
make status

# 7. Logs ansehen
make logs
```

### .env Konfiguration

**Wichtige Variablen:**

```bash
# PostgreSQL
POSTGRES_USER=kirobi
POSTGRES_PASSWORD=ÄNDERN_SIE_DIES
POSTGRES_DB=kirobi
POSTGRES_PORT=5432

# Ollama
OLLAMA_PORT=11434
OLLAMA_NUM_PARALLEL=2
OLLAMA_GPU_MEMORY_FRACTION=0.9

# Open WebUI
OPENWEBUI_PORT=3000
OPENWEBUI_SECRET_KEY=ÄNDERN_SIE_DIES_WIRKLICH

# Flowise
FLOWISE_PORT=3001
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=ÄNDERN_SIE_DIES

# Qdrant
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334

# Auth
JWT_SECRET_KEY=GENERIEREN_SIE_EINEN_SICHEREN_KEY
AUTH_PORT=8002

# API
API_PORT=8003

# Voice
VOICE_PORT=8001
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda
VOICE_LANGUAGE=de
```

---

## Entwicklungsworkflows

### Neues Feature entwickeln

```bash
# 1. Branch erstellen
git checkout -b feature/mein-feature

# 2. CLAUDE.md lesen (PFLICHT!)
cat CLAUDE.md

# 3. Relevante Docs lesen
cat metadata/ZONE-POLICY-MATRIX.md
cat ARCHITECTURE.md

# 4. Code schreiben
nano services/api/main.py

# 5. Testen (lokal)
make restart-service SERVICE=api
make logs-service SERVICE=api

# 6. Commit (conventional commits)
git add services/api/main.py
git commit -m "feat(api): add new endpoint for XYZ"

# 7. Push
git push origin feature/mein-feature

# 8. Pull Request erstellen
gh pr create --title "Add XYZ feature" --body "Description..."
```

### Neuen Agenten hinzufügen

```bash
# 1. Agent-Definition in Registry
nano metadata/AGENTREGISTRY.md

# 2. System-Prompt erstellen
nano kirobi-core/core-prompts/neuer-agent-prompt.md

# 3. Berechtigungen definieren
nano metadata/ZONE-POLICY-MATRIX.md

# 4. Flowise-Workflow erstellen
# → http://localhost:3001

# 5. Testing
# → Open WebUI verwenden, Agent testen

# 6. Dokumentieren
nano experiences/learnings/neuer-agent-notes.md
```

### Service lokal entwickeln (außerhalb Docker)

```bash
# Python-Service (z.B. API)
cd services/api

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=kirobi
export POSTGRES_PASSWORD=changeme
export POSTGRES_DB=kirobi
export OLLAMA_HOST=http://localhost:11434

# Service starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In anderem Terminal: Testen
curl http://localhost:8000/health
```

---

## API-Dokumentation

### REST API Endpoints

**Base URL:** `http://localhost:8003`

#### Authentication

Alle geschützten Endpoints benötigen einen JWT-Token im Header:

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Error Responses

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `200` - Erfolg
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

#### POST /conversations

**Request:**

```json
{
  "title": "Familie Check-in",
  "zone": "FAMILY_PRIVATE"
}
```

**Response:**

```json
{
  "id": "conv-uuid",
  "user_id": "user-uuid",
  "title": "Familie Check-in",
  "zone": "FAMILY_PRIVATE",
  "created_at": "2026-05-05T10:00:00Z",
  "updated_at": "2026-05-05T10:00:00Z",
  "archived": false
}
```

#### POST /conversations/{id}/messages

**Request:**

```json
{
  "content": "Wie war dein Tag?",
  "attachments": []
}
```

**Response:**

```json
{
  "id": "msg-uuid",
  "conversation_id": "conv-uuid",
  "user_id": "user-uuid",
  "role": "assistant",
  "content": "Mein Tag war sehr produktiv! Ich habe...",
  "model_used": "llama3.1:8b",
  "tokens_used": 245,
  "attachments": [],
  "metadata": {},
  "created_at": "2026-05-05T10:05:00Z"
}
```

#### POST /upload

**Request (multipart/form-data):**

```bash
curl -X POST http://localhost:8003/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "zone=WORKSPACE"
```

**Response:**

```json
{
  "id": "file-uuid",
  "filename": "unique-filename.pdf",
  "file_path": "/data/uploads/sven/workspace/unique-filename.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "zone": "WORKSPACE",
  "created_at": "2026-05-05T10:10:00Z"
}
```

---

## Datenbank-Schema

### PostgreSQL Tabellen

#### conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT,
    zone TEXT NOT NULL CHECK (zone IN ('PUBLIC', 'WORKSPACE', 'FAMILY_PRIVATE', 'SACRED')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_zone ON conversations(zone);
```

#### messages

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_used TEXT,
    tokens_used INTEGER,
    attachments JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

#### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'member', 'child')),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

#### file_uploads

```sql
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT,
    zone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_file_uploads_user_id ON file_uploads(user_id);
CREATE INDEX idx_file_uploads_zone ON file_uploads(zone);
```

#### supervisor_tasks

```sql
CREATE TABLE supervisor_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_agent TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    metadata JSONB,
    dependencies TEXT[]
);

CREATE INDEX idx_supervisor_tasks_status ON supervisor_tasks(status);
CREATE INDEX idx_supervisor_tasks_priority ON supervisor_tasks(priority);
```

#### supervisor_events

```sql
CREATE TABLE supervisor_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_supervisor_events_timestamp ON supervisor_events(timestamp DESC);
CREATE INDEX idx_supervisor_events_type ON supervisor_events(event_type);
```

### Qdrant Collections

| Collection | Embedding-Modell | Dimensionen | Zweck |
|-----------|-----------------|------------|-------|
| `kirobi_public` | nomic-embed-text | 768 | PUBLIC-Dokumente |
| `kirobi_workspace` | bge-m3 | 1024 | WORKSPACE-Dokumente |
| `kirobi_family` | bge-m3 | 1024 | FAMILY_PRIVATE-Dokumente |
| `kirobi_canon` | bge-m3 | 1024 | Canon-Dokumente |
| `kirobi_experiences` | bge-m3 | 1024 | Experiences |
| `kirobi_code` | nomic-embed-text | 768 | Code-Snippets |
| `kirobi_sacred` | bge-m3 (encrypted) | 1024 | SACRED-Dokumente |

**Collection erstellen:**

```bash
curl -X PUT http://localhost:6333/collections/kirobi_test \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'
```

---

## Testing

### Unit Tests

```bash
# Alle Unit Tests
cd tests/unit
pytest -v

# Spezifischer Test
pytest test_supervisor.py::test_task_creation -v

# Mit Coverage
pytest --cov=services --cov-report=html
```

### Integration Tests

```bash
# Services müssen laufen
make up

# Integration Tests
cd tests/integration
pytest -v

# API-Tests
pytest test_api_integration.py -v
```

### Security Tests

```bash
cd tests/security

# Zone-Zugriffstests
pytest test_zone_enforcement.py -v

# Prompt Injection Tests
pytest test_prompt_injection.py -v

# Auth Tests
pytest test_authentication.py -v
```

### Manuelle Tests

```bash
# Health Checks
curl http://localhost:8003/health
curl http://localhost:8002/health
curl http://localhost:8001/health

# Ollama Test
curl http://localhost:11434/api/tags

# Qdrant Test
curl http://localhost:6333/collections
```

---

## Debugging

### Logs ansehen

```bash
# Alle Services
make logs

# Spezifischer Service
docker compose logs -f api
docker compose logs -f supervisor

# Letzte 100 Zeilen
docker compose logs --tail=100 ollama

# Supervisor Event Log
tail -f kirobi-core/core-events.log

# PostgreSQL Logs
docker compose logs postgres | grep ERROR
```

### Container betreten

```bash
# API Service
docker compose exec api bash

# PostgreSQL
docker compose exec postgres psql -U kirobi -d kirobi

# Ollama
docker compose exec ollama bash
```

### Python Debugger (pdb)

In Code einfügen:

```python
import pdb; pdb.set_trace()
```

Dann Container mit angehängtem Terminal starten:

```bash
docker compose up api
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Deployment

### Production Checklist

- [ ] **.env anpassen:** Alle Secrets ändern
- [ ] **GPU-Treiber:** NVIDIA-Treiber und CUDA installiert
- [ ] **Docker:** Docker & Docker Compose v2+ installiert
- [ ] **Backups:** Backup-Verzeichnis konfiguriert
- [ ] **Firewall:** Nur notwendige Ports öffnen
- [ ] **SSL/TLS:** Reverse Proxy mit Let's Encrypt
- [ ] **Monitoring:** Logs und Metriken sammeln
- [ ] **Ressourcen:** Genügend RAM/Disk für Modelle

### Production .env

```bash
# ÄNDERE ALLE SECRETS!
POSTGRES_PASSWORD=$(openssl rand -base64 32)
OPENWEBUI_SECRET_KEY=$(openssl rand -base64 32)
FLOWISE_SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Backup
BACKUP_ENABLED=true
BACKUP_TARGET_DIR=/mnt/backup/kirobi
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30

# Sicherheit
CORS_ORIGINS=https://kirobi.example.com
ALLOWED_HOSTS=kirobi.example.com
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name kirobi.example.com;

    ssl_certificate /etc/letsencrypt/live/kirobi.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kirobi.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8003/;
        proxy_set_header Host $host;
    }
}
```

### Systemd Service

`/etc/systemd/system/kirobi.service`:

```ini
[Unit]
Description=Kirobi Disruptive OS
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/sven/kirobi
ExecStart=/usr/bin/make up
ExecStop=/usr/bin/make down
User=sven
Group=sven

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable kirobi
sudo systemctl start kirobi
```

---

## Best Practices

### Sicherheit

1. **Secrets niemals committen**
   - `.env` ist in `.gitignore`
   - Verwende `.env.example` als Template

2. **Zone-Klassifizierung beachten**
   - Immer frontmatter mit `zone:` Tag
   - FAMILY_PRIVATE niemals an Cloud-APIs

3. **Input-Validierung**
   - Alle User-Inputs validieren
   - Pydantic-Modelle verwenden
   - SQL-Injection vermeiden (parametrisierte Queries)

4. **Prompt Injection verhindern**
   - User-Input niemals direkt in Prompts
   - System-Prompts von User-Input trennen
   - Output-Filtering

### Code-Qualität

1. **Type Hints verwenden**
   ```python
   def get_user(user_id: str) -> Optional[User]:
       ...
   ```

2. **Docstrings schreiben**
   ```python
   def create_task(name: str, priority: TaskPriority) -> Task:
       """
       Create a new task in the supervisor queue.

       Args:
           name: Human-readable task name
           priority: Task priority level

       Returns:
           Created Task object
       """
   ```

3. **Error Handling**
   ```python
   try:
       result = await call_ollama(prompt)
   except httpx.TimeoutException:
       logger.error("Ollama timeout")
       return "Service temporarily unavailable"
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       raise
   ```

4. **Logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.debug("Detailed debug info")
   logger.info("Informational message")
   logger.warning("Warning message")
   logger.error("Error occurred")
   ```

### Git Workflow

1. **Conventional Commits**
   ```bash
   feat(api): add user profile endpoint
   fix(supervisor): resolve task queue deadlock
   docs(readme): update installation instructions
   refactor(auth): simplify token validation
   test(api): add conversation tests
   chore(deps): update FastAPI to 0.110.0
   ```

2. **Branch-Naming**
   ```
   feature/user-profile
   bugfix/task-queue-deadlock
   hotfix/security-vulnerability
   refactor/simplify-auth
   docs/api-documentation
   ```

3. **Pull Request Template**
   ```markdown
   ## Beschreibung
   Was wurde geändert und warum?

   ## Testing
   - [ ] Unit Tests laufen
   - [ ] Integration Tests laufen
   - [ ] Manuell getestet

   ## Checklist
   - [ ] Code folgt Coding-Standards
   - [ ] Keine Secrets committed
   - [ ] Dokumentation aktualisiert
   - [ ] Zone-Compliance geprüft
   ```

---

## Häufige Probleme

### Problem: Ollama-Modell lädt nicht

**Symptome:** Modell-Antworten extrem langsam oder Fehler

**Lösung:**

```bash
# GPU-Verfügbarkeit prüfen
nvidia-smi

# Ollama-Container GPU-Zugriff prüfen
docker compose exec ollama nvidia-smi

# Modell neu herunterladen
docker exec -it kirobi-ollama ollama pull llama3.1:8b

# Ollama-Logs prüfen
docker compose logs ollama
```

---

### Problem: PostgreSQL Connection Failed

**Symptome:** Services können nicht zur DB verbinden

**Lösung:**

```bash
# PostgreSQL-Status prüfen
docker compose ps postgres

# PostgreSQL-Logs
docker compose logs postgres

# Manuell verbinden
docker compose exec postgres psql -U kirobi -d kirobi

# Credentials in .env prüfen
cat .env | grep POSTGRES
```

---

### Problem: Disk Space voll

**Symptome:** Services crashen, writes fehlschlagen

**Lösung:**

```bash
# Disk-Usage prüfen
df -h
docker system df

# Docker aufräumen
docker system prune -a -f

# Alte Ollama-Modelle entfernen
docker exec kirobi-ollama ollama list
docker exec kirobi-ollama ollama rm old-model

# Archive/Quarantine aufräumen
rm -rf archive/old-snapshots/*
```

---

### Problem: Agent verletzt Zone-Policy

**Symptome:** Agent sendet FAMILY_PRIVATE an Cloud-API

**Lösung:**

```bash
# Event-Log prüfen
grep "ZONE_VIOLATION" kirobi-core/core-events.log

# Agent-Prompt überprüfen
cat kirobi-core/core-prompts/agent-name-prompt.md

# Zone-Policy-Matrix prüfen
cat metadata/ZONE-POLICY-MATRIX.md

# Agent deaktivieren (temporär)
# In Flowise: Flow deaktivieren
```

---

## Contribution Guidelines

### Bevor du beiträgst

1. **CLAUDE.md lesen** (PFLICHT!)
2. **PROJECT-CHARTER.md verstehen** (Vision & Prinzipien)
3. **CONTRIBUTING.md lesen** (Prozess-Details)

### Was kann beigetragen werden?

✅ **Erlaubt:**
- Bug-Fixes
- Feature-Implementierungen (nach Diskussion)
- Dokumentations-Verbesserungen
- Tests hinzufügen
- Performance-Optimierungen
- Neue Agenten (PUBLIC/WORKSPACE only)

❌ **Nicht erlaubt:**
- Änderungen an SACRED-Zone
- Änderungen an Security-Policies ohne Review
- Breaking Changes ohne Major Version Bump
- Code, der proprietäre APIs ohne Opt-in nutzt

### Code Review Prozess

1. **Pull Request erstellen**
2. **CI/CD prüft automatisch:**
   - Linting
   - Tests
   - Security Scan
3. **Maintainer Review**
4. **Änderungen einarbeiten**
5. **Merge**

---

## Weiterführende Ressourcen

### Interne Dokumentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detaillierte Architektur
- [DEVELOPER-RUNBOOK.md](./DEVELOPER-RUNBOOK.md) - Ops-Handbuch
- [SECURITY.md](./SECURITY.md) - Sicherheitsrichtlinien
- [THREAT-MODEL.md](./THREAT-MODEL.md) - Bedrohungsanalyse
- [ROADMAP.md](./ROADMAP.md) - Entwicklungs-Roadmap

### Externe Dokumentation

- **Docker:** https://docs.docker.com/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Ollama:** https://github.com/ollama/ollama
- **Qdrant:** https://qdrant.tech/documentation/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Flowise:** https://docs.flowiseai.com/

---

**Dokument-Version:** 1.0
**Letzte Aktualisierung:** 2026-05-05
**Nächste Review:** 2026-08-05
**Betreut von:** kirobi-architect, kirobi-coder

**Bei Fragen:** Erstelle ein Issue auf GitHub oder kontaktiere das Core-Team.
