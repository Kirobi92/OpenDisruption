---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: PROPOSAL
---

# TARGET_STRUCTURE.md — Empfohlene Zielarchitektur

## 1. Repo-Topologie (Ziel)

```
OpenDisruption/
├── README.md                        ← Entry Point (Quick Start, Status)
├── CLAUDE.md                        ← Agent-Sicherheits-Pflicht
├── AGENTS.md                        ← Repo-Konventionen + Service-Map
├── PROJECT-CHARTER.md               ← Vision & Mission
├── PROJECT-ARCHITECTURE.md          ← System-Design (single source of truth)
├── ROADMAP.md                       ← Phasen-Plan
├── SECURITY.md                      ← Threat-Modell-Übersicht
├── CONTRIBUTING.md                  ← Beitragsrichtlinien
├── DEVELOPER-RUNBOOK.md             ← Tagesbetrieb
├── LICENSE.md
│
├── docs/
│   ├── README.md                    ← Doku-Index
│   ├── SERVICE-REGISTRY.md          ← NEU: Alle Services + Ports + Owner
│   ├── DATA-PIPELINE.md             ← NEU: sources → extracts → canon → experiences
│   ├── ORCHESTRATION-MAP.md         ← NEU: Wer orchestriert was (KeyCodi/Hermes/Supervisor)
│   ├── API-REFERENCE.md             ← NEU: Aggregierte OpenAPI-Übersicht
│   ├── DEPLOYMENT.md                ← NEU: Production-Guide
│   ├── TROUBLESHOOTING.md           ← NEU: Häufige Probleme
│   ├── SECURITY-THREAT-MODEL.md     ← (von Root verschoben)
│   ├── BENUTZERHANDBUCH.md          ← (von Root verschoben, aktualisiert)
│   └── agents/
│       ├── HERMES.md
│       ├── KEYCODI.md
│       ├── PERSONAL-AGENTS.md
│       └── ORCHESTRATOR.md
│
├── archive/
│   └── docs-old/
│       ├── README.md                ← Was archiviert wurde + warum
│       ├── ARCHITECTURE.md
│       ├── COMPLETION-REPORT.md
│       ├── ULTIMATE-IMPLEMENTATION-ROADMAP.md
│       ├── IMPLEMENTATION-SUMMARY.md
│       ├── POST-CLONE-SETUP.md      (in README mergen)
│       ├── AGENT-SYSTEM-PROMPT.md   (in AGENTS.md mergen)
│       ├── AGENT-INSTALLATION.md
│       ├── AGENT-RECOVERY.md        (→ docs/TROUBLESHOOTING.md)
│       ├── AUDIT-REPORT.md          (durch CODEBASE_AUDIT.md ersetzt)
│       ├── ENTWICKLERDOKUMENTATION.md
│       ├── CHANGELOG.md             (durch git log ersetzt)
│       ├── QUICK-REFERENCE.md       (in README mergen)
│       └── AGENT-DECISION-MATRIX.md
│
├── apps/
│   ├── web/                         ← PWA + Familien-Portal (PRIMARY)
│   │   └── src/...                  (Chat, Voice, Brain, Goals, Profile)
│   ├── admin-dashboard/             ← Admin + Operator (merge admin+dashboard)
│   ├── installer/                   ← Doc-Only
│   └── archive/                     ← desktop, mobile, web-svelte (Frozen/POC)
│
├── services/
│   ├── README.md                    ← Service-Index mit Owner
│   ├── _shared/                     ← NEU: gemeinsame Helpers (auth_deps, db, logging, cors)
│   ├── api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py              ← nur FastAPI() + Router-Registrierung
│   │       ├── deps.py
│   │       ├── routers/
│   │       │   ├── conversations.py
│   │       │   ├── messages.py
│   │       │   ├── agents.py
│   │       │   ├── operator.py
│   │       │   └── health.py
│   │       ├── schemas.py
│   │       └── services/
│   ├── auth/
│   ├── retrieval/
│   ├── embeddings/
│   ├── ingest/
│   ├── model-routing/               (mit Auth + CORS-Fix)
│   ├── personal-agents/             (v2 ✅)
│   ├── analytics-service/
│   ├── image-generation/
│   ├── music-generation/
│   ├── video-generation/
│   ├── media-processing/
│   ├── voice-processing/            (in Module aufgeteilt)
│   ├── telegram/                    (Container starten + Healthcheck)
│   ├── orchestrator/
│   ├── hermes-runtime/              (per-User Memory + opendisruption-orchestrator Skill)
│   └── nutzi/                       (eNVenta-ERP-Spezialfall)
│   # ENTFERNT: openclaw-gateway (war leer)
│
├── agents/                          ← Agent-Profile (Markdown + YAML)
│   ├── hermes/
│   │   ├── orchestrator.yaml        ← NEU: Hauptagent-Profil
│   │   └── prompts/
│   ├── keycodi/
│   ├── opencode/
│   ├── obsidian/
│   └── openclaw/
│
├── kirobi-core/                     ← Markdown-Identität, Prompts (zone: WORKSPACE)
├── kirobi_core/                     ← Python-CLI/Lib (importable)
│   # NICHT umbenennen — Migration zu teuer (TD-022 = P3)
│
├── keycodi/                         ← Master-Code-Orchestrator (Phasen)
│
├── infra/
│   ├── caddy/
│   ├── scripts/
│   │   ├── healthcheck.sh
│   │   ├── backup.sh
│   │   ├── restore.sh               ← NEU: Restore-Test
│   │   ├── validate-env.sh
│   │   └── init-qdrant.py
│   └── compose-profiles/
│
├── tests/
│   ├── unit/                        ← bestehend, kirobi_core
│   ├── services/                    ← NEU: pro Service Unit-Tests
│   ├── integration/                 ← NEU: HTTP-Smoke gegen Compose
│   └── fixtures/                    ← Beispiel-Daten
│
├── config/
├── data/                            ← Volumes (gitignored)
├── archive/
├── canon/                           ← versionierte Wissens-Wahrheit
├── experiences/                     ← Lernen, Reflexion
├── extracts/                        ← extrahierte/klassifizierte Daten
├── clusters/                        ← semantische Gruppen
├── sources/                         ← Roh-Inputs
├── quarantine/                      ← Untrusted (kein Promote ohne Review)
├── sacred/                          ← Sven-only (NIE auto-touch)
└── metadata/                        ← Governance
```

## 2. Service-Aufgaben (klare Grenzen)

| Service | Verantwortung | NICHT verantwortlich für |
|---|---|---|
| `auth` | Login, JWT, User/Zone-Permissions | Inhalte |
| `api` | HTTP-Frontdoor, Conversations/Messages, Agent-Routing | LLM-Calls direkt (über model-routing) |
| `retrieval` | RAG-Suche, Zone-Enforcement | Embeddings erzeugen |
| `embeddings` | Text → Vektor → Qdrant | Suche |
| `ingest` | File-Upload, Job-Tracking | Embedding-Erzeugung (delegiert) |
| `model-routing` | LLM-Auswahl (lokal vs. cloud), Fallback-Strategie | Auth (delegiert), aber prüft Token |
| `personal-agents` | Familien-Profile, Anti-Halluzination, Datenspeicher-Sync | Allgemeine Chats (api übernimmt) |
| `voice-processing` | Whisper STT + Piper TTS | UI |
| `telegram` | Bot-Interface, Sven↔System | Logik (delegiert an api/hermes) |
| `orchestrator` | Backlog-Runner, geplante Tasks | Live-Coding (KeyCodi) |
| `hermes-runtime` | Familien-/Wissens-Hauptagent (CLI + MCP) | Backlog (Supervisor) |
| `analytics-service` | Event-Tracking, Stats | Inhalte |
| `image/music/video-generation` | Lokale Mediengenerierung | Speicherung (media-processing) |
| `media-processing` | Pillow/mutagen/ffmpeg-Wrapper | Generierung |
| `nutzi` | eNVenta-ERP-Companion | Allgemein |

## 3. Schnittstellen-Verträge

Alle Services exposen mind.:
- `GET /health` → `{status, version, timestamp, db_latency_ms?}`
- OpenAPI unter `/docs` (FastAPI default)
- Auth via Bearer-JWT (außer `/health` und `/login`)

Shared schemas in `services/_shared/schemas/`:
- `Health`
- `ErrorEnvelope` (RFC 7807-ähnlich)
- `User` / `JwtClaims`

## 4. Naming-Konventionen

- Service-Pfade: `services/<kebab-case>/`
- Container-Namen: `kirobi-<service>`
- Env-Vars: `<SERVICE>_<KEY>` (z.B. `AUTH_JWT_SECRET`)
- Ports: dokumentiert in `docs/SERVICE-REGISTRY.md`, primary owner `AGENTS.md`
- Branches: `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `infra/`, `agent/`

## 5. Frontend-Konsolidierungspfad

| Heute | Schritt 1 (Sprint 2) | Schritt 2 (Sprint 3) |
|---|---|---|
| `web` (PWA) | bleibt | + Voice-Tab integriert |
| `portal` | Routes nach `web/src/app/portal/` mergen | entfernt |
| `dashboard` | bleibt | merged mit `admin` |
| `admin` | merge mit `dashboard` | entfernt |
| `voice` | bleibt einzeln (oder Tab in web) | optional entfernt |
| `web-svelte` | sofort archivieren | entfernt |
| `desktop`, `mobile` | Frozen, aus compose | Re-Open in Phase 6 |

Effekt: Von **6 Apps + 3 GB node_modules** → **2–3 Apps + 1 pnpm-Workspace + ~1 GB**.

## 6. Konfigurations-Strategie

### `.env` → schema-validiert
```python
# kirobi_core/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class CoreSettings(BaseSettings):
    POSTGRES_USER: str = "kirobi"
    POSTGRES_PASSWORD: str  # required, no default
    POSTGRES_DB: str = "kirobi"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    JWT_SECRET_KEY: str  # required
    KIROBI_BIND_HOST: str = "127.0.0.1"
    OLLAMA_HOST: str = "http://ollama:11434"

    @validator("JWT_SECRET_KEY")
    def secret_strong(cls, v):
        if not v or "CHANGEME" in v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY too weak")
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"
```

Alle Services importieren aus `kirobi_core.settings`.

## 7. Logging-Strategie

- **stdlib `logging`** mit JSON-Formatter
- Struktur: `{ts, level, service, msg, request_id?, user_id?, ...}`
- Kein `print()` mehr
- Keine Secrets/PII in Logs (Redaction-Helper in `kirobi_core/logging_config.py`)

## 8. Fehler-Strategie

Single Error-Format (`services/_shared/errors.py`):
```python
class ApiError(Exception):
    type: str       # "auth.invalid_token", "zone.forbidden", ...
    title: str
    status: int
    detail: str
    instance: str | None
```

Globaler FastAPI-Exception-Handler → JSON nach RFC 7807-Stil.

## 9. CI/CD-Ziel-Matrix

| Stage | Heute | Ziel |
|---|---|---|
| Lint | ShellCheck | + ruff (Python), eslint (TS) |
| Test | unit | + integration + coverage 60 %+ |
| Security | – | pip-audit, npm audit, trivy on images |
| Build | – | docker build pro Service |
| Deploy | manuell | Compose-Profile via Tag |

## 10. Roadmap-Anker

→ Konkrete Schritte in `IMPLEMENTATION_ROADMAP.md` (Phase 0–7).
