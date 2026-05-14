---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: ACTIVE
---

# RESTRUCTURING_PLAN.md

Stufenweise, sicher umsetzbar. Jede Phase mit **Ziel**, **konkreten Aufgaben**,
**betroffenen Pfaden**, **Akzeptanzkriterien**, **Risiken** und **empfohlener Reihenfolge**.

> Keine Phase ohne grünes `make integration-test` davor und danach.

---

## Phase 0 — Sicherheits- und Backup-Vorbereitung
**Dauer: 1 h** · **Risiko: 🟢 niedrig**

### Ziel
Sicherer Ausgangszustand. Reversibel.

### Aufgaben
1. Branch erstellen: `git checkout -b chore/audit-restructure-phase0`
2. Vollbackup: `make backup` (oder `bash infra/scripts/backup.sh`)
3. Verifizieren: Tar-Inhalt listen, Größe prüfen
4. **Restore-Test in Sandbox-Verzeichnis** (NEU) → wenn `restore.sh` fehlt, scaffold
5. `git tag pre-restructure-2026-05-14` setzen

### Akzeptanzkriterien
- [ ] Backup-Tar existiert in `archive/snapshots/`
- [ ] Restore-Test erfolgreich gegen `/tmp/restore-test/`
- [ ] Git-Tag gepusht
- [ ] `.env` in `.gitignore` bestätigt

### Risiken
- Backup zu groß (>10 GB) → temporär exkludieren von `data/`-Volumes

---

## Phase 1 — Quick Wins (Security + Ops)
**Dauer: 4–6 h** · **Risiko: 🟢 niedrig**

### Ziel
Top-3-Critical-Findings + Telegram online.

### Aufgaben (in Reihenfolge)

#### 1.1 Telegram-Service starten (5 min)
```bash
docker compose up -d telegram
docker compose ps telegram
docker compose logs --tail=50 telegram
```
**Akzeptanz:** `/getMe` über Container erreichbar, Bot reagiert auf `/start`.

#### 1.2 5 Services auf 127.0.0.1 (30 min)
- `services/api/main.py` (Endezeile)
- `services/auth/main.py`
- `services/model-routing/main.py`
- `services/media-processing/main.py`
- `services/video-generation/main.py`

Pattern:
```python
host = os.getenv("BIND_HOST", "127.0.0.1")
uvicorn.run(app, host=host, port=PORT)
```
**Akzeptanz:** `ss -tnl` zeigt nur 127.0.0.1-Bindings.

#### 1.3 JWT-Secret + Postgres-Pass: Fail-fast (15 min)
- `services/auth/main.py:31` → `os.environ["JWT_SECRET_KEY"]` (KeyError wenn fehlt)
- Bei `services/{api,auth,telegram}/main.py`: Postgres-Pass-Fallback entfernen

**Akzeptanz:** Test-Lauf ohne env-Var schlägt mit klarer Meldung fehl.

#### 1.4 CORS auf 3 Services härten (30 min)
- `services/model-routing/main.py:109`
- `services/personal-agents/app/main.py`
- `services/nutzi/app/main.py`

CORS-Pattern aus `services/ingest/main.py:195` übernehmen.
**Akzeptanz:** `curl -H "Origin: https://attacker.com" ...` → CORS-Header fehlen.

#### 1.5 Healthchecks ergänzen (60 min)
In `docker-compose.yml`:
- `api`: `healthcheck.test: ["CMD","python","-c","import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).status==200 else 1)"]`
- `auth`: ersetze TCP-Probe durch HTTP-Probe
- `orchestrator`, `voice-processing`, `telegram`, `hermes-runtime`: vergleichbar

**Akzeptanz:** `docker compose ps` zeigt 35/35 healthy nach 90 s.

#### 1.6 Hermes per-User-Memory (30 min)
- `services/hermes-runtime/config/cli-config.yaml`: filesystem-MCP-Pfad um `/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/` ergänzen
- Pro User-Knowledge-Graph in `Datenspeicher/.../{Sven,Samira,Sineo}/agent/memory/knowledge_graph.json`

**Akzeptanz:** Hermes-CLI sieht beide Pfade.

### Phase-1-Akzeptanz
- [ ] `make integration-test` grün
- [ ] Telegram-Bot antwortet auf `/start`
- [ ] Top-3-Critical-Findings (CRIT-1, CRIT-2, CRIT-3) erledigt
- [ ] Healthchecks 35/35

---

## Phase 2 — Doku-Konsolidierung
**Dauer: 2 h** · **Risiko: 🟢 niedrig**

### Ziel
25 Root-MDs → 10 kanonisch + `docs/` + `archive/docs-old/`.

### Aufgaben
1. Erstelle `archive/docs-old/README.md` mit Mapping (alt → neu / archiviert)
2. Verschiebe (mit `git mv`):
   - `ARCHITECTURE.md` → `archive/docs-old/`
   - `COMPLETION-REPORT.md`, `IMPLEMENTATION-SUMMARY.md`, `ULTIMATE-IMPLEMENTATION-ROADMAP.md` → `archive/docs-old/`
   - `POST-CLONE-SETUP.md` → in README mergen, danach archivieren
   - `AGENT-SYSTEM-PROMPT.md`, `AGENT-DECISION-MATRIX.md`, `AGENT-INSTALLATION.md`, `AGENT-RECOVERY.md` → `docs/agents/` und `docs/TROUBLESHOOTING.md`
   - `AUDIT-REPORT.md` → ersetzt durch CODEBASE_AUDIT.md (alt archivieren)
   - `ENTWICKLERDOKUMENTATION.md` → DE-Inhalte in `DEVELOPER-RUNBOOK.md` mergen
   - `CHANGELOG.md` → optional `archive/docs-old/` (git log ersetzt)
   - `QUICK-REFERENCE.md` → in README mergen
3. Erstelle `docs/SERVICE-REGISTRY.md` (alle Ports, Owner, Status)
4. Erstelle `docs/DATA-PIPELINE.md` (sources → extracts → canon → experiences)
5. Erstelle `docs/ORCHESTRATION-MAP.md` (KeyCodi vs. Hermes vs. Supervisor)
6. Erstelle `docs/TROUBLESHOOTING.md`
7. README.md auf Quick-Start + Links zu `docs/` reduzieren

### Akzeptanz
- [ ] Maximal 10 MDs im Root
- [ ] `docs/` enthält die 6+ neuen Referenzdokumente
- [ ] Alle Links in archivierten Dateien zeigen auf neue Pfade
- [ ] `make integration-test` grün

### Risiken
- Externe Links (z.B. von Issues) zeigen ins Leere — Migration mit Redirect-Kommentaren in archivierten Files

---

## Phase 3 — Compose / Service-Cleanup
**Dauer: 3 h** · **Risiko: 🟡 mittel**

### Ziel
Service-Sprawl beseitigen, Resource-Limits, Mount-Hygiene.

### Aufgaben
1. **Entfernen:** `services/openclaw-gateway` Service-Block aus `docker-compose.yml` und Verzeichnis
2. **Aus Compose nehmen:** `apps/desktop`, `apps/mobile` falls referenziert (Frozen)
3. **Resource-Limits:** in `docker-compose.yml` ergänzen
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '1.0'
   ```
   Pro Service angemessen (api: 2G, voice: 4G, ollama: per profile)
4. **RW→RO**: `./kirobi-core:/kirobi-core` für `supervisor` auf `:ro` falls möglich
5. **Service-URLs zentralisieren:** `services/_shared/urls.py`

### Akzeptanz
- [ ] `docker compose config` validiert
- [ ] `make integration-test` grün
- [ ] `docker stats` zeigt Limits aktiv

### Risiken
- Memory-Limits zu eng → OOM-Kills; mit `docker stats` Baseline messen, +30 % Puffer

---

## Phase 4 — Architektur-Refactoring (api + voice-processing)
**Dauer: 1–2 d** · **Risiko: 🟠 hoch**

### Ziel
Monolithen aufteilen, ohne Funktionsverlust.

### Aufgaben

#### 4.1 services/api/main.py Split
Ziel-Layout (siehe `TARGET_STRUCTURE.md` §1):
```
services/api/app/
  main.py        # FastAPI() + Router-Registrierung + Lifespan
  deps.py        # auth, db, redis (Depends)
  routers/
    health.py
    conversations.py
    messages.py
    agents.py
    operator.py
  schemas.py
  services/
    ollama_bridge.py
    agent_registry.py
```

Schritte (jeweils mit Tests):
1. `routers/health.py` extrahieren → Tests grün
2. `routers/conversations.py` extrahieren → Tests grün
3. `routers/messages.py` extrahieren → Tests grün
4. `routers/agents.py` extrahieren → Tests grün
5. `routers/operator.py` extrahieren → Tests grün

#### 4.2 services/voice-processing Modulisierung
- `whisper_client.py`, `piper_client.py`, `routes.py`, `main.py`
- Tests pro Modul

### Akzeptanz
- [ ] `services/api/app/main.py` < 100 LOC
- [ ] Jede Route hat Test in `tests/services/api/`
- [ ] HTTP-Verhalten unverändert (Verträge halten)
- [ ] `make integration-test` grün

### Risiken
- Versteckte Imports → Tests müssen Coverage haben
- Lifespan-Reihenfolge: Postgres-Bootstrap muss vor Router-Registrierung laufen

---

## Phase 5 — Tests & Qualitätssicherung
**Dauer: 2 d (Sprint)** · **Risiko: 🟢 niedrig**

### Ziel
- Coverage 30 % minimum (Sprint 1)
- Pro Service mindestens Health + 1 Happy-Path-Test
- CI veröffentlicht Coverage

### Aufgaben
Siehe `TESTING_STRATEGY.md` Phase 1+2.

### Akzeptanz
- [ ] `make ci-coverage` grün mit `fail_under=30`
- [ ] `tests/integration/test_smoke.py` deckt 12 Services ab
- [ ] Codecov-Badge im README

---

## Phase 6 — Performance, Security, DevEx
**Dauer: 3 d** · **Risiko: 🟡 mittel**

### Ziel
Härtung über 80 / 100 Security, DevEx-Verbesserungen.

### Aufgaben
1. **Auth-Pflicht:** Alle Schreib-Endpoints `Depends(get_current_user)`
2. **Rate Limits:** SlowAPI-Middleware shared
3. **Logging-Standardisierung:** JSON, structlog
4. **Pydantic-Settings:** Central env-validation
5. **`make dev`:** Hot-Reload für lokale Entwicklung
6. **pip-audit + npm audit** in CI
7. **Renovate-Bot** für Dependency-Updates

### Akzeptanz
- [ ] Audit-Score > 80 / 100
- [ ] `pip-audit` ohne CRITICAL findings
- [ ] `npm audit --audit-level=high` ohne findings
- [ ] `make dev` startet alle Services in < 60 s

---

## Phase 7 — Frontend-Konsolidierung + finale Doku
**Dauer: 1 Woche** · **Risiko: 🟠 hoch**

### Ziel
Apps von 6 → 2–3, finale Dokumentation, Übergabe-fertig.

### Aufgaben
1. pnpm-Workspace einführen (`pnpm-workspace.yaml`)
2. `apps/portal` → `apps/web/src/app/portal/` mergen
3. `apps/admin` → `apps/dashboard/` mergen, Verzeichnis umbenennen `admin-dashboard`
4. `apps/web-svelte`, `apps/_design` archivieren
5. Voice-Tab in `apps/web` integrieren (oder `apps/voice` belassen)
6. README final überarbeiten
7. `docs/DEPLOYMENT.md` schreiben
8. **Demo-Video** aufnehmen (5 min Walkthrough)

### Akzeptanz
- [ ] `apps/` enthält ≤ 4 aktive Apps
- [ ] Disk-Verbrauch `node_modules` < 1.5 GB
- [ ] Alle frontends bauen mit `pnpm -r build`
- [ ] README ist self-explanatory für neuen Entwickler

---

## Übergreifende Regeln

- **Eine Phase pro PR**, kleine Commits
- **Conventional Commits** strikt
- **Nach jeder Phase:** Tag setzen (`phaseN-done`)
- **Bei Failed-Test:** Sofort revertieren, nicht „forward fixen"
- **CHANGELOG.md** ersetzt durch `git log` + GitHub-Releases

## Phasen-Reihenfolge (empfohlen, fix)

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 5 (parallel zu 4)
                                            ↓
                                          Phase 4
                                            ↓
                                          Phase 6 → Phase 7
```

Phase 5 (Tests) **parallel** zu Phase 4 (Refactoring) erlaubt — sogar empfohlen,
weil Tests dem Refactor Sicherheit geben.
