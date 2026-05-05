# Ordner-Schema: sources/ (Hauptverzeichnis)

**Zone:** QUARANTINE | **Version:** 1.0

## Allgemeine Konventionen für alle sources/-Unterordner

### Dateinamens-Konventionen
```
YYYY-MM-DD_kurze-beschreibung[_quelle].[ext]
Beispiele:
  2024-01-15_meeting-protokoll_zoom.pdf
  2024-01-20_geschaeftsbericht-q4-2023.xlsx
  2024-02-01_forschungsartikel-ai-agents_arxiv.pdf
```

### Verbotene Zeichen in Dateinamen
- Leerzeichen (Unterstriche verwenden)
- Umlaute (ae, oe, ue schreiben)
- Sonderzeichen außer: `-_.()`

### Maximale Tiefe
- Keine Unterverzeichnisse in sources/ anlegen
- Alle Dateien direkt in den typisierten Unterordner

### Automatische Verarbeitung
hermes-extractor prüft alle sources/-Unterordner regelmäßig (Intervall: 15 Minuten)
