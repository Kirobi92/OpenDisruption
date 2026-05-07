---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# API-Proxy Route

Next.js Route Handler der alle Requests an `/api/proxy/{service}/{...path}` an den jeweiligen Backend-Service weiterleitet.

## Zweck

Ermöglicht dem Dashboard, alle Backend-Services über einen einzigen Origin anzusprechen — kein CORS-Problem, keine hardcodierten Ports im Frontend.

## Service-Port-Map

| Service | Port |
|---------|------|
| auth | 8002 |
| api | 8003 |
| embeddings | 8004 |
| retrieval | 8006 |
| ingest | 8007 |
| analytics | 8010 |
| image-generation | 8011 |
| media-processing | 8012 |
| music-generation | 8013 |
| video-generation | 8014 |

## Sicherheit

- Unbekannte Service-Namen → HTTP 400
- SACRED-Daten werden nie durch diesen Proxy geleitet
- Nur für interne Dashboard-Nutzung gedacht
