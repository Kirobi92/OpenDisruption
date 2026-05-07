# KeyCodi — Multi-Subagent Development

**Zone:** WORKSPACE
**Letzte Aktualisierung:** 2026-05-07

KeyCodi orchestriert spezialisierte **Subagenten** für Teilaufgaben. Jeder Subagent hat einen klar abgegrenzten Scope, Lese-/Schreibrechte und ein definiertes Output-Format. Ein Subagent ist **kein** eigenständiger Roadmap-Owner — KeyCodi bleibt der Owner.

Existierende Subagent-Definitionen liegen in `.codex/agents/` (Codex-CLI) und werden hier zur OpenDisruption-Konvention erweitert.

---

## 1. Subagent-Rollen

| Rolle              | Lese-Scope              | Schreib-Scope         | Default-Modell-Klasse | Quelle                        |
|--------------------|-------------------------|-----------------------|-----------------------|-------------------------------|
| `explorer`         | repo-readonly           | none                  | "fast"                | `.codex/agents/explorer.toml` |
| `reviewer`         | repo-readonly           | PR-Kommentare         | "review"              | `.codex/agents/reviewer.toml` |
| `docs-researcher`  | web (PUBLIC) + repo     | none                  | "research"            | `.codex/agents/docs-researcher.toml` |
| `test-writer`      | repo-readonly + Spec    | `tests/`              | "code"                | (neu, ab Phase 1)             |
| `runbook-writer`   | repo-readonly           | `keycodi/runbooks/`   | "docs"                | (neu, ab Phase 1)             |
| `vault-curator`    | `obsidian/`             | `obsidian/`           | "docs"                | (neu, ab Phase 3)             |

Subagenten **erweitern** sich nicht selbständig. Neue Rollen brauchen ein ADR in `keycodi/decisions/`.

---

## 2. Auftragsschema

Ein KeyCodi-Subagent-Auftrag ist immer:

```yaml
subagent: <rolle>
issue:    <#NNN>
phase:    <0..6>
zone:     PUBLIC | WORKSPACE
input:
  - <Datei oder URL>
  - ...
expected_output:
  format: markdown | python | yaml | json
  destination: <Pfad oder „PR-Kommentar">
constraints:
  - "Keine Änderungen außerhalb expected_output.destination"
  - "Keine externen Calls außer in PUBLIC-Zone"
  - "Keine Spekulation — Quellen zitieren"
deadline: <ISO-8601 oder null>
```

KeyCodi protokolliert jeden Auftrag in `keycodi/learnings/` mit Auftrag-Hash, Subagent, Outcome.

---

## 3. Aufrufrichtlinien

- **Parallel** wenn die Aufträge unabhängig sind (`explorer` + `docs-researcher` zur selben Frage).
- **Sequentiell** wenn ein Subagent das Ergebnis eines anderen braucht (`explorer` → `test-writer`).
- **Niemals rekursiv** — Subagenten rufen keine Subagenten auf. Nur KeyCodi orchestriert.
- **Keine Geheimnisse weitergeben** — Subagenten erhalten nie Tokens, ENV-Werte oder FAMILY_PRIVATE-Daten.

---

## 4. Validierung von Subagent-Output

KeyCodi vertraut Subagent-Output **nie** blind. Vor Übernahme:

1. **Format-Check** — entspricht dem `expected_output.format`?
2. **Quellen-Check** — bei `explorer` / `docs-researcher`: jede Aussage hat Datei + Zeile / URL.
3. **Zonen-Check** — keine Datei aus untersagter Zone referenziert.
4. **Test-Check** — bei Code/Test-Output: `pytest` muss grün laufen, bevor übernommen wird.
5. **Diff-Check** — Subagent-Diff bleibt im versprochenen Pfad.

Schlägt einer dieser Checks fehl: Output verworfen, Eintrag in `learnings/`, Auftrag wird **nicht** automatisch wiederholt.

---

## 5. Phasen-spezifische Subagenten-Pakete

### Phase 1 (ContextDB)

- `explorer` → analysiert bestehende Redis-Konfigurationen im Repo (gibt es welche?).
- `test-writer` → schreibt die vier Test-Dateien aus `MILESTONES.md` Phase 1.
- `reviewer` → reviewt jeden PR vor Merge.

### Phase 2 (Agent-Skelette)

- `runbook-writer` → ergänzt `runbooks/phase-2-agent-skeletons.md` um konkrete Schritte.
- `test-writer` → smoke- und refusal-Tests pro Agent.

### Phase 3 (Obsidian)

- `vault-curator` → MOCs und Daily-Notes generieren.
- `docs-researcher` → prüft Obsidian-Plugin-Kompatibilität (PUBLIC-Quellen).

### Phase 4 (KIDI/KEYBRODI)

- `explorer` → identifiziert Stellen im Repo, die Routing schon näherungsweise machen.
- `test-writer` → Routing- und Synthese-Tests.

### Phase 5 (Telegram, gated)

- `reviewer` → besonders strenge Reviews, Fokus auf Zone-Filter-Bypass-Versuche.

### Phase 6 (Installer)

- `docs-researcher` → vergleicht install.sh-Patterns sicherer Open-Source-Installer.
- `reviewer` → Sicherheits-Review.

---

## 6. Was Subagenten **nie** tun dürfen

- Roadmap-Reihenfolge ändern.
- Issues schließen.
- Ohne Auftrag handeln.
- Schreibzugriff auf `metadata/`, `CLAUDE.md`, `.env`, `sacred/`, `extracts/family-private/`.
- Externe Calls aus FAMILY_PRIVATE / SACRED-Daten heraus.
- Tokens / Secrets generieren.
- Andere Subagenten direkt anstoßen.
