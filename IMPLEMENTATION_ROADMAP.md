---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: ACTIVE
---

# IMPLEMENTATION_ROADMAP.md

Konkrete, ausführbare Schritte. Jeder Block ist standalone, mit Befehlen.

---

## ⚡ HEUTE (1–2 h) — Sofort-Wins

### Schritt 1 · Telegram online (5 min)
```bash
cd /home/sven/OpenDisruption
docker compose up -d telegram
docker compose ps telegram
docker compose logs --tail=80 telegram
```
**Verifikation:** Telegram an @Disruptivbot → `/start` → Bot antwortet.

### Schritt 2 · 0.0.0.0 → 127.0.0.1 (30 min)
Patches anwenden auf:
```
services/api/main.py
services/auth/main.py
services/model-routing/main.py
services/media-processing/main.py
services/video-generation/main.py
```
Patch-Pattern (am Ende jeder Datei):
```diff
- uvicorn.run(app, host="0.0.0.0", port=PORT)
+ uvicorn.run(app, host=os.getenv("BIND_HOST", "127.0.0.1"), port=PORT)
```
Anschließend:
```bash
docker compose restart api auth model-routing media-processing video-generation
ss -tnlp | grep -E ':800[2-9]|:801[0-7]'   # nur 127.0.0.1
```

### Schritt 3 · JWT-Secret fail-fast (10 min)
`services/auth/main.py:31`:
```diff
- JWT_SECRET = os.getenv("JWT_SECRET_KEY", "CHANGEME-in-production-...")
+ JWT_SECRET = os.environ["JWT_SECRET_KEY"]   # KeyError wenn fehlt
+ if "CHANGEME" in JWT_SECRET or len(JWT_SECRET) < 32:
+     raise RuntimeError("JWT_SECRET_KEY too weak. Set a 32+ char random string in .env.")
```

### Schritt 4 · CORS härten (30 min)
Pattern in `services/_shared/cors.py` anlegen, in `model-routing`, `personal-agents`,
`nutzi` einbinden.

### Schritt 5 · Healthchecks fertigstellen (60 min)
In `docker-compose.yml` für api/auth/orchestrator/voice-processing/telegram/hermes-runtime
HTTP-basierte Healthchecks (Python urllib).

**End of Day check:**
```bash
make integration-test
docker compose ps          # 35/35 healthy
```

---

## 🚀 DIESE WOCHE (1–3 d) — Konsolidierung

### Schritt 6 · openclaw-gateway entfernen (10 min)
```bash
rm -rf services/openclaw-gateway
```
Dann aus `docker-compose.yml` den Service-Block entfernen.

### Schritt 7 · 25 Root-MDs auf 10 reduzieren (2 h)
```bash
mkdir -p archive/docs-old docs/agents
git mv ARCHITECTURE.md archive/docs-old/
git mv COMPLETION-REPORT.md IMPLEMENTATION-SUMMARY.md ULTIMATE-IMPLEMENTATION-ROADMAP.md \
       AUDIT-REPORT.md AGENT-DECISION-MATRIX.md AGENT-INSTALLATION.md AGENT-RECOVERY.md \
       AGENT-SYSTEM-PROMPT.md POST-CLONE-SETUP.md QUICK-REFERENCE.md CHANGELOG.md \
       ENTWICKLERDOKUMENTATION.md  archive/docs-old/
```
Dann:
- `archive/docs-old/README.md` mit Mapping schreiben
- `docs/SERVICE-REGISTRY.md` schreiben (Vorlage in TARGET_STRUCTURE)
- `docs/DATA-PIPELINE.md` skizzieren
- `docs/ORCHESTRATION-MAP.md` skizzieren

### Schritt 8 · Pydantic-Settings (1.5 h)
- `kirobi_core/settings.py` anlegen
- 1–2 Services pilothaft umstellen (`auth`, `model-routing`)
- Restliche im Verlauf

### Schritt 9 · Backup + Restore-Test (2 h)
- `infra/scripts/restore.sh` schreiben
- In `make backup-test` einbinden
- CI-Job: monatlich

### Schritt 10 · Hermes-Setup (PROBE — siehe Hermes-Skill, separat) (1 h)
- `agents/hermes/orchestrator.yaml`
- `services/hermes-runtime/config/skills/opendisruption-orchestrator/SKILL.md`
- `cli-config.yaml` System-Prompt erweitert

---

## 🌳 NÄCHSTE 2 WOCHEN — Test-Sprint

### Schritt 11 · Coverage-Setup
```bash
pip install pytest-cov coverage[toml]
```
- `pyproject.toml` Konfig
- `make ci-coverage` Target
- CI-Workflow `.github/workflows/test.yml` erweitern
- Codecov-Token in Secrets
- README-Badge

### Schritt 12 · Service-Tests (P0)
Erstelle pro Service:
- `tests/services/<name>/test_health.py`
- `tests/services/<name>/test_routes.py`

P0-Reihenfolge (Risiko-basiert): **api, auth, ingest, retrieval**

### Schritt 13 · Integration-Smoke
`tests/integration/test_smoke.py` mit Health-Pings für 12 Services.

---

## 🏗 NÄCHSTE 4 WOCHEN — Architektur-Refactoring

### Schritt 14 · services/api Split (siehe RESTRUCTURING_PLAN §4.1)
1. Branch `refactor/api-split`
2. Routers extrahieren in 5 PRs (je 1 Router)
3. Tests grün lassen

### Schritt 15 · voice-processing Modulisierung
1. `whisper_client.py`, `piper_client.py`, `routes.py`
2. Tests pro Modul

### Schritt 16 · Auth-Pflicht für Schreib-Endpoints
- Shared `services/_shared/auth_deps.py`
- Pro Service Schreib-Routen mit `Depends(get_current_user)`

---

## 🎨 NÄCHSTE 6 WOCHEN — Frontend-Konsolidierung

### Schritt 17 · pnpm-Workspace
```bash
cd apps && pnpm init  # workspace
echo "packages:\n  - 'web'\n  - 'admin-dashboard'\n  - 'voice'" > pnpm-workspace.yaml
```

### Schritt 18 · apps/portal → apps/web/portal/
Verschmelzen, gemeinsame Components in `apps/web/src/components/shared/`.

### Schritt 19 · apps/admin → apps/dashboard
Mergen, umbenennen zu `apps/admin-dashboard/`.

### Schritt 20 · apps/web-svelte archivieren
```bash
mv apps/web-svelte archive/apps-old/
```

---

## 📅 6-Monats-Vision

| Monat | Meilenstein | Akzeptanz |
|---|---|---|
| M1 | Phase 0–2 abgeschlossen | Telegram live, Top-3-Crit fixed, ≤10 Root-MDs |
| M2 | Tests-Sprint 1 abgeschlossen | Coverage 30 %, P0-Services getestet |
| M3 | api + voice-processing refactored | Router-Split, < 100 LOC main.py |
| M4 | Auth-Pflicht durchgezogen | Alle Schreib-Routen geschützt |
| M5 | Frontend konsolidiert | ≤ 3 Apps, pnpm-Workspace |
| M6 | Coverage 60 %+, Demo-fertig | Pitch-Video aufgenommen |

---

## 🛡 Sicherheits-Gate vor jedem Merge

```bash
make integration-test                  # Pflicht
ruff check services/ kirobi_core/      # neu
pip-audit -r services/api/requirements.txt --strict
( cd apps/web && npm audit --audit-level=high )
```

---

## 🚦 Erste empfohlene Aktion JETZT

```bash
# 1. Branch
git checkout -b chore/audit-phase0-quickwins

# 2. Backup (Phase 0)
make backup
git tag pre-restructure-2026-05-14

# 3. Telegram online (Schritt 1)
docker compose up -d telegram
docker compose ps telegram

# 4. Verifizieren in Telegram-App
#    @Disruptivbot → /start
```

Wenn Bot antwortet → weiter mit Schritt 2 (0.0.0.0-Fix).

---

## Definition of Done — pro Phase

- [ ] Akzeptanzkriterien aus `RESTRUCTURING_PLAN.md` erfüllt
- [ ] `make integration-test` grün
- [ ] CHANGELOG-Eintrag (oder Release-Notes auf GitHub)
- [ ] Tag `phaseN-done` gesetzt
- [ ] Telegram-Status an @Disruptivbot gepostet (durch Hermes orchestrator)
