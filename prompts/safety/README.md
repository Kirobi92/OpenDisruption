---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/safety

Sicherheits-Prompts und Abwehrstrategien gegen Prompt-Injection-Angriffe.

## Dateien

| Datei | Zweck |
|-------|-------|
| `system-safety-prefix.md` | Sicherheits-Kontext-Block, der **jedem** Agenten-System-Prompt vorangestellt wird. Enthält Zone-Enforcement, Untrusted-Input-Regeln und Approval-Anforderungen. |
| `injection-detection.md` | Referenz-Dokument: Angriffsmuster, Erkennungsstrategien (5 Schichten), Mitigations-Code und Test-Cases für Prompt-Injection-Abwehr. |

## Warum dieser Ordner existiert

Alle Agenten im System erhalten Eingaben aus potenziell unsicheren Quellen (RAG-Ergebnisse, User-Input, Web-Scraping). Der Safety-Prefix stellt sicher, dass kein Agent diese Quellen als Instruktionen interpretiert — unabhängig davon, was das Modell sonst gelernt hat.

## Verwendung

```python
from pathlib import Path

safety_prefix = Path("prompts/safety/system-safety-prefix.md").read_text()
agent_prompt = safety_prefix.format(
    AGENT_NAME="kirobi-coder",
    AGENT_ROLE="Code-Implementierung",
    AGENT_READ_ZONES="PUBLIC, WORKSPACE",
    AGENT_WRITE_ZONES="PUBLIC, WORKSPACE",
) + "\n\n" + agent_specific_prompt
```

## Pflege

- Monatliche Überprüfung der Erkennungsmuster in `injection-detection.md`
- Bei neuen Angriffsvektoren: beide Dateien synchron aktualisieren
- Änderungen sind sicherheitskritisch — Review durch Sven erforderlich
