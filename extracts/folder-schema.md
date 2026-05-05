# Ordner-Schema: extracts/

**Zone:** Gemischt | **Version:** 1.0

## Zonen-Zuordnung

Jedes Extrakt wird in das Unterverzeichnis der passenden Zone gelegt:
- Öffentlich teilbar → `public/`
- Arbeit/Technik → `workspace/`
- Familie → `family-private/`

## Dateinamens-Konventionen

```
YYYY-MM-DD_quelle-beschreibung.md
Beispiel: 2024-01-15_zoom-meeting-projektplanung.md
```

## Pflicht-Frontmatter

Jedes Extrakt MUSS diese Felder im YAML-Frontmatter haben:
- `source`: Originale Quelldatei
- `extracted_by`: Agent-Name
- `extraction_date`: ISO-8601
- `zone`: Zone-Bezeichnung
- `tags`: Mindestens 1 Tag
- `reviewed`: true/false

## Qualitätssicherung

hermes-extractor markiert unvollständige Extrakte mit `reviewed: false`.
kirobi-observer prüft wöchentlich unreviewed Extrakte.
