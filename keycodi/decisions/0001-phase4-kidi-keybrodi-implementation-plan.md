---
zone: WORKSPACE
created_by: kirobi-architect
created_at: 2026-05-08
reviewed_by: pending
version: 1.0
---

# ADR 0001 — Phase 4: KIDI-Engine + KEYBRODI-Orchestrator — Implementierungsplan & Agent-Koordination

**Datum:** 2026-05-08
**Status:** accepted
**Phase:** 4
**Issue / PR:** pending
**Sven-Sign-off:** required

---

## Kontext

### Wo stehen wir?

Nach Analyse aller laufenden Sessions, des Backlogs und des aktuellen Repo-Zustands ergibt sich folgendes Bild:

| Phase | Status | Offene Punkte |
|-------|--------|---------------|
| Phase 0 | 🟡 15/16 — Sven-Sign-off ausstehend | Sven muss Architektur formal abnicken |
| Phase 1 | 🟢 DONE | CI-Merge ausstehend |
| Phase 2 | 🟢 DONE | CI-Merge ausstehend |
| Phase 3 | 🟢 DONE | CI-Merge ausstehend; `obsidian/agents/*/00-Index.md` MOCs generiert |
| Phase 4 | ⚪ PENDING | **Alle 6 Deliverables offen** — das ist der kritische Pfad |
| Phase 5 | ⚪ GATED | Wartet auf Phase 4 + Docker Secrets |
| Phase 6 | ⚪ PENDING | Wartet auf Phase 5 |

**Test-Baseline:** 477 passed, 27 skipped (Stand 2026-05-08) — stabil.

**Apps-Status:**
- `apps/desktop/` (Tauri + React/Vite) — Scaffold only, kein Runtime-Code
- `apps/mobile/` (Expo + React Native) — Scaffold only, kein Runtime-Code
- `apps/web/`, `apps/dashboard/`, `apps/voice/` — vollständig, produktiv

### Das Problem

Phase 4 ist der einzige verbleibende Blocker für den gesamten KEYBRODI-Handoff. Ohne `kidi/keybrodi/orchestrator.py` und `kidi/core/collective_intelligence.py` kann kein deterministisches Routing stattfinden, kein Metrik-Loop laufen, und die Handoff-Kriterien aus `HANDOFF-TO-KEYBRODI.md` können nicht erfüllt werden.

Gleichzeitig existieren zwei App-Scaffolds (`desktop`, `mobile`), die bisher keine Implementierung haben und in keiner Phase explizit adressiert sind.

**Constraints:**
- Dateisystem ist System of Record — Postgres/Qdrant sind abgeleitete Indizes
- Zone-Modell ist absolut: SACRED > FAMILY_PRIVATE > QUARANTINE > WORKSPACE > PUBLIC
- Alle Services müssen idempotent und rebuildfähig sein
- `kirobi-core/core-events.log` ist append-only — kein Rewrite
- Phase 5 bleibt gated bis Phase 4 vollständig grün ist

---

## Optionen

### Option A — Sequenziell: Phase 4 vollständig vor allem anderen

Alle Ressourcen auf Phase 4 konzentrieren. Erst wenn `kidi/keybrodi/` und `kidi/core/` grün sind, werden Desktop/Mobile und Phase 5/6 angegangen.

- **Pro:** Maximale Fokussierung; KEYBRODI-Handoff-Kriterien werden schnellstmöglich erfüllt; kein Kontext-Switch
- **Pro:** Entspricht der Reihenfolge-Garantie aus `ROADMAP.md` (strikt linear)
- **Contra:** Desktop/Mobile-Scaffolds bleiben länger unberührt
- **Risiko:** Niedrig — Phase 4 ist klar spezifiziert in `KIDI-ENGINE.md` und `KEYBRODI-SUPERINTELLIGENZ.md`

### Option B — Parallel: Phase 4 + Desktop/Mobile gleichzeitig

kirobi-coder implementiert Phase 4; kirobi-frontend baut Desktop/Mobile-Grundgerüst parallel.

- **Pro:** Schnellerer Gesamtfortschritt auf dem Papier
- **Contra:** Erhöhter Koordinationsaufwand; Desktop/Mobile haben keine Phase-Abhängigkeit und keinen definierten Scope
- **Contra:** Desktop/Mobile-Scope ist unklar (kein Runbook, kein ADR, kein Milestone-Eintrag)
- **Risiko:** Mittel — parallele Arbeit ohne klare Spec führt zu Rework

### Option C — Phase 4 + CI-Cleanup zuerst, dann Rest

Vor Phase 4 werden die ausstehenden CI-Merges für Phasen 1–3 sauber abgeschlossen, dann Phase 4 implementiert, dann Desktop/Mobile als Phase 7 (neu) geplant.

- **Pro:** Saubere Git-History; CI-Baseline ist klar; keine technischen Schulden
- **Pro:** Desktop/Mobile bekommen einen eigenen Milestone mit Spec — kein Blindflug
- **Contra:** Leicht mehr Vorlaufzeit durch CI-Cleanup
- **Risiko:** Niedrig — CI-Cleanup ist mechanisch, nicht kreativ

---

## Entscheidung

**Option C — Phase 4 + CI-Cleanup zuerst, dann Desktop/Mobile als Phase 7.**

Begründung: Die Reihenfolge-Garantie aus `ROADMAP.md` ist nicht verhandelbar. Phase 4 ist der kritische Pfad zum KEYBRODI-Handoff. Gleichzeitig haben die ausstehenden CI-Merges für Phasen 1–3 keine technischen Blocker — sie sind reine Hygiene und sollten vor Phase 4 abgeschlossen werden, damit die Test-Baseline sauber ist. Desktop und Mobile erhalten einen eigenen Milestone (Phase 7) mit klarer Spec, bevor Code geschrieben wird — das entspricht dem Prinzip „Architektur vor Implementierung" aus Phase 0.

---

## Konsequenzen

### Positive Auswirkungen

- KEYBRODI-Handoff-Kriterien werden auf dem direktesten Weg erfüllt
- CI-Baseline bleibt sauber und nachvollziehbar
- Desktop/Mobile bekommen eine echte Spec statt Blindflug-Implementierung
- Metrik-Loop in `kirobi-core/core-events.log` wird aktiviert — Observability steigt
- Zone-Enforcement wird durch Phase 4 Tests vollständig abgedeckt

### Negative Auswirkungen / Risiken

- Desktop/Mobile-Implementierung verzögert sich um ~Phase 4 Dauer (geschätzt 1–2 Sessions)
- Phase 5 (Telegram) bleibt gated — kein Telegram-Bot bis Phase 4 grün
- Sven-Sign-off für Phase 0 ist noch ausstehend — ohne diesen ist Phase 4 formal nicht freigegeben

### Offene Fragen

1. **Sven-Sign-off Phase 0:** Muss formal erfolgen (Issue-Kommentar oder Label `keycodi:approved`) bevor Phase 4 startet
2. **Desktop/Mobile Scope:** Was soll `apps/desktop/` können? Tauri-Shell um die PWA? Native Features? → Spec für Phase 7 nötig
3. **Docker Secrets für Phase 5:** Sind `KIROBI_TELEGRAM_TOKEN_FILE` etc. lokal vorhanden?
4. **Default Vault-Pfad (Phase 3 Hard-Blocker):** `obsidian/` in-Repo vs. `~/kidi-vault/` — Sven entscheidet

---

## Implementierungs-Plan

### Sofort (vor Phase 4): CI-Cleanup

**kirobi-ops:**
- [ ] PR für Phase 1 (Redis ContextDB) mergen → CI grün bestätigen
- [ ] PR für Phase 2 (Agenten-Skelette) mergen → CI grün bestätigen
- [ ] PR für Phase 3 (Obsidian-Vault) mergen → CI grün bestätigen
- [ ] `MILESTONES.md` CI-Checkboxen abhaken

---

### Phase 4 — KIDI-Engine + KEYBRODI-Orchestrator

#### kirobi-coder: `kidi/core/collective_intelligence.py`

```
Datei: kidi/core/collective_intelligence.py
Spec:  docs/agent/KIDI-ENGINE.md §3

Exports:
  - synthesize(inputs: list[AgentOutput]) -> SynthesisResult
  - SynthesisResult(output: str, sources: list[str], confidence: float, zone: Zone)

Regeln:
  - Konfidenz-gewichtete Synthese (Gewichte aus AgentOutput.confidence)
  - Zonen-Preservation: Output-Zone = max(input zones) — niemals downgrade
  - Konflikt-Detektion: wenn zwei Inputs widersprechen → ConflictError mit beiden Quellen
  - Metrik-Schreiber: jede Synthese → append zu kirobi-core/core-events.log
    Format: [TIMESTAMP] [kidi] SYNTHESIZE zone=X inputs=N confidence=0.NN
```

#### kirobi-coder: `kidi/keybrodi/orchestrator.py` + `routing_table.py`

```
Dateien:
  kidi/keybrodi/__init__.py
  kidi/keybrodi/orchestrator.py
  kidi/keybrodi/routing_table.py

Spec: docs/agent/KEYBRODI-SUPERINTELLIGENZ.md + AGENT-DECISION-MATRIX.md

Exports (orchestrator.py):
  - route(task: Task) -> RoutingDecision
  - RoutingDecision(agent: str, requires_human_approval: bool, zone: Zone, reason: str)

Regeln:
  - Routing-Tabelle aus AGENT-DECISION-MATRIX.md als statische Datenstruktur (routing_table.py)
  - Zonen-Eskalation → ZoneEscalationError (kein Routing)
  - requires_human_approval=True → DEFER mit Notification-Eintrag im Event-Log
  - Jede Routing-Entscheidung → append zu kirobi-core/core-events.log
    Format: [TIMESTAMP] [keybrodi] ROUTE task=X agent=Y zone=Z
  - Jede Ablehnung → REJECT-Eintrag mit Reason-Code
```

#### kirobi-coder: Tests

```
tests/unit/kidi/
  test_synthesis.py          — Happy-Path, Konflikt-Detektion, Zonen-Preservation
  test_routing.py            — alle Matrix-Einträge, Zonen-Eskalation, DEFER-Pfad
  test_zone_preservation.py  — merge + synthesize dürfen Zone nie downgraden
  test_metrics.py            — Event-Log-Einträge werden geschrieben (mock file)

Mindest-Coverage: alle Kombinationen aus ZONE-POLICY-MATRIX.md
Baseline nach Phase 4: >500 Tests
```

#### kirobi-ops: Compose + Makefile

```
docker-compose.yml:
  - kidi-Service unter Profile `kidi` (falls Runtime nötig)
  - Healthcheck für kidi/serve.py (existiert bereits)

Makefile:
  - make test-kidi-phase4   → pytest tests/unit/kidi/ -q
  - make keybrodi-route TASK='...'  → headless Routing-Test
```

#### kirobi-architect: ADRs für KEYBRODI (Handoff-Kriterium 1.5)

```
keycodi/decisions/
  0002-kidi-synthesis-algorithm.md    — Konfidenz-Gewichtung, Konflikt-Strategie
  0003-keybrodi-routing-table-format.md — statisch vs. dynamisch, Datenstruktur
  (dieses ADR zählt als erstes der drei geforderten)
```

---

### Phase 7 (neu): Desktop + Mobile Apps

**Voraussetzung:** Phase 4–6 abgeschlossen, Sven-Spec vorhanden

**kirobi-architect** (nächste Session nach Phase 6):
- [ ] ADR für Desktop-App-Scope (Tauri-Shell vs. native Features)
- [ ] ADR für Mobile-App-Scope (Expo PWA-Wrapper vs. native)
- [ ] Milestone-Einträge in `MILESTONES.md` Phase 7

**kirobi-frontend** (nach ADR-Sign-off):
- [ ] `apps/desktop/` — Tauri-Shell mit eingebetteter PWA (`apps/web/`)
- [ ] `apps/mobile/` — Expo-App mit Chat + Voice-Interface
- [ ] Shared Component Library zwischen web/desktop/mobile evaluieren

---

## Referenzen

- `keycodi/ROADMAP.md` — Phasen-Reihenfolge
- `keycodi/MILESTONES.md` — Tracking-Liste
- `keycodi/HANDOFF-TO-KEYBRODI.md` — Handoff-Kriterien
- `docs/agent/KIDI-ENGINE.md` — KIDI-Synthese-Spec
- `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md` — KEYBRODI-Routing-Spec
- `AGENT-DECISION-MATRIX.md` — Routing-Tabelle (Quelle der Wahrheit)
- `CLAUDE.md` §3, §5, §12 — Prohibitions, Agent-Permissions, Logging
- `metadata/ZONE-POLICY-MATRIX.md` — Zone-Kombinationen
- `kirobi-core/core-events.log` — Append-only Audit-Log
