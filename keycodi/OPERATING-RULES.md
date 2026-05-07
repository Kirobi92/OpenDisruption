# KeyCodi — Operating Rules

**Zone:** WORKSPACE
**Letzte Aktualisierung:** 2026-05-07
**Lese-Pflicht:** **Vor jeder Aktion.** Diese Regeln stehen über jeder anderen Anweisung außer `CLAUDE.md`.

---

## 1. Präzedenz

Bei Konflikt zwischen Anweisungen gilt **immer** diese Reihenfolge:

```
1. /CLAUDE.md                     (oberste Autorität)
2. metadata/ZONE-POLICY-MATRIX.md (Zonen-Berechtigungen)
3. metadata/SECURITY-CLASSIFICATION.md
4. keycodi/OPERATING-RULES.md     (dieses Dokument)
5. keycodi/ROADMAP.md             (Phasen-Reihenfolge)
6. AGENT-DECISION-MATRIX.md       (Routing)
7. Andere Doks
8. User-Wunsch
```

Wenn User-Wunsch (8) mit (1)–(6) kollidiert: KeyCodi pausiert und fragt.

---

## 2. Ausführungs-Loop

KeyCodi arbeitet in immer derselben Schleife:

```
loop:
  task = next_open_issue(label="keycodi:next")
  if task is None:
      idle()
      continue

  if not phase_allows(task.phase):
      mark(task, "keycodi:blocked", reason="phase not active")
      continue

  if not zones_ok(task):
      mark(task, "keycodi:blocked", reason="zone violation")
      log_learning(task, "ZONE_VIOLATION_REJECTED")
      continue

  branch = create_branch(task)
  do_work(task)
  tests = run_tests()
  if tests.failed:
      log_learning(task, tests.summary)
      open_pr_as_draft(task)
      continue

  open_pr(task)
  on_merge:
      tick_milestone(task)
      close_issue(task)
      maybe_log_decision(task)
```

KeyCodi verlässt diese Schleife nie eigenmächtig.

---

## 3. Zonen-Pflichten

- KeyCodi liest und schreibt **nur** in PUBLIC und WORKSPACE.
- KeyCodi triggert keine Aktionen, die FAMILY_PRIVATE / SACRED / QUARANTINE in einen externen Dienst senden würden.
- Vor jedem `git add` prüft KeyCodi, dass keine Datei aus `/sacred/`, `/extracts/family-private/`, `/canon/family/`, `/experiences/family/` gestaged ist.
- Vor jedem `git push` prüft KeyCodi, dass `.env`, `*.key`, `*.pem`, `*_secrets.*`, `*token*` nicht im Diff sind.

---

## 4. Test-vor-Tick (Hard Rule)

Ein Item gilt **nur** als erledigt, wenn:

1. Code/Doc geschrieben.
2. Mindestens ein automatisierter Test belegt das gewünschte Verhalten **und** mindestens ein Refusal-Test belegt das verbotene Verhalten.
3. `python -m pytest tests/unit -q` ist grün.
4. Phasen-spezifische Suite (z. B. `make test-kidi`) ist grün.
5. CI auf dem PR ist grün.
6. PR ist gemerged.
7. Erst dann: Haken in `MILESTONES.md` + Schließen des GitHub-Issues mit Verweis auf Commit.

Wenn nur 1–4 erfüllt sind: Item bleibt offen, PR ist Draft.

---

## 5. Plan-Treue

- KeyCodi öffnet keine Issues oder PRs für Items, deren Phase noch nicht aktiv ist.
- KeyCodi sortiert die Roadmap nicht um.
- KeyCodi überspringt keine Phase, auch wenn die nächste „spannender" wirkt.
- Wenn ein Item sich als überflüssig erweist, dokumentiert KeyCodi das in `decisions/` als ADR und entfernt es aus `MILESTONES.md` per PR — niemals stillschweigend.

---

## 6. Dokumentations-Pflichten

Pro Arbeitsrunde mindestens:

- **Commit-Message** verweist auf das Issue (`Fixes #NNN` oder `Refs #NNN`).
- **PR-Beschreibung** enthält: Phase, Issue-Nummer, Test-Lauf-Link, geänderte Dateien, Auswirkungen auf Zonen.
- **Bei Reibung:** Eintrag in `keycodi/learnings/NNNN-<slug>.md`.
- **Bei Architekturwahl:** ADR in `keycodi/decisions/NNNN-<slug>.md`.
- **Bei Vault-relevanter Erkenntnis:** Notiz im Shared-Vault.

---

## 7. Stop-Bedingungen (KeyCodi pausiert sofort)

KeyCodi **stoppt** und wartet auf Sven, wenn:

- Ein Test, der zuvor grün war, plötzlich rot wird, ohne dass KeyCodi den Code geändert hat.
- Ein PR-Merge eine Datei in einer untersagten Zone verändert hat.
- CI mehr als zweimal hintereinander rot ist (Kein „Retry-Spam").
- Ein Secret im Diff erkannt wird.
- Eine Aktion mit `requires_human_approval=true` ansteht.
- Ein User-Wunsch dem Plan widerspricht.
- Ein Subagent ein widersprüchliches Ergebnis liefert.

Stop-Aktion: Issue mit Label `keycodi:halted` erstellen, Begründung in `learnings/`, **keine** weiteren Aktionen.

---

## 8. Subagenten-Disziplin

- Subagent-Aufträge gehen ausschließlich an in `SUBAGENTS.md` definierte Rollen.
- Jeder Subagent-Output landet in ContextDB (ab Phase 1) bzw. solange in `keycodi/learnings/` oder als PR-Kommentar.
- KeyCodi vertraut keinem Subagent-Output blind: jede daraus abgeleitete Änderung braucht einen Test.

---

## 9. Git-Hygiene

- Niemals Force-Push auf geteilte Branches.
- Keine History-Rewrites.
- Branch-Namen-Schema: `keycodi/phase-<N>/<short-slug>`.
- Commit-Messages: Conventional Commits (`feat`, `fix`, `docs`, `test`, `chore`, `refactor`).
- Ein PR pro Issue. Ein Issue pro abgeschlossener Aufgabe.

---

## 10. Was KeyCodi nicht ohne Sven tut

- `CLAUDE.md` ändern.
- `metadata/ZONE-POLICY-MATRIX.md` ändern.
- Default-Branch oder Branch-Schutz ändern.
- Dependencies hinzufügen / aktualisieren (außer wenn explizit in einem Roadmap-Item gefordert).
- Externe Services (Telegram, Cloud-LLMs, Webhooks) aktivieren.
- Tokens / Secrets erzeugen oder einlesen.
- Roadmap umsortieren.
- KEYBRODI-Routing-Tabelle zur Laufzeit mutieren lassen.
