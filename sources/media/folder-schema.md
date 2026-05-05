# Ordner-Schema: sources/media

**Zone:** QUARANTINE | **Version:** 1.0

## Dateinamens-Konventionen

```
YYYY-MM-DD_beschreibung[_quelle].ext
Beispiel: 2024-01-15_meeting-notes_zoom.pdf
```

## Pflicht-Metadaten beim Einlegen

- Dateiname nach Konvention
- Wenn möglich: Quelle dokumentieren
- Bei sensiblen Inhalten: Notiz zur Zone-Einstufung

## Automatische Verarbeitung

hermes-extractor prüft dieses Verzeichnis regelmäßig auf neue Dateien.
Verarbeitete Dateien werden nach erfolgreicher Extraktion archiviert.

## Maximale Dateigröße

| Typ | Max-Größe |
|-----|-----------|
| PDF | 100 MB |
| Bild | 50 MB |
| Audio | 500 MB |
| Video | 2 GB |
| Sonstige | 50 MB |
