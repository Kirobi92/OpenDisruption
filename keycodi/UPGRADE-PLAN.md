---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# KeyCodi Upgrade Plan — OpenDisruption Ökosystem

**Erstellt:** 2026-05-07  
**Status:** In Ausführung  
**Ziel:** Alle im Repo definierten Funktionen vollständig implementieren

---

## Analyse-Ergebnis: Was existiert vs. was fehlt

### ✅ Vollständig implementiert

| Bereich | Status | Details |
|---------|--------|---------|
| `kirobi_core/` | ✅ Vollständig | zones, audit, backlog, orchestrator, autonomous, scanner, registry, keycodi, bridge, interview, doctor, cli |
| `services/auth/` | ✅ Vollständig | FastAPI JWT-Auth, Zone-Permissions, User-Management |
| `services/api/` | ✅ Vollständig | Konversationen, Messages, File-Uploads, Ollama-Bridge |
| `services/telegram/` | ✅ Vollständig | Webhook + Long-Polling, JWT-Auth, DB-Integration |
| `services/voice-processing/` | ✅ Vollständig | Whisper STT + Piper TTS |
| `apps/web/` | ✅ Vollständig | Next.js 15 PWA, Chat, Health, Status |
| `kidi/context_db/` | ✅ Vollständig | Redis-basierter Kontext-Store, Zone-Enforcement |
| `agents/_base/` | ✅ Vollständig | BaseAgent, AgentResult, Task |
| `agents/hermes/` | ✅ Skelett | Reasoning-Agent (Echo-Stub, Phase 4) |
| `agents/obsidian/` | ✅ Vollständig | Vault-CRUD, Knowledge-Graph, Daily-Notes |
| `tests/unit/` | ✅ 219 Tests | Alle kirobi_core Module abgedeckt |
| `.opencode/agents/` | ✅ 7 Agenten | Alle mit GPT-5.5 + Highx Mode |
| `.opencode/skills/` | ✅ 7 Skills | keycodi + alle 6 Spezialisten |
| `.opencode/commands/` | ✅ 13 Commands | Alle Workflows abgedeckt |

### 🔧 Gerade implementiert (dieser Upgrade)

| Bereich | Was wurde gebaut |
|---------|-----------------|
| `services/embeddings/main.py` | FastAPI Embedding-Service via Ollama nomic-embed-text |
| `services/ingest/main.py` | Hermes-Extractor: inbox/ → extracts/ → Qdrant |
| `services/retrieval/main.py` | RAG-Retrieval mit Zone-Enforcement |
| `services/model-routing/main.py` | Intelligente Modell-Selektion |
| `services/orchestrator/supervisor.py` | route_to_agent() mit echtem LLM-Routing |
| `opencode.json` | GPT-5.5 + Highx Mode für alle Agenten |
| `opencode.json` | MCP Server context7 + gh-grep aktiviert |

### 📋 Noch offen (priorisiert)

#### P0 — Blockiert MVP (sofort)

| # | Was | Wo | Wer |
|---|-----|----|-----|
| 1 | Qdrant-Collections initialisieren | `infra/scripts/init-qdrant.py` ausführen | kirobi-ops |
| 2 | Docker Compose: embeddings/ingest/retrieval/model-routing Services hinzufügen | `docker-compose.yml` | kirobi-ops |
| 3 | `.env.example` mit neuen Service-Ports erweitern | `.env.example` | kirobi-ops |

#### P1 — Wichtig (diese Woche)

| # | Was | Wo | Wer |
|---|-----|----|-----|
| 4 | Flowise-Flows für alle 14 Agenten erstellen | `integrations/flows/` | kirobi-architect |
| 5 | FastAPI-Service-Tests (Coverage = 0%) | `tests/unit/services/` | kirobi-coder |
| 6 | `apps/dashboard/` implementieren | `apps/dashboard/` | kirobi-frontend |
| 7 | `agents/hermes/` — echtes LLM-Reasoning | `agents/hermes/agent.py` | kirobi-coder |
| 8 | `agents/opencode/` + `agents/openclaw/` vervollständigen | `agents/opencode/`, `agents/openclaw/` | kirobi-coder |

#### P2 — Zukunft (nächster Sprint)

| # | Was | Wo | Wer |
|---|-----|----|-----|
| 9 | `apps/mobile/` — React Native oder PWA-Extension | `apps/mobile/` | kirobi-frontend |
| 10 | `apps/voice/` — Voice-First Interface | `apps/voice/` | kirobi-frontend |
| 11 | `services/analytics-service/` — Langfuse-Integration | `services/analytics-service/` | kirobi-coder |
| 12 | `services/image-generation/` — Stable Diffusion | `services/image-generation/` | kirobi-coder |
| 13 | M365-Integration aktivieren | `integrations/connectors/` | kirobi-architect |
| 14 | `kidi/` — serve-Endpoint für MCP-Server | `kidi/serve.py` | kirobi-coder |

---

## OpenCode Infrastruktur — Upgrade-Status

### Agenten (7/7 ✅)

| Agent | Modell | Reasoning | Skill |
|-------|--------|-----------|-------|
| keycodi | gpt-5.5 | high | ✅ keycodi-orchestrator |
| kirobi-architect | gpt-5.5 | high | ✅ kirobi-architect |
| kirobi-coder | gpt-5.5 | medium | ✅ kirobi-coder |
| kirobi-ops | gpt-5.5 | medium | ✅ kirobi-ops |
| kirobi-frontend | gpt-5.5 | medium | ✅ kirobi-frontend |
| kirobi-reviewer | gpt-5.5 | high | ✅ kirobi-reviewer |
| kirobi-docs | gpt-5.5 | low | ✅ kirobi-docs |

### MCP Server (3/4 aktiv)

| Server | Status | Zweck |
|--------|--------|-------|
| kirobi-supervisor | ✅ Aktiv | `python3 -m kirobi_core status --json` |
| context7 | ✅ Aktiviert | Externe Dokumentations-Suche |
| gh-grep | ✅ Aktiviert | GitHub Code-Suche |
| kirobi-context-db | ⏳ Pending | KIDI Redis-Store (kidi/serve.py fehlt) |

### Commands (13/13 ✅)

`architect`, `autonomous`, `agents`, `backlog`, `deploy`, `kidi`, `mission`, `refactor`, `review`, `scan`, `status`, `test`, `upgrade`

### Skills (7/7 ✅)

`keycodi-orchestrator`, `kirobi-architect`, `kirobi-coder`, `kirobi-ops`, `kirobi-frontend`, `kirobi-reviewer`, `kirobi-docs`

---

## Nächste empfohlene Mission

```bash
# P0 sofort ausführen:
make keycodi MISSION="Docker Compose um embeddings/ingest/retrieval/model-routing Services erweitern und Qdrant-Collections initialisieren"
```

---

## Architektur-Übersicht (nach Upgrade)

```
OpenCode (KeyCodi + 6 Spezialisten)
    ↓ GPT-5.5 + Highx Mode
    ↓ 13 Commands + 7 Skills + 3 MCP Server
    ↓
kirobi_core (Python stdlib)
    ↓ zones, audit, backlog, orchestrator, scanner, registry
    ↓
Services (FastAPI)
├── auth:8002          ✅ JWT-Auth
├── api:8003           ✅ Haupt-API + Ollama-Bridge
├── voice:8001         ✅ Whisper STT + Piper TTS
├── telegram:8005      ✅ Telegram-Bot
├── supervisor:8004    ✅ Autonomer Loop (route_to_agent implementiert)
├── embeddings:8006    🆕 nomic-embed-text via Ollama
├── ingest:8007        🆕 Hermes-Extractor Pipeline
├── retrieval:8008     🆕 RAG-Retrieval + Zone-Enforcement
└── model-routing:8009 🆕 Intelligente Modell-Selektion
    ↓
Infrastruktur
├── ollama:11434       LLM-Inferenz
├── qdrant:6333        Vector-DB (7 Collections)
├── postgres:5432      Relationale DB
├── caddy:80/443       LAN Reverse Proxy
└── flowise:3001       Workflow-Engine
    ↓
Agenten (Python)
├── agents/_base/      ✅ BaseAgent
├── agents/hermes/     ✅ Reasoning-Skelett
├── agents/obsidian/   ✅ Vault-CRUD
├── agents/opencode/   🔧 Skelett
└── agents/openclaw/   🔧 Skelett
    ↓
KIDI Context-DB (Redis)
└── kidi/context_db/   ✅ Zone-enforced Agenten-Kontext
```
