---
zone: WORKSPACE
created_by: claude-opus-4.7
created_at: 2026-05-09
reviewer: pending
version: 1.0
status: Phase-1 Bestandsaufnahme (vor Säulen-Entscheidung)
---

# KIDI-Analysebericht — Phase 1 (Bestandsaufnahme)

**Mandat:** Sven hat am 2026-05-09 eine KIDI-Evolution mit 6 Säulen (AQAL, Spiral Dynamics, Phi-Harmonics, Quantum Resonance, Numerologische Resonanz, Samira-Heart-Upgrade) angefragt. Vor jeder Implementierung: ehrliche, vollständige Bestandsaufnahme.

**Methodik:** Schichtweise Inspektion gemäß `PROJECT-ARCHITECTURE.md` §2 (Layer 0–7). Direkte Quelle: aktueller Code, nicht Roadmap-Wunschzustand.

---

## 1. Realitätsabgleich: Was KIDI heute IST vs. was im Mandat angenommen wird

| Annahme im Mandat | Realität im Repo | Status |
|---|---|---|
| `kidi/engine.py` existiert mit Confidence-Weighted-Merge | Datei existiert nicht. Vorhanden: `kidi/serve.py` (MCP-Server) + `kidi/context_db/` (SQLite-Storage-Layer). | ❌ Annahme falsch |
| KIDI ist „bereits architektonisches Konzept und in Teilen als Code" | Konzept ja (`docs/agent/KIDI-ENGINE.md`, 137 Zeilen). Code: nur ContextDB + MCP-Tools. **Synthese-Engine = 0 Zeilen.** | ⚠️ Teilweise |
| KEYBRODI-Routing existiert | `kidi/keybrodi/` existiert nicht. `keycodi/MILESTONES.md` Phase 4 = alle Items offen. | ❌ Annahme falsch |
| 14 Agenten implementiert | `agents/` enthält 4 Skeletons (`opencode`, `openclaw`, `hermes`, `obsidian`) + `_base`. Weitere „Agenten" (Samira, Sineo, Research-Crew, etc.) nur in `metadata/AGENTREGISTRY.md` dokumentiert, **kein Code**. | ❌ Annahme stark übertrieben |
| Samira-Heart-Agent ist „Mediations-Bot" | Existiert nur als Registry-Eintrag und in Dokumenten. Kein Python-Modul, keine Tests. | ❌ Nicht implementiert |
| Phi-Harmonics, AQAL, Spiral Dynamics, Quantum Resonance bereits geplant | Keine Spur in Roadmap, ADRs oder Code. Alles neu mit diesem Mandat. | 🆕 Komplett neu |

**Konsequenz:** Die im Mandat geforderten Säulen sind keine „Erweiterung der bestehenden KIDI", sondern **Erfindung der KIDI-Synthese-Engine zusammen mit 6 zusätzlichen, nicht-falsifizierbaren Heuristik-Schichten**.

---

## 2. Codebase-Inventar (verifiziert)

### Layer 0–1 — Infra & Host

- **docker-compose.yml:** 879 Zeilen, 27 aktive Service-Definitionen, 7 Profile (`agents`, `kidi`, `external-agents`, `voice-full`, `cpu`, `gpu`, `minimal`).
- **Bind-Policy:** Alle Services auf `${KIROBI_BIND_HOST:-127.0.0.1}`. Caddy = einziger LAN-Edge (`KIROBI_PROXY_BIND_HOST=0.0.0.0`).
- **Aktuell laufend (verifiziert mit `docker compose ps`):** 27 Container; nach heutigem Fix alle gesund (qdrant, hermes-runtime, openclaw-gateway).
- **install.sh:** idempotent, schreibt `.kirobi/install.json`. Profile-Layering via `COMPOSE_FILE`-Pinning.

### Layer 2 — Modelle

- **Ollama:** Container `kirobi-ollama` läuft, Port 11434 lokal. Kein Modell-Manifest im Repo; Modelle werden zur Laufzeit gepullt.
- **Whisper/Piper:** in `services/voice-processing/` (Port 8001). Healthy.
- **Embedding-Modelle:** `nomic-embed-text` (768 dim) für public/code, `bge-m3` (1024 dim) für workspace/family/canon/experiences (vgl. `metadata/COLLECTION-MAPPING.md`).

### Layer 3 — Speicher

- **Qdrant:** 8 Collections live (`kirobi_family_private_documents`, `kirobi_public_documents`, `kirobi_sacred_documents`, `kirobi_workspace_notes`, `kirobi_workspace_document`, `kirobi_workspace_research`, `kirobi_workspace_documents`, `kirobi_workspace_code`). Healthcheck heute gefixt (bash-TCP statt curl).
- **Postgres:** healthy, Schemas durch Auth+API beim Start gebootstrappt.
- **Filesystem als System of Record:** 5-Zonen-Struktur (`canon/`, `experiences/`, `extracts/`, `sacred/`, `quarantine/`).
- **ContextDB (`kidi/context_db/`):** SQLite-basiert (`store.py`), Zone-Guard (`zone_guard.py`), Key-Schema (`keys.py`). 4 Test-Dateien unter `tests/unit/kidi/context_db/`.

### Layer 4 — Wissen / Ingestion

- **ingest service** (Port 8007): Text + File-Upload, `ingest_jobs` table. Healthy.
- **embeddings** (Port 8004): `/embed`, `/embed/batch`, `/store`. Healthy.
- **retrieval** (Port 8006): `/search`, `/rag` mit harter SACRED→403-Sperre. Healthy.

### Layer 5 — Services

- 17 Service-Verzeichnisse unter `services/`. Hyphenated dirs (`image-generation` etc.) brauchen `_register_hyphenated_service` in `tests/conftest.py`.
- Alle Services binden auf `127.0.0.1` und exponieren via Caddy-Routing.

### Layer 6 — Agenten

| Kategorie | Verzeichnis | Status |
|---|---|---|
| Implementierte Agenten | `agents/{opencode,openclaw,hermes,obsidian}/agent.py` | 4 Stück, jeweils mit Dockerfile, smoke + zone_refusal Tests (52 Tests gesamt, 0.16s) |
| `agents/_base/agent.py` | Basisklasse | ✓ |
| Externe Tools (Phase 4.5) | `services/{hermes-runtime,openclaw-gateway}/`, host-side `aionui-cockpit` | Live, healthy |
| Im Registry-Dokumentiert, **kein Code** | `kirobi-core` (Supervisor), `kirobi-architect`, `kirobi-coder`, `kirobi-ops`, `kirobi-observer`, `samira-heart`, `sineo-creator`, `research-crew`, `mediation-crew`, `creative-agent`, `voice-agent`, `installer-agent`, `enterprise-agent` | **0 Module, 0 Tests** |

### Layer 7 — Erfahrung

- **apps/web** (PWA, Port 3002): vollständig.
- **apps/dashboard** (Port 3003): vollständig.
- **apps/voice** (Port 3004): vollständig.
- **apps/{desktop,mobile,installer}**: Scaffolds, eingefroren (vgl. `.github/copilot-instructions.md` „Frozen / Deprioritized").

### Tests

- `tests/unit/`: 48 Testdateien, **535 passed, 27 skipped** (heute verifiziert mit `make integration-test`).
- Keine E2E- oder Property-Based-Tests.

---

## 3. Roadmap-Status (aus `keycodi/MILESTONES.md`)

```
Phase 0: 🟡 IN PROGRESS  — 15/16, Sven-Sign-off ausstehend
Phase 1: 🟢 DONE  (ContextDB)
Phase 2: 🟢 DONE  (4 Agent-Skeletons)
Phase 3: 🟢 DONE  (Obsidian-Vault, 6/7 Items)
Phase 4: ⚪ PENDING  — KIDI-Engine + KEYBRODI komplett offen
Phase 4.5: 🟡 IN PROGRESS  — heute Code/Docs done; Live-Smoke+Pin offen
Phase 5: ⚪ PENDING (Telegram, gated)
Phase 6: ⚪ PENDING (install.sh polish)
```

**Phase 4 = Critical Path.** Vor Säulen-Diskussion müssen mindestens existieren:
- `kidi/core/collective_intelligence.py` (Confidence-Weighted-Merge gemäß `KIDI-ENGINE.md` §3)
- `kidi/keybrodi/orchestrator.py` + `routing_table.py`
- Tests `test_synthesis.py`, `test_routing.py`, `test_zone_preservation.py`, `test_metrics.py`

---

## 4. Bewertung der 6 vorgeschlagenen Säulen

### Säule 1 — AQAL-Engine (Wilber: 4 Quadranten + Stufen)

- **Charakter:** Strukturierungs-Heuristik. Falsifizierbar im Sinn „macht der Output konsistent Sinn?", nicht im physikalischen Sinn.
- **Repo-Fit:** Mappt sauber auf Agent-Routing (Quadranten = Perspektiven). Risiko-frei wenn als **Tagging-Layer**, nicht als Pflicht-Filter.
- **Empfehlung:** Geeignet als optionales Routing-Hint nach Phase-4-Kern, NICHT als Voraussetzung für die Synthese.

### Säule 2 — Spiral Dynamics

- **Charakter:** Wertesystem-Modell, in Coaching/Org-Entwicklung etabliert, in Kognitionswissenschaft umstritten.
- **Repo-Fit:** Als „Tonalitäts-Tag" für Outputs nützlich. Als „Routing-Faktor mit Confidence-Gewicht" problematisch — kein objektiver Messwert.
- **Empfehlung:** Optional, nur in `kidi/experimental/`.

### Säule 3 — Phi-Harmonics (Φ-Gewichtung)

- **Charakter:** Mathematisch präzise (Φ = 1.618…), aber als „natürlichere" Gewichtung im Confidence-Merge ist das **eine ästhetische Wahl ohne Beweis besserer Outputs**.
- **Repo-Fit:** Harmlos für UI-Proportionen. Im Synthese-Algorithmus = Risiko, technische Entscheidungen mit pseudo-objektiven Konstanten zu legitimieren.
- **Empfehlung:** **NICHT** in den Synthese-Merge. UI-Proportionen ja.

### Säule 4 — „Quantum Resonance"

- **Charakter:** Begriff „Quantum" wird hier metaphorisch verwendet. Im physikalischen Sinn nicht zutreffend (keine Verschränkung, keine Superposition in klassischer Software).
- **Repo-Fit:** Ein „Kohärenz-Score" über Agent-Outputs ist als **Konsistenz-Metrik** legitim — aber dann sollte er auch so heißen (z.B. `coherence_metrics.py`), nicht „Quantum Resonance".
- **Empfehlung:** Umbenennen, scope-reduzieren auf semantische Konsistenz-Checks.

### Säule 5 — Numerologische Resonanz (Grabovoi-inspiriert)

- **Charakter:** Numerologie ist nicht falsifizierbar; Grabovoi-Codes wurden in Russland mehrfach mit Heilungsversprechen vermarktet (Kontext: Strafverfahren wegen Betrugs).
- **Repo-Fit:** **Hohes Reputations- und Haftungsrisiko** wenn in einem System für Familie + Business läuft. Selbst opt-in birgt Risiko, weil das System Codes „aktiviert".
- **Empfehlung:** **Stark überdenken.** Falls überhaupt, nur als reines Datenfeld (`metadata/intentions.yaml`) ohne aktive Wirkung im Merge, mit explizitem Disclaimer in jeder Antwort.

### Säule 6 — Samira-Heart-Agent Upgrade

- **Charakter:** Der Agent existiert noch nicht als Code. „Upgrade" bedeutet: zuerst bauen, dann erweitern.
- **Repo-Fit:** Sinnvoll als emotionaler Bewerter (Tonalitäts-Hint, Konflikt-Detection) auf WORKSPACE/FAMILY_PRIVATE-Daten — letzteres nur lokal mit Ollama.
- **Empfehlung:** **Erst Basis-Samira als Phase-4.6 bauen** (analog zu existierenden Agent-Skeletons), dann emotionale Module.

---

## 5. Technische Schulden / TODOs

- `Makefile` definiert `status` zweimal (siehe `AGENTS.md` „Known Gotchas").
- `agents/openclaw/` (interner Phase-2-Agent) und `services/openclaw-gateway/` (Phase-4.5-Bridge) tragen ähnliche Namen — Verwechslungsgefahr in Doku.
- KEYBRODI-Routing-Tabelle aus ADR-0004 (Hermes/OpenClaw/AionUi-Eintrag) ist vorbereitet, aber `kidi/keybrodi/routing_table.py` existiert nicht.
- `make status` läuft Python-Variante (zweite Definition überschreibt Docker-Variante). Original-Health-Check nur via `bash infra/scripts/healthcheck.sh`.
- 27 skipped Tests — Grund: optionale FastAPI-Stack-Deps; in `.venv` würden sie laufen, aber CI baseline ist stdlib-only.

---

## 6. Heute durchgeführte Fixes (Sven-Bug-Report)

| Symptom | Ursache | Fix | Verifikation |
|---|---|---|---|
| `kirobi-qdrant` `(unhealthy)` | Healthcheck nutzt `curl`, das im distroless qdrant-Image fehlt | `docker-compose.yml` Healthcheck → bash `/dev/tcp` Probe | `docker ps` → `(healthy)` ✓ |
| `kirobi-hermes-runtime` Restart-Loop | Dashboard refused 0.0.0.0 ohne `--insecure` | Command erweitert um `--insecure` (im Docker-Bridge-Net + 127.0.0.1-Bind sicher) | `curl :9119/` → HTTP 200 ✓ |
| `kirobi-openclaw-gateway` 78 Restarts | Gateway erwartet `openclaw setup` oder `--allow-unconfigured` | Command erweitert um `--allow-unconfigured` | `curl :18789/healthz` → HTTP 200, `(healthy)` ✓ |
| Behauptung „Qdrant/Flowise nicht zugänglich" | Beide Services WAREN erreichbar (HTTP 200 direkt + via Caddy); nur Healthcheck-Status irreführend | s.o. | `curl /qdrant/collections` → 8 Collections JSON ✓ |

`make integration-test` nach Fixes: **green**.

---

## 7. Empfohlener nächster Schritt (zur Diskussion mit Sven)

**Reihenfolge mit minimalem Risiko und maximalem Erkenntnisgewinn:**

1. **Phase 4 Kern bauen** — `kidi/core/collective_intelligence.py` mit dem konservativen Algorithmus aus `KIDI-ENGINE.md` §3 (zone-preserving, sources-citing, conflict-flagging). KEINE esoterischen Säulen im Merge.
2. **KEYBRODI Static Routing** — `kidi/keybrodi/orchestrator.py` + `routing_table.py` aus `AGENT-DECISION-MATRIX.md` als statische Tabelle generieren.
3. **Metriken** — `kirobi-core/core-events.log` Schreiber für `KIDI_SYNTHESIS`, `KIDI_ZONE_DOWNGRADE`, `KEYBRODI_ROUTE`.
4. **Phase-4-Gate schließen** — Tests grün, ADR `0005-kidi-phase4-implementation.md`.
5. **DANN** entscheiden: Welche der 6 Säulen ziehen wir als opt-in `kidi/experimental/`-Module nach? Mit klarer Trennung „Heuristik-Layer ≠ Synthese-Kern".

**Zu vermeiden:**
- Phi-Harmonics oder numerologische Codes als Pflicht-Faktoren im Merge → verletzt Falsifizierbarkeit, riskiert Haftung bei Familien-Nutzung.
- „Multi-Dimensional Confidence-Weighted Merge" mit 6 Faktoren BEVOR der einfache 1-Faktor-Merge existiert und stabil läuft.
- Samira-Upgrade BEVOR Basis-Samira als Skeleton existiert.

---

## 8. Status & Empfehlung

- **Phase-1-Analyse: ABGESCHLOSSEN.**
- **Phase-4.5-Bug-Fix:** Qdrant-Healthcheck + Hermes/OpenClaw-Restart-Loops behoben.
- **Phase-4-Säulen-Implementierung:** Wartet auf Sven-Entscheidung über Reihenfolge und Scope der esoterischen Schichten.

**Konkrete Frage an Sven (für nächste Runde):**
> Sollen wir Phase 4 (Kern-KIDI-Synthese ohne Säulen) zuerst sauber abschließen, und die 6 Säulen danach als opt-in-Module unter `kidi/experimental/` evaluieren — oder hast du einen anderen Plan?
