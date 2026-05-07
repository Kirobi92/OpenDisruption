# Shared OpenDisruption Vault

**Zone:** WORKSPACE
**Vault-Typ:** Shared (alle Agenten lesen/schreiben PUBLIC + WORKSPACE)
**Phase:** 0 (Skelett)

Aus diesem Vault leiten sich **alle Zusammenhänge** des Ökosystems ab: Phasen-Status, ADRs, Learnings, Glossar. Die per-Agent-Vaults verlinken hierher.

## Struktur

| Ordner            | Inhalt                                                                  |
|-------------------|-------------------------------------------------------------------------|
| `00-Index/`       | MOC (Map of Content), Daily Notes, Phase-Dashboard                      |
| `10-Agents/`      | Pro Agent: Steckbrief + Aufgaben + Verweise auf Agent-Vault             |
| `20-Phases/`      | Pro Phase: Status, Runbook-Verweis, offene Items, geschlossene PRs      |
| `30-Decisions/`   | ADR-Spiegel aus `keycodi/decisions/` (Read-only, automatisch gepflegt)  |
| `40-Learnings/`   | Learnings-Spiegel aus `keycodi/learnings/` (Read-only, automatisch)     |
| `50-Glossary/`    | Begriffsdefinitionen (KIDI, KEYBRODI, KeyCodi, Zonen, ContextDB, …)     |
| `99-Inbox/`       | Unstrukturierte Schnipsel, manuell + automatisch befüllt, später triagiert |

## Schreibregeln

- **Nie** FAMILY_PRIVATE/SACRED-Inhalte ablegen.
- Frontmatter mit `zone:` ist Pflicht.
- ADRs und Learnings werden hier **nur gespiegelt** — Originale liegen in `keycodi/{decisions,learnings}/`.
- Daily Notes werden ausschließlich von `infra/scripts/obsidian-daily-note.sh` (ab Phase 3) erzeugt.

## Cross-Vault-Verlinkung

Notes verlinken nach `obsidian/agents/<name>/...` mit relativem Pfad. Beispiel:

```
KeyCodi pflegt diesen Vault automatisch — siehe [[../../agents/keycodi/00-Index|KeyCodi Vault]].
```
