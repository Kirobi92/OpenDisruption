# Sources – Rohdaten-Eingang

**Zone:** QUARANTINE (bis verarbeitet) | **Verantwortlich:** hermes-extractor

## Zweck
Das `sources/`-Verzeichnis ist das Eingangstor aller Rohdaten ins Kirobi-System. Alle Inhalte hier sind im QUARANTINE-Status bis sie von hermes-extractor verarbeitet wurden.

## Unterverzeichnisse

| Verzeichnis | Inhalt |
|-------------|--------|
| `inbox/` | Allgemeiner Eingang (unklassifiziert) |
| `imports/` | Strukturierte Imports aus Systemen |
| `chats/` | Chat-Exports (ChatGPT, WhatsApp, etc.) |
| `apis/` | API-Responses und Webhook-Daten |
| `web-research/` | Gespeicherte Webinhalte |
| `docs/` | Dokumente (PDF, DOCX, PPTX) |
| `media/` | Allgemeine Medien |
| `audio/` | Audio-Dateien |
| `video/` | Video-Dateien |
| `images/` | Bild-Dateien |
| `spreadsheets/` | Tabellen und Daten |
| `models-3d/` | 3D-Modelle |

## Verarbeitungs-Pipeline

```
sources/[typ]/ → hermes-extractor → extracts/[zone]/
                                  ↘ quarantine/ (bei Fehler)
```

## Sicherheits-Hinweis
Inhalte in sources/ dürfen KEINE bereits klassifizierten SACRED-Informationen enthalten. Wenn du SACRED-Inhalte einlegen möchtest, lege sie direkt in sacred/ ab.
