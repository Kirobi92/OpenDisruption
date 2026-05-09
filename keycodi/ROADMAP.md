# KeyCodi — Roadmap (Phasen 0–6)

**Zone:** WORKSPACE
**Letzte Aktualisierung:** 2026-05-07
**Quelle der Wahrheit für Reihenfolge.** KeyCodi weicht hier nicht ab.

---

## Übersicht

```
Phase 0  ──►  Phase 1  ──►  Phase 2  ──►  Phase 3  ──►  Phase 4  ──►  Phase 5  ──►  Phase 6
 Docs        ContextDB     Agent-          Obsidian-      KIDI +         Telegram        install.sh
              (Redis)      Skelette        Vault +        KEYBRODI        (gated)         + Polish
                                            Qdrant         (Metrics)
```

Detaillierte Tracking-Liste: `MILESTONES.md`. Phasen-Runbooks: `runbooks/phase-N-*.md`.

---

## GitHub-Abarbeitungsmodell

Dieses Dokument ist nicht nur Richtung, sondern Backlog-Struktur.

### Epics / Milestones

- **Ein GitHub-Milestone pro Phase**
- **Ein Epic-Issue pro Phase**
- **Mehrere Unter-Issues pro Lieferumfang / Exit-Kriterium**

### Pflicht-Labels

- `phase:0` bis `phase:6`
- `area:*` je betroffener Domäne
- `type:feature|fix|docs|test|infra|security`
- `gate:blocker|ready|passed`

### Reihenfolge für GitHub-Issues

1. Zuerst Blocker-/Gate-Issues
2. Dann Vertrags-/Test-Issues
3. Dann Implementierungs-Issues
4. Dann Doku-/Polish-Issues

### Minimaler Issue-Aufbau

1. Ziel
2. Scope in / out
3. Betroffene Dateien / Services
4. Verifikationsbefehl
5. Definition of done
6. Rollback / Revert-Hinweis

---

## Phase 0 — Architektur-Sign-off (LAUFEND)

**Ziel:** Architekturentscheidungen festschreiben, KeyCodi-HQ und Obsidian-Vault-Topologie bereitstellen — kein Runtime-Code.

**Lieferumfang**
- `docs/agent/MULTI-AGENT-ARCHITECTURE.md`, `KIDI-ENGINE.md`, `KEYBRODI-SUPERINTELLIGENZ.md`, `CONTEXT-WINDOW.md`, `TELEGRAM-INTEGRATION.md`
- `AGENT-DECISION-MATRIX.md`
- `metadata/ZONE-POLICY-MATRIX.md` + `metadata/AGENTREGISTRY.md` aktualisiert
- `keycodi/` (dieses Verzeichnis)
- `obsidian/` Vault-Topologie
- `.github/ISSUE_TEMPLATE/` für Backlog

**Exit-Kriterien**
1. Sven hat Architektur abgenickt (Kommentar im PR oder Issue mit Label `keycodi:approved`).
2. Drei offene Entscheidungen sind beantwortet:
   - Telegram: **Option A — Restricted Bridge**.
   - Token-Storage: **lokale `.env`**.
   - Installer: **repo-lokales `install.sh`, `--dry-run` als sicherer Default**.
3. CI grün.
4. README verlinkt auf `keycodi/` und `obsidian/`.

**Hard-Blocker**
- Telegram-Policy ist entschieden (Option A), aber Phase 5 bleibt gated bis Phase 4 grün ist und die lokale `.env` vollständig vorhanden ist.

---

## Phase 1 — Shared Context Window (Redis ContextDB)

**Ziel:** Zonen-getaggter Kurzzeit-Kontext-Store, der von allen späteren Agenten konsumiert wird.

**Lieferumfang**
- `kidi/context_db/` (Python-Paket: `client.py`, `keys.py`, `zone_guard.py`, `errors.py`).
- API: `put`, `get`, `query`, `merge` — exakt wie in `docs/agent/CONTEXT-WINDOW.md` §5 spezifiziert.
- `docker-compose.yml` erweitert um `redis`-Service hinter Profile `kidi`, gebunden an `${KIROBI_BIND_HOST:-127.0.0.1}:6379`.
- `.env.example`: `KIROBI_REDIS_PASSWORD`, `KIROBI_EGRESS_ALLOWED=false` als Default.
- Tests in `tests/unit/kidi/context_db/` (stdlib + pytest):
  `test_keys.py`, `test_zone_enforcement.py`, `test_merge.py`, `test_egress_guard.py`.
- Makefile-Target: `make test-kidi`.

**Exit-Kriterien**
1. `python -m pytest tests/unit -q` grün, mindestens 12 neue Tests.
2. `docker compose --profile kidi up redis` läuft + Healthcheck grün.
3. Cross-Zone-Read-Reject ist durch Test belegt.
4. Eintrag in `learnings/` zu mindestens einer Reibung (auch wenn nur „kein Problem").

**Hard-Blocker zu klären, bevor Phase 1 startet**
- Soll Redis Passwort-geschützt sein im Default? (Empfehlung: ja, generiert beim ersten `make bootstrap`.)
- AOF-Persistenz aktivieren? (Empfehlung: `appendfsync everysec`.)

---

## Phase 2 — Agenten-Skelette

**Ziel:** Headless-fähige Skelette für `opencode`, `openclaw`, `hermes-reasoner`, `obsidian` mit gemeinsamer Basisklasse.

**Lieferumfang**
- `agents/_base/agent.py` — Basisklasse: ContextDB-Anbindung, deklarierte Zonen, `handle(task)`-Interface, Audit-Logging.
- `agents/{opencode,openclaw,hermes,obsidian}/agent.py` — minimales Echo-Verhalten.
- Dockerfile pro Agent + Compose-Einträge hinter Profile `agents`.
- Makefile: `make agent-<name> TASK='...'` ruft Agent headless auf.
- Tests: pro Agent mindestens `test_handle_smoke.py`, `test_zone_refusal.py`.

**Exit-Kriterien**
1. Alle vier Agenten reagieren auf eine Test-Task headless.
2. Zonen-Verstoß durch Test belegt → wird abgelehnt.
3. CI grün.

---

## Phase 3 — Obsidian-Vault + Knowledge-Graph

**Ziel:** `agents/obsidian/` liest/schreibt den lokalen Vault (`obsidian/`), nutzt **bestehende** Qdrant-Collections aus `metadata/COLLECTION-MAPPING.md` — **kein** paralleler Store.

**Lieferumfang**
- `agents/obsidian/agent.py` mit CRUD auf `obsidian/`-Vault.
- Daily-Note-Generator + MOC-Generator als Skripte unter `infra/scripts/`.
- Wired via `Makefile` — **nicht** automatisch als Cron.
- Embedding-Calls gehen ausschließlich an die zonen-passende Collection (Lookup-Logik).
- Tests: Vault-CRUD, Zonen-Mapping zu Qdrant-Collection, Refusal bei Mismatch.

**Exit-Kriterien**
1. Daily-Note + MOC werden für den Shared-Vault generiert.
2. Embedding-Mismatch wird durch Test belegt → Reject.
3. Pro Agent existiert in `obsidian/agents/<name>/00-Index.md` ein generierter MOC.

**Hard-Blocker**
- Default-Vault-Pfad: `obsidian/` (in-Repo) für Dev, `~/kidi-vault/` für User. Sven entscheidet.

---

## Phase 4 — KIDI-Engine + KEYBRODI-Orchestrator

**Ziel:** Konfidenz-gewichtete Synthese (KIDI) + deterministisches Routing (KEYBRODI). Metrik-Loop only — **keine** Selbst-Mutation.

**Lieferumfang**
- `kidi/core/collective_intelligence.py` — Synthese exakt wie `docs/agent/KIDI-ENGINE.md` §3.
- `kidi/keybrodi/orchestrator.py` — Routing-Tabelle aus `AGENT-DECISION-MATRIX.md` als statische Datenstruktur.
- Metrik-Schreiber → `kirobi-core/core-events.log` (existierende Konvention).
- Tests: Zonen-Preservation in `merge`, Konflikt-Detektion, Routing-Reject auf Zonen-Verstoß.

**Exit-Kriterien**
1. KEYBRODI routet eine Test-Task korrekt zum erwarteten Agenten.
2. KIDI synthetisiert zwei Inputs zu einem Output mit Quellen-Liste.
3. Zonen-Eskalation wird abgelehnt.
4. Metrik-Eintrag im Event-Log überprüfbar.

**Handoff-Vorbereitung:** Erst nach Phase 4 ist KEYBRODI funktionsfähig genug, dass `HANDOFF-TO-KEYBRODI.md` greifen kann.

---

## Phase 4.5 — External Agent Track (PARALLEL, Sven-Override 2026-05-09)

**Status:** Sven-Override für parallelen Track erteilt. Kein Blocker für Phase 4 oder 5; läuft additiv.

**Quelle:** `keycodi/decisions/0004-external-agent-integration.md`.

**Lieferumfang**
- Submodules unter `external/hermes-agent/` und `external/openclaw/` (Pin auf konkrete Refs vor Merge).
- Compose-Profile `external-agents` mit Services `hermes-runtime` und `openclaw-gateway`.
- Caddy-Routes `/hermes/*` und `/openclaw/*` hinter `@not_edge_private`.
- `infra/scripts/install-aionui.sh` für host-seitige `.deb`-Installation des AionUi-Cockpits.
- AGENTREGISTRY-Einträge 21–23, ZONE-POLICY-MATRIX um drei Zeilen erweitert.
- Doku unter `docs/agent/EXTERNAL-AGENT-INTEGRATION.md`.

**Exit-Kriterien**
1. `make integration-test` bleibt grün.
2. `docker compose --profile external-agents config` validiert.
3. Caddyfile validiert (`caddy validate`).
4. Beide externe Container starten und Healthchecks werden grün.
5. AionUi-Installer bleibt im `--dry-run` Default — Apply nur explizit.

**Hart ausgeschlossen**
- Cloud-Provider in Hermes (alle deaktiviert ausser `custom`/Ollama).
- FAMILY_PRIVATE/SACRED-Mounts in beide Container.
- Hermes API-Server ohne `API_SERVER_KEY`.
- AionUi in Docker (statt host-side `.deb`).

---

## Phase 5 — Telegram-Integration (GATED)

**Voraussetzung:** Sven hat Option A aus `docs/agent/TELEGRAM-INTEGRATION.md` §2 gewählt. Phase 5 bleibt trotzdem gated bis Phasen 1–4 abgeschlossen und die lokale `.env` vollständig vorhanden ist.

**Lieferumfang (nur bei Option A)**
- Sechs Bot-Handler in eigenen Containern, jeweils unter Profile `telegram`.
- `agents/_telegram/zone_filter.py` — einziger Choke-Point, lehnt FAMILY_PRIVATE/SACRED/QUARANTINE hart ab.
- Redis-ACL-User für Telegram-Service (nur `ctx:PUBLIC:*` und `ctx:WORKSPACE:*`).
- `infra/scripts/daily-team-meeting.sh` als Opt-in (Cron **nicht** automatisch installiert).
- Tests für jeden Reject-Pfad.

**Exit-Kriterien**
1. Default `KIROBI_TELEGRAM_ENABLED=false`.
2. Jeder gesperrte Zonen-Wert ist durch Test belegt.
3. Kein Token in `.env.example`, kein Token im Repo.

---

## Phase 6 — `install.sh` + Doku-Polish

**Ziel:** Repo-lokaler `install.sh`, der `bootstrap.sh` umhüllt und neue Phasen integriert. Gewählte Option: komfortabel und sicher — lokal aus dem Clone, `--dry-run` als Standard, `--apply` explizit.

**Lieferumfang**
- `install.sh` mit `--dry-run` als Standard.
- Update von `README.md`, `BENUTZERHANDBUCH.md`, `QUICK-REFERENCE.md`.
- Eintrag in `CHANGELOG.md`.

**Exit-Kriterien**
1. `./install.sh --dry-run` läuft auf einem frischen Clone fehlerfrei.
2. Doku konsistent mit allen vorherigen Phasen.

---

## Reihenfolge-Garantie

Phasen sind **strikt linear**: 0 → 1 → 2 → 3 → 4 → (5) → 6.

Phase 5 ist gewählt (Option A), bleibt aber durch Zone-Filter, lokale `.env`-Konfiguration und explizites Opt-in geschützt. Alle Phasen müssen abgeschlossen sein, bevor die nächste startet.

---

## Nächste GitHub-Arbeitspakete ab jetzt

1. **Phase-0-Cleanup abschließen**
   - Architektur-Sign-off dokumentieren
   - Milestones/Status angleichen
   - Root- und Bereichs-Instruktionen pflegen
2. **Phase 4 vorbereiten**
   - Epic für `KIDI + KEYBRODI` anlegen
   - Unter-Issues für `collective_intelligence.py`, `orchestrator.py`, Routing-Tabelle, Metriken, Tests
3. **Phase 5 weiter gated halten**
   - Telegram nur Break/Fix und sichere `.env`-Konfiguration
   - Keine Scope-Ausweitung vor grünem Phase-4-Gate
4. **Phase 6 als Abschluss-Milestone**
   - Installer-Polish
   - README/Handbuch/Quick-Reference/Changelog angleichen

---

## Status-Zeile (KeyCodi pflegt)

```
Phase 0: 🟢 DONE
Phase 1: 🟢 DONE
Phase 2: 🟢 DONE
Phase 3: 🟡 IN PROGRESS
Phase 4: ⚪ PENDING
Phase 4.5: 🟡 IN-PROGRESS (Sven-Override 2026-05-09, parallel)
Phase 5: ⚪ PENDING (Option A gewählt, gated)
Phase 6: ⚪ PENDING
```

Legende: ⚪ pending · 🟡 in progress · 🟢 done · 🟠 blocked · 🔴 failed
