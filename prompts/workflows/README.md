---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/workflows – Workflow-Prompts

Mehrstufige Prompt-Chains und Workflow-Definitionen für komplexe, automatisierte Aufgaben im Kirobi-Ökosystem. Workflow-Prompts koordinieren mehrere Agenten oder LLM-Aufrufe in einer definierten Reihenfolge.

## Zweck

Während einfache Prompts eine einzelne Aufgabe lösen, orchestrieren Workflow-Prompts ganze Prozesse: z. B. „Dokument einlesen → klassifizieren → zusammenfassen → in Qdrant speichern" oder „Aufgabe analysieren → planen → delegieren → Ergebnis prüfen".

## Namenskonvention

```
[prozess]-workflow-v[version].md
Beispiele:
  ingestion-pipeline-workflow-v1.md
  research-summarize-workflow-v1.md
  task-delegation-workflow-v1.md
  interview-capture-workflow-v1.md
```

## Workflow-Typen

| Typ | Beschreibung |
|-----|-------------|
| Pipeline | Sequenzielle Verarbeitungsschritte (A → B → C) |
| Parallel | Mehrere Agenten arbeiten gleichzeitig |
| Conditional | Verzweigungen basierend auf Zwischenergebnissen |
| Loop | Iterative Verfeinerung bis Qualitätskriterium erfüllt |
| Human-in-the-Loop | Pausiert für menschliche Bestätigung |

## Struktur eines Workflow-Prompts

```markdown
## Ziel
[Was soll am Ende erreicht sein?]

## Eingabe
[Welche Daten/Parameter werden erwartet?]

## Schritte
1. [Schritt 1 – Agent/Modell – Prompt-Referenz]
2. [Schritt 2 – ...]

## Ausgabe
[Format und Ziel des Ergebnisses]

## Fehlerbehandlung
[Was passiert bei Fehlern in einzelnen Schritten?]
```

## Verwandte Verzeichnisse

- `integrations/flows/` – Flowise-Implementierungen von Workflows
- `prompts/agents/` – Agent-Prompts, die in Workflows genutzt werden
- `prompts/system/` – Übergeordnete System-Prompts
