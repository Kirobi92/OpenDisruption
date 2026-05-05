# sources/audio – Eingangszone

**Zone:** QUARANTINE (bis verarbeitet) | **Verantwortlich:** hermes-extractor

## Zweck
Eingangszone für audio-Dateien zur späteren Verarbeitung durch hermes-extractor.

## Was gehört hier hinein?
- MP3, WAV, M4A-Dateien\n- Podcast-Episoden\n- Sprachaufnahmen\n- Voice-Memos

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
