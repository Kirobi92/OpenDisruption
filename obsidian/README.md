# Obsidian-Vaults für OpenDisruption

**Zone:** WORKSPACE (Topologie-Doku); einzelne Vaults siehe Zonen-Mapping unten.
**Letzte Aktualisierung:** 2026-05-07

OpenDisruption nutzt **mehrere Obsidian-Vaults** statt einem Mono-Vault. Jeder Agent bekommt einen **eigenen Vault** für seine Arbeitsnotizen, plus einen **Shared-Vault** (`shared-opendisruption/`), aus dem sich alle Zusammenhänge ableiten lassen.

Die Vaults in diesem Verzeichnis sind **Skelette** (Phase 0) — sie enthalten Struktur, READMEs und MOCs, aber keine Notiz-Inhalte. Phase 3 (`agents/obsidian/`) befüllt sie programmatisch.

---

## Topologie

```
obsidian/
├── README.md                       ← du bist hier
├── shared-opendisruption/          ← Shared-Vault (alle Agenten dürfen lesen/schreiben PUBLIC+WORKSPACE)
│   ├── README.md
│   ├── 00-Index/MOC.md
│   ├── 10-Agents/
│   ├── 20-Phases/
│   ├── 30-Decisions/
│   ├── 40-Learnings/
│   ├── 50-Glossary/
│   └── 99-Inbox/
└── agents/                         ← Pro-Agent-Vault
    ├── keycodi/
    ├── keybrodi/
    ├── opencode/
    ├── openclaw/
    ├── hermes/
    ├── obsidian-agent/
    └── kidi/
```

---

## Zonen-Mapping

| Vault                                  | Default-Zone     | Wer schreibt?                       | Wer liest?                         |
|----------------------------------------|------------------|-------------------------------------|------------------------------------|
| `shared-opendisruption/`               | WORKSPACE        | alle Agenten (mit Zonen-Check)      | alle Agenten (mit Zonen-Check)     |
| `agents/keycodi/`                      | WORKSPACE        | KeyCodi                             | alle Agenten                       |
| `agents/keybrodi/`                     | WORKSPACE        | KEYBRODI                            | alle Agenten                       |
| `agents/opencode/`                     | WORKSPACE        | opencode-Agent (= KeyCodi-Code-Rolle) | alle Agenten                     |
| `agents/openclaw/`                     | WORKSPACE        | openclaw-Agent                      | alle Agenten                       |
| `agents/hermes/`                       | WORKSPACE        | hermes-reasoner                     | alle Agenten                       |
| `agents/obsidian-agent/`               | WORKSPACE        | obsidian-Agent                      | alle Agenten                       |
| `agents/kidi/`                         | WORKSPACE        | kidi-Synthesizer                    | alle Agenten                       |

> **Wichtig:** Kein Vault in diesem Verzeichnis ist FAMILY_PRIVATE oder SACRED. Diese Zonen leben außerhalb des Repos (`~/kidi-vault/family/`, `~/kidi-vault/sacred/`) und werden **nie** in Git getrackt. Das Mapping dort folgt der gleichen Logik, ist aber nur am lokalen Host sichtbar. Siehe `CLAUDE.md` §3.

---

## Konventionen

### Frontmatter (Pflicht)

Jede Note hat ein YAML-Frontmatter:

```yaml
---
zone: WORKSPACE
agent: keycodi
created: 2026-05-07
updated: 2026-05-07
phase: 0
tags: [routing, decision]
sources: []
---
```

`zone` ist Pflicht, alle anderen sind empfohlen.

### Naming

- Datei: `kebab-case.md` (z. B. `phase-1-contextdb-runbook.md`).
- MOC: `00-Index/MOC.md` pro Vault.
- Daily Notes: `00-Index/daily/YYYY-MM-DD.md` (nur im Shared-Vault).

### Wikilinks

Cross-Vault-Links sind **erlaubt**, aber müssen den Vault-Pfad enthalten, weil Obsidian per Default vault-lokal verlinkt:

```
[[../../shared-opendisruption/30-Decisions/0001-redis-as-contextdb|ADR 0001]]
```

Innerhalb eines Vaults: kurze Wikilinks (`[[note-name]]`).

---

## Was die Vaults nicht sind

- Kein Ersatz für `metadata/` — die Zonen-Policy bleibt dort.
- Kein Ersatz für Qdrant — die Embeddings bleiben in den existierenden Collections (`metadata/COLLECTION-MAPPING.md`).
- Kein Cloud-Sync. Vaults sind lokal. Wer Sync möchte, nutzt Syncthing oder Git über einen privaten Remote — **niemals** Obsidian Sync für FAMILY_PRIVATE/SACRED.

---

## Phase-Roadmap

| Phase | Beitrag zu Vaults                                                            |
|-------|------------------------------------------------------------------------------|
| 0     | Skelette + READMEs + MOCs (dieses PR)                                        |
| 1     | ContextDB schreibt Daily-Note-Referenzen in `shared-opendisruption/40-Learnings/` |
| 2     | Agenten bekommen ein `agents/<name>/00-Index.md` MOC                         |
| 3     | `agents/obsidian-agent/` befüllt Vaults programmatisch                       |
| 4     | KEYBRODI-Routing-Entscheidungen werden als Notes im Shared-Vault gespiegelt  |
| 5     | (gated) Telegram-Aktivität → `shared-opendisruption/40-Learnings/telegram/`  |
| 6     | Doku-Polish, MOCs final regeneriert                                          |
