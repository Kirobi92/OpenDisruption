# sources/inbox – Eingangszone

**Zone:** QUARANTINE (bis verarbeitet) | **Verantwortlich:** hermes-extractor

## Zweck
Eingangszone für alle unklassifizierten Neueingänge zur späteren Verarbeitung durch hermes-extractor.

## Was gehört hier hinein?
- Alle neuen, noch unklassifizierten Dateien\n- Direkte Uploads von Sven\n- Automatische Imports aus anderen Systemen

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
