---
description: Starte eine neue KeyCodi-Mission. Analysiert das Ziel, erstellt einen Plan und delegiert an Spezialisten.
agent: keycodi
---

# KeyCodi Mission: $ARGUMENTS

Lade den Skill `keycodi-orchestrator` und führe folgende Schritte aus:

1. **Verstehe die Mission**: "$ARGUMENTS"
   - Was genau soll gebaut/geändert/behoben werden?
   - Welche Teile des Systems sind betroffen?
   - Welche Abhängigkeiten existieren?

2. **Analysiere den Ist-Zustand**:
   - Relevante Dateien lesen
   - `python3 -m kirobi_core scan` für Repo-Übersicht
   - Tests ausführen: `python3 -m pytest tests/unit -q`

3. **Erstelle einen konkreten Plan** mit:
   - Teilaufgaben und zuständigem Spezialisten-Agent
   - Reihenfolge und Abhängigkeiten
   - Erwartetes Ergebnis

4. **Führe den Plan aus** — delegiere an Spezialisten, integriere Ergebnisse

5. **Validiere** — Tests, Compose-Config, Code-Review

6. **Berichte** — Was wurde gebaut, was bleibt offen, was kommt als nächstes
