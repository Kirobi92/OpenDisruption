# Runbook — Phase 4: KIDI-Engine + KEYBRODI-Orchestrator

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/KIDI-ENGINE.md`, `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`
**Milestones:** `keycodi/MILESTONES.md` § Phase 4

---

## Vorbedingungen

- Phase 3 ist `🟢 done`. Vault-CRUD + Qdrant-Bridge laufen.

## Schritte

### 1. KIDI-Engine

Datei: `kidi/core/collective_intelligence.py`

API exakt wie in `docs/agent/KIDI-ENGINE.md` §§3–4.

- `synthesize(entries: list[ContextEntry], output_zone: Zone) -> SynthesisEntry`
- Refusal: `output_zone > min(input zones)` → `ZoneViolation`.
- Konflikt-Erkennung: identische `task_id`, widersprüchliche Felder → `conflicts[]` im Output.
- Quellen-Liste: `sources` enthält die Input-Keys.

Tests:
- `test_synthesis.py` (Konfidenz-Gewichtung, Quellen)
- `test_zone_preservation.py` (Reject bei Eskalation)
- `test_conflict_detection.py`

### 2. KEYBRODI-Orchestrator

Datei: `kidi/keybrodi/orchestrator.py`

API: `route(task: Task) -> RoutingDecision`.

- Routing-Tabelle: `kidi/keybrodi/routing_table.py` als statische `dict`/`dataclass`-Struktur, **handgepflegt** aus `AGENT-DECISION-MATRIX.md`. Keine Laufzeit-Mutation.
- Validierungs-Algorithmus exakt wie in `AGENT-DECISION-MATRIX.md` §4.
- Reject + Defer-Pfade durch Tests belegt.

### 3. Metrik-Schreiber

- Jede Routing-Entscheidung → Eintrag in `kirobi-core/core-events.log` im Format aus `KEYBRODI-SUPERINTELLIGENZ.md` §3.
- Jede Synthese → `SYNTHESIZE`-Eintrag.
- Jede Ablehnung → `REJECT`-Eintrag mit Reason-Code.
- Format: ein einzelner stringifizierter Eintrag pro Zeile, append-only.

### 4. Tests

- `test_routing.py` — pro Task-Typ aus der Matrix mind. ein Test.
- `test_routing_zone_reject.py`
- `test_routing_defer_human_approval.py`
- `test_metrics_logging.py` — Log-Format verifizieren.

### 5. Make-Targets

- `make test-kidi-core`
- `make test-keybrodi`

### 6. Mini-CLI

`python -m kidi.keybrodi route --task '<json>'` druckt die `RoutingDecision`. Nützlich für Debug + Demos.

### 7. Handoff-Bereitschafts-Check

Am Ende dieser Phase prüft KeyCodi alle Items in `keycodi/HANDOFF-TO-KEYBRODI.md` §1 und füllt Belege.

## Definition of Done

KIDI synthetisiert zwei Inputs zu einem Output. KEYBRODI routet alle Matrix-Tasks korrekt. Zonen-Eskalation wird abgelehnt. CI grün. Mindestens 7-Tage-Live-Metriken sind aufgezeichnet, bevor der Handoff initiiert wird.

## Mögliche Stolpersteine

- KIDI versucht ein neues Qdrant-Collection anzulegen (verboten).
- KEYBRODI wechselt Routing-Tabelle dynamisch (verboten).
- Metrik-Log wächst unbegrenzt — Rotation in `infra/scripts/` ergänzen.

## Übergang

Nach `🟢 done` und 7 Tagen Live-Metriken: `runbooks/phase-5-telegram.md` (nur wenn Sven Option A wählt) oder `runbooks/phase-6-installer.md`.

Außerdem: Handoff-PR gemäß `keycodi/HANDOFF-TO-KEYBRODI.md` initiieren.
