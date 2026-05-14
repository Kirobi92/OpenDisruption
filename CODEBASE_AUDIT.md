---
zone: WORKSPACE
created: 2026-05-14
created_by: GitHub Copilot CLI (Claude Opus 4.7)
auditor: OpenDisruption Audit Crew (scope-architecture-deep + scope-security-quality)
version: 1.0
status: ACTIVE
---

# CODEBASE_AUDIT.md — OpenDisruption / Kirobi

## 0. Executive Summary

OpenDisruption ist eine **technisch ambitionierte, lokale-first KI-Familienplattform** mit
solider Sicherheits-Grundausrichtung (5-Zone-Modell, SACRED=403, Caddy als alleiniger
Edge), die jedoch unter erheblicher **organisatorischer Schuld** leidet:

- **35 Compose-Services** (16–18 mit echtem Code, mehrere Karteileichen)
- **6 aktive Web-Frontends** (web, portal, admin, dashboard, voice, web-svelte) — Doppelung
- **25 Markdown-Dateien im Root** — Doku-Sprawl
- **Nur 2 von 16 Backend-Services haben echte Unit-Tests** (analytics, orchestrator)
- **5 Services binden noch auf `0.0.0.0`** (api, auth, model-routing, media-processing, video-generation)
- **3 Services CORS-Wildcard + ohne Auth** (model-routing, personal-agents, nutzi)
- **Hermes-Runtime-Rolle unklar** vs. supervisor / orchestrator / KeyCodi

### Gesamt-Score (Audit-Crew-Mittelwerte)
| Dimension | Score | Trend |
|---|---|---|
| Funktionalität | **9 / 10** | ✅ Läuft |
| Sicherheit (Code-Layer) | **3.5 / 10** | 🔴 Critical Gaps |
| Sicherheit (Zone-Modell) | **8 / 10** | ✅ Solides Konzept |
| Wartbarkeit | **6 / 10** | 🟡 Doku scattered |
| Testabdeckung | **2 / 10** | 🔴 12 % Services |
| Observability | **5 / 10** | 🟡 Healthchecks lückenhaft |
| Architektur-Klarheit | **6 / 10** | 🟡 Service-Sprawl |
| **Gesamt** | **5.6 / 10** | 🟡 |

### Distanz zum Idealzustand
**~6–8 Wochen fokussierte Arbeit** für 80 % des Gewinns.
Kein Rewrite nötig, nur **Konsolidierung + Härtung**.

---

## 1. Codebase-Inventar

### Sprachen / LOC
| Sprache | Dateien | Anteil |
|---|---|---|
| TypeScript | 14 680 | 86 % |
| Python | 1 916 | 11 % |
| JavaScript | 332 | 2 % |
| TSX | 292 | 2 % |
| Shell | 212 | 1 % |
| YAML | 244 | 1 % |

### Backend-Services (sortiert nach LOC)
| Service | LOC | Files | Healthcheck | Tests | Auth | CORS | Status |
|---|---|---|---|---|---|---|---|
| telegram | 4 761 | 14 | ❌ | ❌ | ✅ | n/a | ⚠️ Container down |
| api | 2 262 | 3 | ❌ | ❌ | ⚠️ teilw. | ✅ | ✅ Aktiv |
| voice-processing | 1 880 | 5 | ❌ | ❌ | ❌ | ❌ | ✅ Aktiv |
| orchestrator | 1 261 | 1 | ❌ | ✅ (3) | n/a | n/a | ✅ Aktiv |
| nutzi | 1 001 | 3 | ✅ | ❌ | ❌ | 🔴 `*` | ⚠️ Spezialfall |
| auth | 790 | 3 | ✅ | ❌ | ✅ self | ✅ | ✅ Aktiv |
| music-generation | 780 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| ingest | 678 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| image-generation | 628 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| personal-agents (v2) | 563 | 1 | ✅ | ❌ | ❌ | 🔴 `*` | ✅ Aktiv |
| video-generation | 509 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| analytics-service | 485 | 1 | ✅ | ✅ (10) | ❌ | ✅ | ✅ Aktiv |
| embeddings | 466 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| retrieval | 362 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv (SACRED 403 ✅) |
| hermes-runtime | 316 | 1 | ❌ | ❌ | n/a | n/a | ✅ Aktiv |
| media-processing | 313 | 1 | ✅ | ❌ | ❌ | ✅ | ✅ Aktiv |
| model-routing | 185 | 1 | ✅ | ❌ | 🔴 keine | 🔴 `*` | ✅ Aktiv |
| **openclaw-gateway** | **0** | **0** | – | – | – | – | 🔴 **LEER** |

### Apps-Übersicht
| App | node_modules | src files | Aktiv | Empfehlung |
|---|---|---|---|---|
| apps/web | 745 MB | 41 | ✅ | **PRIMARY** behalten |
| apps/dashboard | 667 MB | 18 | ✅ | Behalten (Admin) |
| apps/portal | 603 MB | 19 | ✅ | **In `web` mergen** |
| apps/admin | 576 MB | 18 | ✅ | **In `dashboard` mergen** |
| apps/voice | 435 MB | 5 | ✅ | Behalten oder in `web` integrieren |
| apps/web-svelte | 177 MB | 19 | ⚠️ | **Archivieren** (POC) |
| apps/desktop | – | 4 | 🚧 Scaffold | Frozen (AGENTS.md) |
| apps/mobile | – | 0 | 🚧 Scaffold | Frozen (AGENTS.md) |
| apps/installer | – | 0 | 📄 Doc | Behalten als Doc |
| apps/_design | – | 0 | – | Archivieren |

**Disk savings**: ~3.5 GB durch pnpm-Workspace + Konsolidierung.

### Markdown-Doku (Root)
**25 Dateien** — viele redundant. Empfehlung: **10 kanonische** Dateien
(siehe `TARGET_STRUCTURE.md`).

---

## 2. Top-20 strukturelle Befunde

| # | Kategorie | Befund | Pfad-Beispiel | Schwere |
|---|---|---|---|---|
| 1 | Naming-Konflikt | `kirobi-core/` (MD-Identität) vs. `kirobi_core/` (Python-CLI) — beide aktiv | `kirobi-core/`, `kirobi_core/` | 🟠 |
| 2 | Service-Leiche | `services/openclaw-gateway/` enthält 0 Files | `services/openclaw-gateway/` | 🟡 |
| 3 | Verantwortungs-Doppelung | `orchestrator` + `supervisor`-Mode + `KeyCodi` + `Hermes` orchestrieren alle „irgendwie" | services/orchestrator/, agents/, keycodi/ | 🟠 |
| 4 | Frontend-Sprawl | 6 aktive Web-Apps mit überlappenden Funktionen | apps/* | 🟠 |
| 5 | API-Monolith | `services/api/main.py` = 2 262 LOC, 1 Datei | services/api/main.py | 🟠 |
| 6 | Voice-Monolith | `services/voice-processing/` = 1 880 LOC verteilt, aber unstrukturiert | services/voice-processing/ | 🟡 |
| 7 | Telegram-Monolith | `services/telegram/main.py` + 13 Beifiles, 4 761 LOC, **Container down** | services/telegram/ | 🔴 |
| 8 | Doku-Doppelung | `ARCHITECTURE.md` (37 KB) vs. `PROJECT-ARCHITECTURE.md` (10 KB) | Root | 🟡 |
| 9 | Doku-Doppelung | `DEVELOPER-RUNBOOK.md` (EN) vs. `ENTWICKLERDOKUMENTATION.md` (DE) | Root | 🟡 |
| 10 | Veraltete Reports | `COMPLETION-REPORT.md`, `IMPLEMENTATION-SUMMARY.md`, `ULTIMATE-IMPLEMENTATION-ROADMAP.md` (56 KB) | Root | 🟡 |
| 11 | Test-Lücke | 14/16 Backend-Services ohne Unit-Tests | tests/unit/ | 🔴 |
| 12 | Hardcoded Secrets-Fallback | `JWT_SECRET_KEY="CHANGEME-..."` Fallback | services/auth/main.py:31 | 🔴 |
| 13 | Hardcoded DB-Pass-Fallback | `POSTGRES_PASSWORD="changeme"` Fallback in 6 Services | mehrere | 🟠 |
| 14 | Externe Doppelmounts | docker-compose `kirobi-core/profiles:/app/profiles:ro` + Datenspeicher rw — verwirrend (jetzt funktional gelöst, Doku fehlt) | docker-compose.yml | 🟡 |
| 15 | Env-Sprawl | 183 Env-Vars in compose, keine Schema-Validierung | docker-compose.yml, .env.example | 🟠 |
| 16 | Healthcheck-Lücken | api, auth (TCP-only), orchestrator, voice-processing, telegram, hermes-runtime ohne sinnvollen Healthcheck | docker-compose.yml | 🔴 |
| 17 | CI-Coverage fehlt | `make integration-test` läuft Compile-Checks, aber kein `pytest --cov` | Makefile, .github/workflows/ | 🟠 |
| 18 | Resource Limits fehlen | Keine `mem_limit` / `cpus` außer GPU-Diensten | docker-compose.yml | 🟡 |
| 19 | RW-Mount wo RO reicht | `./kirobi-core:/kirobi-core` in Supervisor schreibend | docker-compose.yml | 🟡 |
| 20 | Hermes-Memory single-file | Hermes MCP `memory` zeigt auf `/opt/data/memory/knowledge_graph.json`, ignoriert per-User-Graphs unter `/Datenspeicher/.../*/agent/memory/` | services/hermes-runtime/config/cli-config.yaml | 🟠 |

---

## 3. Was funktioniert gut ✅

1. **Zone-Modell ist sauber definiert** (CLAUDE.md, AGENTS.md, ZONE-POLICY-MATRIX.md).
2. **Local-First-Prinzip durchgehalten** — Caddy als einziger Edge, sonst 127.0.0.1-Bind via `KIROBI_BIND_HOST`.
3. **Retrieval-Service erzwingt SACRED=403** ohne Override-Möglichkeit.
4. **Idempotente Installation** (`install.sh` + `.kirobi/install.json`).
5. **Personal-Agents v2 ist nach jüngstem Refactor sauber** (Anti-Halluzination zuerst, Datenspeicher als Quelle, Symlinks gesetzt, 574 Tests grün).
6. **CI-Gate `make integration-test` deckt** Unit-Tests + Compose-Validation + Shell-Lint + FastAPI-Compile + PWA-Manifest.
7. **Conventional-Commits-Konvention dokumentiert** (CONTRIBUTING.md, AGENTS.md).
8. **Skill-Pack-Architektur** (`.opencode/skills/`, `.agents/skills/`-Mirror) konsistent angelegt.
9. **Bot @Disruptivbot** ist erreichbar (getMe ✅).
10. **Datenspeicher-Pfad** (`/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/`) ist klar geregelt.

---

## 4. Was sofort weh tut 🔴

| # | Befund | Konsequenz heute | Fix in |
|---|---|---|---|
| A | **Telegram-Service-Container läuft nicht**, obwohl Bot konfiguriert | Sven kann nicht via Telegram steuern | < 5 min (`docker compose up -d telegram`) |
| B | 5 Services binden auf `0.0.0.0` statt `127.0.0.1` | LAN-Exposure trotz „local-first" | < 30 min (5 Patches) |
| C | 3 Services CORS-Wildcard + keine Auth | CSRF / Datenexfiltration via Browser möglich | < 1 h |
| D | JWT-Secret-Fallback `"CHANGEME-..."` | Bei vergessener `.env` läuft System mit bekanntem Secret | < 10 min |
| E | 14/16 Services ohne Tests | Jede Änderung ist russisches Roulette | Wochen |
| F | Hermes hat kein per-User-Memory-Mapping | Wissen wird nicht zwischen Sven/Samira/Sineo getrennt | 30 min Konfig |

---

## 5. Hauptdatenflüsse (wie sie heute laufen)

```
sources/inbox/  ─┐
sources/web/    ─┤  hermes-extractor / ingest
sources/imports ─┘     (services/ingest:8007)
                          │
                          ▼
                   extracts/{public,workspace,family-private}/
                          │
                          ├── embeddings:8004 ──► Qdrant (7 collections)
                          │
                          ▼
                   clusters/  → canon/ → experiences/
                          │
                          └── Postgres (zone_permissions, conversations, messages, audit_log)

User → Caddy → web/portal/dashboard/voice → api:8003 → {auth, retrieval, personal-agents, model-routing}
                                                  │
                                                  ▼
                                              ollama:11434
                                                  │
                                              fallback: GitHub Models (Copilot Pro+)
```

**Bruchstellen:**
- Datenfluss `sources/ → extracts/` ist **nicht codebasiert geprüft** — teils manuell.
- `clusters/ → canon/` hat **keinen automatisierten Promotion-Pfad**.
- `experiences/` wird nur teils befüllt.

---

## 6. Empfehlungs-Tabelle (Konsolidierung)

| Heute | Vorschlag | Effort | Risiko |
|---|---|---|---|
| `services/openclaw-gateway/` (leer) | Löschen aus `docker-compose.yml` | 5 min | 🟢 |
| `apps/web` + `apps/portal` | Mergen → `apps/web` (PWA + Portal-Routes) | 2 d | 🟠 |
| `apps/admin` + `apps/dashboard` | Mergen → `apps/admin-dashboard` | 2 d | 🟠 |
| `apps/web-svelte` | Archivieren (POC) | 30 min | 🟢 |
| `apps/desktop`, `apps/mobile` | Frozen lassen, aus compose nehmen | 30 min | 🟢 |
| `services/api/main.py` (2 262 LOC) | Split in `routers/{conversations,messages,agents,operator}.py` | 4 h | 🟡 |
| `services/telegram/` | Container starten + Healthcheck + Tests | 2 h | 🟢 |
| 25 Root-MDs | Auf 10 reduzieren (siehe TARGET_STRUCTURE.md) | 1 h | 🟢 |
| Doppelte Orchestrator-Schichten | KeyCodi = Coding-Orchestrator, Hermes = Familien-/Wissens-Orchestrator, Supervisor = Backlog-Runner — klar dokumentieren | 2 h | 🟢 |

---

## 7. Audit-Methodik

- **scope-architecture-deep** (explore agent, 277 s) — Architektur, Service-Sprawl, Doku
- **scope-security-quality** (explore agent, 249 s) — Security, Code-Quality, Quick-Patches
- **Direkte Inspektion** — Compose, Makefile, Telegram-API-Test, LOC-Statistik, Healthcheck-Status

Audit-Datum: **2026-05-14**
Nächster Review empfohlen: **nach Phase 3 (Konsolidierung) ~ +6 Wochen**
