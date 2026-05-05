# extracts/structured – STRUCTURED Extrakte

**Zone:** WORKSPACE | **Verantwortlich:** hermes-extractor

## Zweck
Verarbeitete Extrakte aus der WORKSPACE-Zone für strukturierte Daten und Tabellen-Extrakte.

## Eingangsquellen
- sources/inbox/ (via hermes-extractor)
- sources/imports/ (via hermes-extractor)



## Ausgänge / Folgeordner
- Weiterverarbeitung → clusters/structured/
- Kanonisierung → canon/ (nach Review)

## Zugriff
- **Lesen:** hermes-extractor, kirobi-core, kirobi-observer
- **Schreiben:** hermes-extractor
- **Cloud-Sync:** ⚠️ Nur mit Bestätigung
