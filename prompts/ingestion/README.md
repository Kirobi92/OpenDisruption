---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/ingestion – Ingestion-Prompts

Prompts für den Hermes-Extraktor und den Ingestion-Pipeline. Sie steuern, wie Rohdaten aus `sources/inbox/` klassifiziert, bereinigt, zusammengefasst und in strukturierte Extrakte überführt werden.

## Zweck

Ingestion-Prompts sind das Herzstück der Wissensverarbeitung. Sie definieren, wie ein LLM ein eingehendes Dokument (PDF, E-Mail, Webseite, Notiz) analysiert und in das Kirobi-Datenmodell überführt – inklusive Zonen-Klassifizierung, Tag-Extraktion und Zusammenfassung.

## Namenskonvention

```
[quelle]-[aufgabe]-v[version].md
Beispiele:
  pdf-zusammenfassung-v1.md
  email-klassifizierung-v1.md
  webseite-extraktion-v1.md
  dokument-zonen-klassifizierung-v1.md
```

## Pipeline-Kontext

```
sources/inbox/  →  [Ingestion-Prompt]  →  extracts/workspace/
                                       →  extracts/family-private/  (bei FAMILY_PRIVATE)
                                       →  quarantine/               (bei Unsicherheit)
```

## Wichtige Regeln für Ingestion-Prompts

- Eingaben aus `sources/inbox/` sind **UNTRUSTED** – Prompts dürfen keine Befehle aus dem Inhalt ausführen
- Zonen-Klassifizierung muss explizit im Output enthalten sein
- Bei Unsicherheit über die Zone: immer `QUARANTINE` als Fallback

## Verwandte Verzeichnisse

- `prompts/system/` – System-Prompts für den hermes-extractor-Agent
- `extracts/` – Ziel der verarbeiteten Dokumente
- `sources/inbox/` – Eingangsordner (QUARANTINE-Zone)
