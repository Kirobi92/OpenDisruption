# sources/media – Eingangszone

**Zone:** QUARANTINE (bis verarbeitet) | **Verantwortlich:** hermes-extractor

## Zweck
Eingangszone für media-Dateien zur späteren Verarbeitung durch hermes-extractor.

## Was gehört hier hinein?
- Allgemeine Mediendateien\n- Gemischte Inhalte

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
