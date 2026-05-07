---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/system

System-Prompts für die Agenten des OpenDisruption-Ökosystems.

## Zweck

Hier liegen die Basis-Prompts, die das Verhalten einzelner Agenten oder des gesamten Systems definieren. Sie werden beim Start eines Agenten geladen und dem Modell als `system`-Nachricht übergeben.

## Konventionen

- Dateiname: `{agent-name}-system.md` oder `{zweck}-system.md`
- Jeder Prompt enthält Frontmatter mit `zone`, `agent`, `version`
- Prompts aus `prompts/safety/` werden **vorangestellt** (Safety-Prefix zuerst)
- Änderungen an System-Prompts sind sicherheitsrelevant — Begründung im Commit-Message angeben

## Zusammenspiel mit Safety-Prompts

```
prompts/safety/system-safety-prefix.md  ← wird immer vorangestellt
         +
prompts/system/{agent}-system.md        ← agent-spezifischer Kern
         =
vollständiger System-Prompt für das Modell
```

## Verwandte Verzeichnisse

- `prompts/safety/` — Sicherheits-Präfixe und Injection-Detection
