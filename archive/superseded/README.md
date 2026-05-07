---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# archive/superseded

Dateien, die durch neuere Versionen oder bessere Lösungen ersetzt wurden.

## Zweck

Wenn eine Datei, ein Skript oder ein Konzept durch eine überarbeitete Version abgelöst wird, kommt die alte Version hierher — statt gelöscht zu werden. So bleibt die Entwicklungsgeschichte nachvollziehbar.

## Konventionen

- Beim Verschieben: Originalpfad als Kommentar oder im Frontmatter festhalten
- Format: `YYYY-MM-DD_original-name.ext`
- Verweise auf die neue Version hinzufügen, wenn möglich

## Beispiel-Frontmatter

```yaml
---
zone: WORKSPACE
superseded_at: 2026-04-15
superseded_by: services/api/main.py
original_path: services/api/main_v1.py
---
```

Derzeit leer (`.gitkeep`).
