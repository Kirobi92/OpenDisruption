---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: ACTIVE
---

# ARCHITECTURE_REVIEW.md

## 1. Ist-Architektur (verdichtet)

```
                      ┌────────────────┐
                      │  Caddy :80/443 │  ◄─── Tailscale / LAN
                      └────────┬───────┘
                               │
       ┌────────┬──────────────┼──────────────┬─────────┐
       ▼        ▼              ▼              ▼         ▼
   web:3002  portal:?      dashboard:3003  voice:3004  admin:?
       │        │              │              │         │
       └────────┴──────┬───────┴──────────────┴─────────┘
                       ▼
                  api:8003 ◄──── auth:8002 (JWT)
                       │
        ┌──────────────┼──────────────┬─────────────────┐
        ▼              ▼              ▼                 ▼
   retrieval:8006  embeddings:8004  ingest:8007  model-routing:8009
        │              │              │                 │
        ▼              ▼              ▼                 ▼
       Qdrant ◄────  embeddings  ─► Postgres        Ollama:11434
                                                   (+ GitHub Models)
        ┌────────────────────────┐
        │   personal-agents:8017  │  ◄── Sven/Samira/Sineo (Hermes-Stil)
        └────────────────────────┘

        ┌────────────────────────┐
        │   hermes-runtime        │  (CLI-Container, MCPs: memory, postgres, fs, sequential-thinking)
        └────────────────────────┘

        ┌──────────────┬──────────────┬──────────────┐
        │  image:8011  │  music:8013  │  video:8014  │
        └──────────────┴──────────────┴──────────────┘
              │                │                │
              └─────────► media-processing:8012 ◄┘

        ┌────────────────┐
        │ analytics:8010 │ ── Postgres
        └────────────────┘

        ┌──────────────────┐
        │ supervisor       │ ── kirobi_core (Backlog-Runner)
        └──────────────────┘

        ┌──────────────────┐
        │ telegram :8005   │ ◄── @Disruptivbot ── Sven (Telegram)
        └──────────────────┘ (aktuell DOWN)

        ┌──────────────────┐
        │ nutzi            │ ── eNVenta-ERP-Companion (Spezialfall)
        └──────────────────┘

        ┌──────────────────┐
        │ openclaw-gateway │ ── LEER (entfernen)
        └──────────────────┘
```

## 2. Bewertung pro Dimension

### 2.1 Modularität (6 / 10)
- ✅ Service-Schnitt nach Domäne (auth, retrieval, ingest …)
- ❌ `api` ist ein Monolith (2 262 LOC), bündelt Conversations, Operator-Status, Agent-Routing
- ❌ `telegram/main.py` enthält Auth, Bot-Logik, DB-Bootstrap

### 2.2 Separation of Concerns (5 / 10)
- ❌ Orchestrierungs-Logik verteilt auf: `orchestrator/`, `supervisor`-Mode (kirobi_core), `keycodi/`, `agents/hermes`, `services/hermes-runtime/`
- ✅ Auth ist klar getrennt
- ✅ Retrieval enforcet Zone-Policy single-source

### 2.3 Kopplung & Kohäsion (6 / 10)
- ✅ Nachrichtenformat zwischen Services konsistent (JSON, FastAPI/Pydantic)
- ❌ Service-URLs hardcoded in mehreren Diensten (`http://api:8000`, `http://auth:8000` etc.)
- ❌ Postgres-Schema-Bootstrap geschieht in 4 verschiedenen Services (api, auth, ingest, telegram)

### 2.4 Skalierbarkeit (6 / 10)
- ✅ Container-basiert, horizontal grundsätzlich machbar
- ❌ Keine Resource-Limits (außer GPU)
- ❌ Keine Worker-Queues (alles HTTP-direkt)
- ❌ Postgres ohne Read-Replica-Vorbereitung

### 2.5 Erweiterbarkeit (7 / 10)
- ✅ Compose-Profile (`profile-cpu.yml`, `profile-voice-full.yml`)
- ✅ MCP-Server-Pattern in Hermes
- ❌ Neue Agenten erfordern Edits in `services/api/_agent_prompt()` UND `agent_options` UND ggf. service

### 2.6 Lesbarkeit (5 / 10)
- ✅ Deutsch in Doku, Englisch im Code (konsistent)
- ❌ 25 MDs im Root erschweren Einstieg
- ❌ Kein API-Reference-Dokument

### 2.7 Testbarkeit (3 / 10)
- ❌ 14/16 Backends ohne Tests
- ✅ `kirobi_core` selbst hat 574 Unit-Tests
- ❌ Keine HTTP-Contract-Tests zwischen Services
- ❌ Keine E2E-Smoke-Tests gegen laufende Compose

### 2.8 Fehlerbehandlung (4 / 10)
- ❌ Bare `except Exception` in mehreren Services (`services/ingest/main.py:465,522,599,601,621`)
- ❌ Kein Standard-Error-Schema (RFC 7807 / Problem Details)
- ❌ Kein zentrales Error-Logging-Sink
- ✅ Healthchecks fangen Restart automatisch (wo vorhanden)

### 2.9 Security-Basics (4 / 10)
- ❌ 5 Services auf `0.0.0.0`
- ❌ 3 Services CORS `*` + keine Auth
- ❌ JWT-Fallback-Secret
- ✅ SACRED-Enforcement
- ✅ `.env` im `.gitignore` (verifiziert)
- ✅ Caddy als alleiniger Edge

### 2.10 Performance-Fallen
- ⚠️ Synchrone HTTP-Calls in async-Routen (verstreut)
- ⚠️ Keine Connection-Pool-Limits an Postgres
- ⚠️ Embeddings ohne Batch-Cache

### 2.11 Konfigurationsmanagement (5 / 10)
- ❌ 183 Env-Vars, kein zentrales Schema
- ❌ Hardcoded Defaults (`changeme`)
- ✅ `bash infra/scripts/validate-env.sh` existiert (warning-level)

### 2.12 Developer Experience (6 / 10)
- ✅ `Makefile` mit klaren Targets
- ✅ Docker-Compose-Profile
- ❌ Kein einheitliches `make dev` für lokales Hot-Reload
- ❌ Pro-Service-`README.md` teils leer

### 2.13 Automatisierbarkeit (6 / 10)
- ✅ CI-Workflow vorhanden (`.github/workflows/`)
- ❌ Kein Coverage-Report
- ❌ Kein Container-Image-Build in CI
- ❌ Kein automatisiertes Backup-Verify

### 2.14 Dokumentationsqualität (5 / 10)
- ✅ CLAUDE.md / AGENTS.md exzellent
- ❌ 25 Root-MDs mit Doppelungen
- ❌ Kein API-Doc-Bundle (OpenAPI ja, aber nicht aggregiert)

## 3. Konkrete Architektur-Empfehlungen

### 3.1 Orchestrator-Klarheit
**Problem:** „Wer orchestriert was?" wird nicht klar.

**Vorschlag (Single Source of Truth):**
| Schicht | Tool | Aufgabe | Trigger |
|---|---|---|---|
| **Coding** | `keycodi/` (KeyCodi Master-Code-Orchestrator) | Phasen-Sequenzierung von Code-Missionen | Mensch (`make keycodi MISSION=…`) |
| **Familie / Wissen** | `hermes-runtime` (Hermes-Hauptagent) | Tagesablauf, Dokumenten-Triage, Telegram | Telegram, Cron, MCP |
| **Backlog** | `services/orchestrator` (supervisor-mode) | Geplante Tasks aus `.kirobi/backlog/` | Cron innerhalb Container |
| **Personal** | `services/personal-agents:8017` | Familien-Profile (Sven/Samira/Sineo) | Web-Portal-Chat |

→ Doku in **`docs/ORCHESTRATION-MAP.md`** einmalig festschreiben.

### 3.2 API-Service-Split
`services/api/main.py` aufteilen in:
```
services/api/
  app/
    __init__.py
    main.py                # nur FastAPI() + Router-Registrierung
    deps.py                # gemeinsame Depends (auth, db)
    routers/
      conversations.py
      messages.py
      agents.py
      operator.py
      health.py
    services/              # Service-Klassen (Ollama-Bridge, etc.)
    schemas.py             # Pydantic-Modelle
```

### 3.3 Frontend-Konsolidierung
- **`apps/web`** = PWA + Familien-Portal (Chat, Voice, Brain, Goals, Profile)
- **`apps/admin-dashboard`** = Admin + Operator-Dashboard
- **`apps/voice`** = Optional ersetzen durch Voice-Tab in `apps/web`
- **Archivieren:** `apps/web-svelte`, `apps/desktop`, `apps/mobile`, `apps/admin`, `apps/portal` (nach Merge)

### 3.4 Hermes als zentraler Familien-Agent
- Memory-Path **per User**: Hermes erkennt Telegram-User-ID → wählt korrekten Knowledge-Graph
- Skill-Pack `opendisruption-orchestrator` = neuer kanonischer Skill
- Alle Sven-Eingaben (Telegram, Portal, Voice) durchlaufen Hermes als „Front Door"

## 4. Reifegrad-Matrix

| Bereich | Heute | 6 Wochen Ziel | 6 Monate Ziel |
|---|---|---|---|
| Tests | 12 % | 60 % | 80 % |
| Healthchecks | 23/35 (66 %) | 35/35 | + Liveness/Readiness-Split |
| Security | 35/100 | 75/100 | 90/100 |
| Doku-Klarheit | 25 MDs unsortiert | 10 + `/docs/` | + Auto-API-Reference |
| Frontends | 6 aktiv | 2–3 | 2 + Mobile |
| Dependencies | unpinnt | pip-compile + lockfile | renovate-bot |

## 5. Trade-offs / Anti-Patterns die NICHT eingebaut werden sollen

❌ **Kein Kubernetes** — Compose reicht für Familienbetrieb.
❌ **Kein Microservice-Mesh** (Istio/Linkerd) — Overhead > Nutzen.
❌ **Kein GraphQL** — REST ist für interne Kommunikation klarer.
❌ **Kein eigenes Auth-Framework** — `auth` Service + JWT ist solide.
❌ **Kein Event-Bus** als Zwang — nur einführen wenn Worker-Pattern nötig.

## 6. Architektur-Risiko-Heatmap

| Risiko | Eintritt | Impact | Bewertung |
|---|---|---|---|
| Telegram-Bot offline (Service down) | hoch (jetzt!) | mittel | 🔴 |
| LAN-Exposure 0.0.0.0 wird ausgenutzt | mittel | hoch | 🔴 |
| Postgres-Schema-Drift (4 Schreiber) | mittel | mittel | 🟠 |
| Memory-Leak in voice-processing (1 880 LOC, kein Test) | mittel | hoch | 🟠 |
| Hermes-Memory shared statt per-User | hoch | mittel | 🟠 |
| Doku-Veraltung führt zu falschem Onboarding | hoch | mittel | 🟡 |
