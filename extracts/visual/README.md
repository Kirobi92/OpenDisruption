# extracts/visual – VISUAL Extrakte

**Zone:** WORKSPACE | **Verantwortlich:** hermes-extractor

## Zweck
Verarbeitete Extrakte aus der WORKSPACE-Zone für Bild-Analysen und visuellen Inhalt.

## Eingangsquellen
- sources/inbox/ (via hermes-extractor)
- sources/imports/ (via hermes-extractor)

- sources/images/ (via hermes-extractor + LLaVA)

## Ausgänge / Folgeordner
- Weiterverarbeitung → clusters/visual/
- Kanonisierung → canon/ (nach Review)

## Zugriff
- **Lesen:** hermes-extractor, kirobi-core, kirobi-observer
- **Schreiben:** hermes-extractor
- **Cloud-Sync:** ⚠️ Nur mit Bestätigung
