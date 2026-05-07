# Handoff: KeyCodi → KEYBRODI

**Zone:** WORKSPACE
**Letzte Aktualisierung:** 2026-05-07

KeyCodi ist **Interim-Master-Orchestrator**. Sobald KEYBRODI (`docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`) reif ist, gibt KeyCodi die Orchestrierung ab und behält ausschließlich die Coding-Architekt-Rolle.

Dieses Dokument definiert **die exakten, messbaren Bedingungen**, unter denen die Übergabe stattfindet. Vor Erfüllung **aller** Kriterien bleibt KeyCodi Orchestrator. Nach Erfüllung initiiert KeyCodi den Handoff per Issue mit Label `keybrodi:ready`.

---

## 1. Reife-Kriterien für KEYBRODI (alle müssen erfüllt sein)

### 1.1 Funktional

- [ ] `kidi/keybrodi/orchestrator.py` existiert und exportiert `route(task) -> RoutingDecision`.
- [ ] Routing-Tabelle aus `AGENT-DECISION-MATRIX.md` ist als statische Datenstruktur eingelesen.
- [ ] KEYBRODI routet jede in der Matrix gelistete Task korrekt zum erwarteten Agenten — durch Tests belegt.
- [ ] Zonen-Eskalation wird abgelehnt — durch Test belegt.
- [ ] `requires_human_approval=true` führt zu `DEFER` mit Notification — durch Test belegt.

### 1.2 Beobachtbarkeit

- [ ] Jede Routing-Entscheidung erzeugt einen Log-Eintrag in `kirobi-core/core-events.log` im Format aus `KEYBRODI-SUPERINTELLIGENZ.md` §3.
- [ ] Jede KIDI-Synthese erzeugt einen `SYNTHESIZE`-Log-Eintrag.
- [ ] Jede Ablehnung erzeugt einen `REJECT`-Log-Eintrag mit Reason-Code.
- [ ] Mindestens 7 Tage Live-Metriken liegen vor und sind nicht-leer.

### 1.3 Stabilität

- [ ] CI grün auf `main` für mindestens 14 aufeinanderfolgende Tage.
- [ ] Keine offenen `keycodi:halted`-Issues.
- [ ] Keine offenen P0/P1-Bugs in `kidi/`.
- [ ] Keine FAMILY_PRIVATE/SACRED-Verstöße im Audit-Log seit Phase 4.

### 1.4 Sicherheit

- [ ] Zonen-Tests aus `tests/unit/kidi/` decken alle Kombinationen aus `ZONE-POLICY-MATRIX.md` ab.
- [ ] CodeQL-Scan ohne offene High/Critical-Findings im KEYBRODI-Pfad.
- [ ] Manuelle Sicherheits-Review durch Sven (Eintrag mit Label `keycodi:approved` + Verweis).

### 1.5 Dokumentation

- [ ] `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md` ist auf den tatsächlichen Stand gebracht.
- [ ] `keycodi/runbooks/phase-4-kidi-keybrodi.md` ist abgeschlossen.
- [ ] Mindestens 3 ADRs in `keycodi/decisions/` zur KEYBRODI-Architektur.
- [ ] `BENUTZERHANDBUCH.md` enthält ein Kapitel „Wie KEYBRODI orchestriert".

---

## 2. Handoff-Prozess (in genau dieser Reihenfolge)

1. **KeyCodi prüft alle Kriterien.** Wenn auch nur eines offen ist: kein Handoff.
2. **KeyCodi öffnet Handoff-Issue** mit Label `keybrodi:ready` und einer Markdown-Tabelle, die jedes Kriterium mit Belege-Link beweist.
3. **Sven nickt ab** (Kommentar `LGTM` oder Label `keycodi:approved`).
4. **KeyCodi pflegt** `metadata/AGENTREGISTRY.md`: KeyCodis Rolle wird auf „Coding-Architekt (nur Code)" reduziert.
5. **KeyCodi pflegt** `AGENT-DECISION-MATRIX.md`: Routing-Spalten, die zuvor KeyCodi hatten, gehen an KEYBRODI.
6. **KeyCodi pflegt** `keycodi/MISSION.md` und `keycodi/OPERATING-RULES.md`: streicht den Interim-Orchestrator-Teil.
7. **KeyCodi pflegt** `obsidian/agents/keycodi/` und `obsidian/agents/keybrodi/` MOCs.
8. **KeyCodi öffnet Handoff-PR** mit allen oben genannten Doku-Updates und Label `keycodi:approved`.
9. **Nach Merge:** KEYBRODI ist Orchestrator. KeyCodi nimmt nur noch Coding-Tasks (`opencode`-Rolle aus `AGENT-DECISION-MATRIX.md`).
10. **Erste 7 Tage nach Handoff:** KeyCodi monitort KEYBRODI, kann bei P0-Incidents zurück in Interim-Modus wechseln (per `keycodi:resume`-Label).

---

## 3. Was nach dem Handoff bei KeyCodi bleibt

| Aufgabe                                | Vorher (KeyCodi) | Nachher (KeyCodi) | Nachher (KEYBRODI) |
|----------------------------------------|------------------|-------------------|--------------------|
| Code generieren / refactoren           | ✅               | ✅                | ❌                 |
| Tests schreiben                        | ✅               | ✅                | ❌                 |
| CI-Pipeline-Änderungen                 | ✅               | ✅                | ❌                 |
| Routing einer Task                     | ✅               | ❌                | ✅                 |
| Metrik-Erfassung                       | ✅               | ❌                | ✅                 |
| KIDI-Synthese-Aufruf                   | ✅               | ❌                | ✅                 |
| Backlog-Triage                         | ✅               | ✅ (Coding-Items) | ✅ (alle anderen)  |
| Roadmap-Pflege                         | ✅               | ✅                | ❌                 |
| ADR / Learning schreiben               | ✅               | ✅                | ✅                 |

---

## 4. Rückfall-Szenario (Resume)

Wenn KEYBRODI nach Handoff in einen P0-Zustand gerät (Routing schlägt 3× hintereinander fehl, Metriken kommen nicht mehr, Sicherheits-Verstoß):

1. KEYBRODI setzt Label `keybrodi:halted` auf das nächste Routing-Issue.
2. KeyCodi nimmt Interim-Orchestrator-Rolle für die Dauer des Vorfalls wieder auf (Label `keycodi:resume`).
3. Sven wird benachrichtigt.
4. Nach Behebung: erneute Mini-Übergabe nach diesem Dokument (Schritte 1–9), aber abgekürzt auf die Kriterien, die durch den Vorfall berührt waren.

KeyCodi gibt die Orchestrierung **nur** an KEYBRODI zurück, nie an einen anderen Agenten.
