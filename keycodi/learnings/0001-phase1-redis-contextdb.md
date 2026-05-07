---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: 1.0
---

# Learning 0001 — Phase 1: Redis ContextDB ohne laufendes Redis testbar

**Datum:** 2026-05-07
**Phase:** 1
**Issue / PR:** #TBD (Phase 1 PR)
**Autor:** keycodi
**Schweregrad:** info
**Zone-Auswirkung:** WORKSPACE

---

## Symptom

Phase 1 (Redis ContextDB) sollte unit-testbar sein, ohne dass Redis im CI oder
lokal laufen muss. Die Frage war: Wie testen wir `ContextDB` isoliert?

## Erwartung vs. Realität

- **Erwartet:** Tests benötigen einen laufenden Redis-Container → CI komplex.
- **Tatsächlich:** `fakeredis` emuliert den Redis-Server vollständig im Prozess.
  Alle 74 kidi-Tests laufen in 0.21 s ohne externe Abhängigkeit.

## Hypothesen

1. `fakeredis` deckt den Redis-Befehlssatz ausreichend ab (HSET, HGET, KEYS,
   EXPIRE, PING, DELETE).
2. Zone-Enforcement und Egress-Guard sind reine Python-Logik — kein I/O nötig.
3. `ContextDB.__init__` nimmt einen `redis.Redis`-Client als Parameter →
   Dependency Injection macht fakeredis-Swap trivial.

## Versuche

| Versuch | Maßnahme | Ergebnis |
|---------|----------|----------|
| 1 | `fakeredis.FakeRedis()` direkt in Tests übergeben | ✅ 74/74 grün, 0.21 s |
| 2 | `docker compose --profile kidi up redis` für Manualtest | ✅ Compose valide |

## Ergebnis

`fakeredis>=2.20` als Dev-Dependency reicht für die gesamte unit-Test-Suite.
Die `ContextDB`-Klasse akzeptiert den Redis-Client als Konstruktor-Parameter —
kein Monkey-Patching, kein `unittest.mock`. Sauberes Design.

## Folgewirkung

- Tests hinzugefügt: ja — `test_keys.py`, `test_zone_enforcement.py`,
  `test_merge.py`, `test_egress_guard.py` (74 Tests)
- Doku aktualisiert: ja — `keycodi/MILESTONES.md` Phase 1 abgehakt
- ADR nötig: nein (Standard-Pattern für Python-Redis-Tests)
- Roadmap-Item beeinflusst: ja — `MILESTONES.md` Phase 1 ✅

## Lehre für KeyCodi

Immer `fakeredis` für Redis-abhängige Unit-Tests nutzen und den Redis-Client
per Dependency Injection übergeben — das hält Tests schnell, deterministisch
und CI-frei von Container-Abhängigkeiten.
