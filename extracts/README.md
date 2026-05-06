# Extracts – Verarbeitete Wissens-Extrakte

**Zone:** Gemischt (PUBLIC/WORKSPACE/FAMILY_PRIVATE) | **Verantwortlich:** hermes-extractor

## Zweck
Verarbeitete, strukturierte Extrakte aus den Rohdaten in `sources/`. Jedes Extrakt ist ein Markdown-Dokument mit vollständigen Metadaten und Frontmatter.

## Unterverzeichnisse

| Verzeichnis | Zone | Beschreibung |
|-------------|------|-------------|
| `public/` | PUBLIC | Öffentlich teilbare Extrakte |
| `workspace/` | WORKSPACE | Arbeits-Extrakte |
| `family-private/` | FAMILY_PRIVATE | Familien-Extrakte |
| `research/` | PUBLIC/WORKSPACE | Forschungs-Extrakte |
| `business/` | WORKSPACE | Business-Extrakte |
| `technical/` | WORKSPACE | Technische Extrakte |
| `media/` | WORKSPACE | Medien-Transkripte |
| `audio/` | WORKSPACE | Audio-Transkripte |
| `visual/` | WORKSPACE | Bild-Analysen |
| `structured/` | WORKSPACE | Strukturierte Daten |

## Extrakt-Format

```markdown
---
source: sources/inbox/original-datei.pdf
extracted_by: hermes-extractor
extraction_date: 2024-01-15T10:30:00Z
zone: WORKSPACE
tags: [technik, projekte]
aqal_quadrant: IT
language: de
reviewed: false
version: 1.0
---

# [Titel des Extrakts]

## Kernaussagen
...

## Action Items
...

## Quellen
...
```
