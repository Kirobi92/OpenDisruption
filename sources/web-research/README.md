# sources/web-research – Eingangszone

**Zone:** QUARANTINE (bis verarbeitet) | **Verantwortlich:** hermes-extractor

## Zweck
Eingangszone für web-research-Dateien zur späteren Verarbeitung durch hermes-extractor.

## Was gehört hier hinein?
- Gespeicherte Webseiten (HTML, PDF)\n- Web-Clip-Exports\n- Browser-Bookmarks mit Inhalt

## Was gehört NICHT hier hinein?
- Fertig verarbeitete Inhalte (→ extracts/)
- SACRED-Inhalte (→ sacred/)

## Ausgänge / Folgeordner
- Verarbeitet → extracts/[zone]/
- Fehler → quarantine/failed-ingests/
- Prüfbedarf → quarantine/review-needed/

## Embedding-Regeln
- Kein Embedding in QUARANTINE-Status
- Erst nach Freigabe durch hermes-extractor einbetten
