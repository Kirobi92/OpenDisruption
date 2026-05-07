# KeyCodi — Backlog Workflow

**Zone:** WORKSPACE
**Letzte Aktualisierung:** 2026-05-07

Der Backlog wird **als GitHub-Issues** geführt. KeyCodi konsumiert ihn in fester Ordnung. Issue-Templates liegen in `.github/ISSUE_TEMPLATE/`.

---

## 1. Issue-Typen

| Template                  | Wofür                                                  | Default-Labels                       |
|---------------------------|--------------------------------------------------------|--------------------------------------|
| `keycodi-task.yml`        | Geplante Roadmap-Aufgabe (1 Item aus `MILESTONES.md`)  | `keycodi`, `phase-N`, `task`         |
| `keycodi-bug.yml`         | Regression / kaputtes Verhalten                        | `keycodi`, `bug`                     |
| `keycodi-learning.yml`    | Erkenntnis / Reibung, die in `learnings/` gespiegelt wird | `keycodi`, `learning`             |

---

## 2. Labels

KeyCodi nutzt ausschließlich diese Labels (und keine anderen für Roadmap-Arbeit):

| Label                  | Bedeutung                                                                |
|------------------------|--------------------------------------------------------------------------|
| `keycodi`              | Vom KeyCodi-Workflow erfasst.                                            |
| `keycodi:next`         | Nächstes Item, das KeyCodi ziehen darf. **Genau eins pro Phase aktiv.**  |
| `keycodi:in-progress`  | Wird gerade bearbeitet.                                                  |
| `keycodi:blocked`      | Blocker — Hinweis auf Issue/Doku im Body.                                |
| `keycodi:halted`       | Stop-Bedingung aus `OPERATING-RULES.md` §7 ausgelöst.                    |
| `keycodi:approved`     | Sven hat ein Item / einen Plan abgenickt.                                |
| `phase-0` … `phase-6`  | Phasen-Zugehörigkeit.                                                    |
| `task` / `bug` / `learning` | Issue-Art.                                                          |
| `zone:public` / `zone:workspace` | Auf welche Zone das Item wirkt.                                |

Andere Repo-Labels bleiben unberührt.

---

## 3. Reihenfolge-Garantie

- **Genau ein** Issue trägt zu jedem Zeitpunkt das Label `keycodi:next`.
- KeyCodi zieht ausschließlich dieses Issue.
- Nach dem Schließen vergibt KeyCodi `keycodi:next` an das nächste, in `MILESTONES.md` an erster offener Stelle stehende Item.
- Wird ein Issue blockiert, bleibt `keycodi:next` an dem Issue, bis der Block gelöst ist (KeyCodi zieht **nicht** stattdessen das übernächste Item).

---

## 4. Akzeptanz-Definition (Definition of Done)

Ein Issue ist nur dann schließbar, wenn der schließende Commit / PR enthält:

1. Code- oder Doku-Änderung, die das Issue löst.
2. Mindestens einen automatisierten Test (Refusal- und Happy-Path).
3. Aktualisierten Eintrag in `keycodi/MILESTONES.md`.
4. Optional: Eintrag in `learnings/` oder `decisions/`, wenn Reibung / Architekturwahl.
5. Keine geänderten Dateien in Zonen oberhalb WORKSPACE.

---

## 5. Initial-Backlog (KeyCodi legt diese Issues an, sobald Phase 0 abgenickt ist)

> Diese Liste ist die **Vorlage**. KeyCodi erstellt für jeden Bullet-Punkt in `MILESTONES.md` (Phasen 1–6) ein Issue, sobald die Vorgängerphase als `🟢 done` gilt. Vorher: keine Issue-Spam.

Beispiel-Mapping:

| Milestone-Eintrag                                  | Issue-Titel-Vorlage                          |
|----------------------------------------------------|----------------------------------------------|
| `kidi/context_db/client.py`                        | `[phase-1] ContextDB: client.py implementieren` |
| `tests/unit/kidi/context_db/test_zone_enforcement.py` | `[phase-1] ContextDB: Zonen-Enforcement-Tests` |
| `agents/_base/agent.py`                            | `[phase-2] Agent-Basisklasse implementieren` |
| `agents/obsidian/agent.py` Vault-CRUD              | `[phase-3] Obsidian-Agent: Vault-CRUD`       |
| `kidi/keybrodi/orchestrator.py`                    | `[phase-4] KEYBRODI: Orchestrator-Skelett`   |
| `agents/_telegram/zone_filter.py`                  | `[phase-5] Telegram: Zone-Filter (gated)`    |
| `install.sh` mit `--dry-run`-Default               | `[phase-6] install.sh repo-lokal`            |

---

## 6. Bezug zu ContextDB-Issues (ab Phase 1)

Sobald Phase 1 abgeschlossen ist, schreibt KeyCodi vor jeder Issue-Bearbeitung einen ContextDB-Eintrag:

```
ctx:WORKSPACE:keycodi:<uuid> = {
  task_id:    "issue-NNN",
  phase:      N,
  start_time: "...",
  status:     "in-progress"
}
```

und schließt ihn nach Abschluss mit `status: "done" | "blocked" | "halted"`. Vor Phase 1 entfällt das (kein ContextDB).

---

## 7. Anti-Spam-Regeln

- KeyCodi erstellt **kein** Issue, das bereits existiert (Duplicate-Check über Titel-Hash).
- KeyCodi erstellt **kein** Issue mit Label `keycodi:next`, wenn schon eines aktiv ist.
- KeyCodi öffnet **keine** PRs ohne zugehöriges Issue.
